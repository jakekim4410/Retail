"""
모듈 D — 판매 성과 지표 계산 및 대시보드 데이터
"""
from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Any

from app.models.product import Product, ProductStatus, ProductPerformance
from app.models.order import Order


async def get_dashboard_summary(db: AsyncSession) -> dict[str, Any]:
    """대시보드 핵심 KPI 집계"""
    # 전체 상품 상태별 카운트
    status_result = await db.execute(
        select(Product.status, func.count(Product.id))
        .group_by(Product.status)
    )
    status_counts = {row[0].value: row[1] for row in status_result}

    # 총 매출 / 순이익 (전체 기간)
    revenue_result = await db.execute(
        select(
            func.sum(Order.sale_price * Order.quantity),
            func.sum(Order.net_profit * Order.quantity),
            func.count(Order.id),
        )
    )
    rev_row = revenue_result.one()
    total_revenue = float(rev_row[0] or 0)
    total_net_profit = float(rev_row[1] or 0)
    total_orders = int(rev_row[2] or 0)

    # 이번달 매출
    first_day = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    monthly_result = await db.execute(
        select(
            func.sum(Order.sale_price * Order.quantity),
            func.sum(Order.net_profit * Order.quantity),
            func.count(Order.id),
        ).where(Order.ordered_at >= first_day)
    )
    mon_row = monthly_result.one()
    monthly_revenue = float(mon_row[0] or 0)
    monthly_net_profit = float(mon_row[1] or 0)
    monthly_orders = int(mon_row[2] or 0)

    # 하차 후보 상품 수
    delist_count_result = await db.execute(
        select(func.count(Product.id)).where(Product.status == ProductStatus.DELIST_CANDIDATE)
    )
    delist_count = delist_count_result.scalar() or 0

    # 가격 조정 필요 상품 수
    price_adj_result = await db.execute(
        select(func.count(Product.id)).where(Product.status == ProductStatus.PRICE_ADJUST)
    )
    price_adj_count = price_adj_result.scalar() or 0

    return {
        "total_revenue": round(total_revenue),
        "total_net_profit": round(total_net_profit),
        "total_orders": total_orders,
        "monthly_revenue": round(monthly_revenue),
        "monthly_net_profit": round(monthly_net_profit),
        "monthly_orders": monthly_orders,
        "product_status_counts": status_counts,
        "delist_candidate_count": delist_count,
        "price_adjust_count": price_adj_count,
        "net_margin_rate": (
            round(total_net_profit / total_revenue * 100, 2)
            if total_revenue > 0
            else 0.0
        ),
    }


async def get_product_performance_list(db: AsyncSession) -> list[dict[str, Any]]:
    """상품별 성과 데이터"""
    result = await db.execute(
        select(Product, ProductPerformance)
        .outerjoin(ProductPerformance, Product.id == ProductPerformance.product_id)
        .where(Product.is_active == True)
        .order_by(ProductPerformance.total_revenue.desc().nullslast())
    )
    rows = result.all()

    items = []
    for product, perf in rows:
        items.append({
            "id": product.id,
            "source_id": product.source_id,
            "name": product.name,
            "brand": product.brand,
            "sale_price": product.sale_price,
            "margin_rate": round(product.margin_rate or 0, 2),
            "status": product.status.value,
            "coupang_product_id": product.coupang_product_id,
            "total_sales_qty": perf.total_sales_qty if perf else 0,
            "total_revenue": round(perf.total_revenue if perf else 0),
            "total_net_profit": round(perf.total_net_profit if perf else 0),
            "return_qty": perf.return_qty if perf else 0,
            "last_sale_date": perf.last_sale_date.isoformat() if perf and perf.last_sale_date else None,
            "created_at": product.created_at.isoformat() if product.created_at else None,
        })

    return items


async def get_daily_sales_trend(db: AsyncSession, days: int = 30) -> list[dict[str, Any]]:
    """일별 매출 트렌드 (최근 N일)"""
    from_date = datetime.now() - timedelta(days=days)
    result = await db.execute(
        text("""
            SELECT
                DATE(ordered_at) as sale_date,
                COUNT(id) as order_count,
                SUM(sale_price * quantity) as revenue,
                SUM(net_profit * quantity) as net_profit
            FROM orders
            WHERE ordered_at >= :from_date
            GROUP BY DATE(ordered_at)
            ORDER BY sale_date
        """),
        {"from_date": from_date.strftime("%Y-%m-%d")},
    )
    return [
        {
            "date": str(row[0]),
            "order_count": int(row[1] or 0),
            "revenue": round(float(row[2] or 0)),
            "net_profit": round(float(row[3] or 0)),
        }
        for row in result
    ]
