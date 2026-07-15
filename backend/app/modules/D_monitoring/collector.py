"""
모듈 D — 쿠팡 주문/판매 데이터 수집기
"""
from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any

from app.models.order import Order, OrderStatus
from app.models.product import Product, ProductPerformance
from app.modules.C_registration.coupang import coupang_client


async def collect_orders(db: AsyncSession, days_back: int = 1) -> dict[str, Any]:
    """
    최근 N일간 쿠팡 주문 데이터 수집 → DB 저장
    """
    now = datetime.now()
    from_dt = (now - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00")
    to_dt = now.strftime("%Y-%m-%dT23:59:59")

    raw = await coupang_client.get_orders(
        status="ACCEPT",
        created_at_from=from_dt,
        created_at_to=to_dt,
    )

    orders_data = raw.get("data", [])
    new_count = 0
    updated_count = 0

    for order_raw in orders_data:
        order_id = str(order_raw.get("orderId", ""))
        if not order_id:
            continue

        # 이미 저장된 주문인지 확인
        existing = await db.execute(
            select(Order).where(Order.coupang_order_id == order_id)
        )
        existing_order = existing.scalar_one_or_none()

        ordered_at_str = order_raw.get("orderedAt", "")
        try:
            ordered_at = datetime.fromisoformat(ordered_at_str)
        except (ValueError, TypeError):
            ordered_at = datetime.utcnow()

        sale_price = float(order_raw.get("salePrice", 0))
        quantity = int(order_raw.get("quantity", 1))
        settlement = float(order_raw.get("settlementAmount", sale_price * quantity * 0.9))
        commission = float(order_raw.get("commissionAmount", sale_price * quantity * 0.07))
        net_profit = settlement - (sale_price * quantity - settlement)

        # 상품 ID 매핑
        source_id = order_raw.get("sourceId")
        product_id = None
        if source_id:
            prod_result = await db.execute(
                select(Product).where(Product.source_id == source_id)
            )
            prod = prod_result.scalar_one_or_none()
            if prod:
                product_id = prod.id

        status_map = {
            "ACCEPT": OrderStatus.ORDERED,
            "INSTRUCT": OrderStatus.ORDERED,
            "DEPARTURE": OrderStatus.SHIPPED,
            "DELIVERED": OrderStatus.DELIVERED,
            "CANCEL_DONE": OrderStatus.CANCELED,
        }
        order_status = status_map.get(order_raw.get("status", "ACCEPT"), OrderStatus.ORDERED)

        if existing_order:
            existing_order.status = order_status
            updated_count += 1
        else:
            new_order = Order(
                coupang_order_id=order_id,
                product_id=product_id,
                coupang_product_id=str(order_raw.get("productId", "")),
                quantity=quantity,
                sale_price=sale_price,
                settlement_amount=settlement,
                commission_amount=commission,
                net_profit=net_profit,
                status=order_status,
                ordered_at=ordered_at,
            )
            db.add(new_order)
            new_count += 1

    await db.commit()

    # 성과 지표 업데이트
    await _update_performance(db)

    return {
        "collected_from": from_dt,
        "collected_to": to_dt,
        "total_in_source": len(orders_data),
        "new_orders": new_count,
        "updated_orders": updated_count,
    }


async def _update_performance(db: AsyncSession) -> None:
    """주문 데이터를 집계하여 ProductPerformance 업데이트"""
    from sqlalchemy import func

    # 상품별 집계 쿼리
    from sqlalchemy import text
    rows = await db.execute(
        text("""
            SELECT
                product_id,
                SUM(quantity) AS total_qty,
                SUM(sale_price * quantity) AS total_revenue,
                SUM(net_profit * quantity) AS total_net_profit,
                SUM(CASE WHEN status = 'returned' THEN quantity ELSE 0 END) AS return_qty,
                MAX(ordered_at) AS last_sale_date
            FROM orders
            WHERE product_id IS NOT NULL
            GROUP BY product_id
        """)
    )

    for row in rows:
        product_id = row[0]
        if not product_id:
            continue

        perf_result = await db.execute(
            select(ProductPerformance).where(ProductPerformance.product_id == product_id)
        )
        perf = perf_result.scalar_one_or_none()

        if perf:
            perf.total_sales_qty = int(row[1] or 0)
            perf.total_revenue = float(row[2] or 0)
            perf.total_net_profit = float(row[3] or 0)
            perf.return_qty = int(row[4] or 0)
            if row[5]:
                perf.last_sale_date = row[5]
        else:
            perf = ProductPerformance(
                product_id=product_id,
                total_sales_qty=int(row[1] or 0),
                total_revenue=float(row[2] or 0),
                total_net_profit=float(row[3] or 0),
                return_qty=int(row[4] or 0),
                last_sale_date=row[5],
            )
            db.add(perf)

    await db.commit()
