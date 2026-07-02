"""
모듈 E — 최적화 루프
판매 성과 기반 자동 태깅 및 가격 조정 로직
"""
from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any

from app.models.product import Product, ProductStatus, ProductPerformance
from app.modules.A_sourcing.margin import MarginCalculator
from app.modules.C_registration.coupang import coupang_client
from app.config import get_settings

settings = get_settings()


async def run_optimization_loop(db: AsyncSession) -> dict[str, Any]:
    """
    최적화 루프 실행:
    1. 판매 저조 상품 → 하차 후보 태깅
    2. 마진율 기준 미달 상품 → 가격 조정 필요 태깅
    3. 결과 요약 반환
    """
    results = {
        "delist_tagged": [],
        "price_adjust_tagged": [],
        "total_processed": 0,
    }

    # 판매 중인 상품 모두 조회
    product_result = await db.execute(
        select(Product, ProductPerformance)
        .outerjoin(ProductPerformance, Product.id == ProductPerformance.product_id)
        .where(
            Product.status.in_([
                ProductStatus.ON_SALE,
                ProductStatus.REGISTERED,
                ProductStatus.DELIST_CANDIDATE,
                ProductStatus.PRICE_ADJUST,
            ]),
            Product.is_active == True,
        )
    )
    rows = product_result.all()
    results["total_processed"] = len(rows)

    poor_sales_cutoff = datetime.utcnow() - timedelta(days=settings.poor_sales_days)

    for product, perf in rows:
        # ── 하차 후보 판정 ──────────────────────────────────────────────
        days_since_creation = (datetime.utcnow() - product.created_at).days
        no_sales = (perf is None or perf.total_sales_qty == 0)

        if days_since_creation >= settings.poor_sales_days and no_sales:
            if product.status != ProductStatus.DELIST_CANDIDATE:
                product.status = ProductStatus.DELIST_CANDIDATE
                results["delist_tagged"].append({
                    "product_id": product.id,
                    "source_id": product.source_id,
                    "name": product.name,
                    "days_since_creation": days_since_creation,
                    "reason": f"{settings.poor_sales_days}일 이상 판매 0건",
                })

        # ── 마진율 재계산 → 가격 조정 필요 판정 ───────────────────────
        calc = MarginCalculator(threshold_pct=settings.margin_threshold_percent)
        current_result = calc.calculate(
            source_id=product.source_id,
            name=product.name,
            wholesale_price=product.wholesale_price,
            sale_price=product.sale_price,
            source_category_code=product.source_category_code or "DEFAULT",
        )

        if not current_result.passed and product.status not in (
            ProductStatus.DELIST_CANDIDATE, ProductStatus.DELISTED
        ):
            suggested_price = calc.suggest_sale_price(
                product.wholesale_price,
                product.source_category_code or "DEFAULT",
            )
            product.status = ProductStatus.PRICE_ADJUST
            results["price_adjust_tagged"].append({
                "product_id": product.id,
                "source_id": product.source_id,
                "name": product.name,
                "current_margin_rate": round(current_result.net_margin_rate, 2),
                "current_price": product.sale_price,
                "suggested_price": suggested_price,
                "reason": f"마진율 {round(current_result.net_margin_rate, 1)}% < 기준 {settings.margin_threshold_percent}%",
            })

    await db.commit()
    return results


async def auto_apply_price_adjustments(db: AsyncSession) -> dict[str, Any]:
    """
    PRICE_ADJUST 상태 상품에 권장 가격 자동 적용 (선택적 기능)
    쿠팡 API로 가격 즉시 반영
    """
    result = await db.execute(
        select(Product).where(
            Product.status == ProductStatus.PRICE_ADJUST,
            Product.coupang_product_id.isnot(None),
        )
    )
    products = result.scalars().all()

    applied = []
    calc = MarginCalculator(threshold_pct=settings.margin_threshold_percent)

    for product in products:
        suggested = calc.suggest_sale_price(
            product.wholesale_price,
            product.source_category_code or "DEFAULT",
        )
        api_result = await coupang_client.update_price(
            product.coupang_product_id,
            int(suggested),
        )
        if api_result.get("code") == "200":
            old_price = product.sale_price
            product.sale_price = suggested
            product.status = ProductStatus.ON_SALE
            applied.append({
                "product_id": product.id,
                "name": product.name,
                "old_price": old_price,
                "new_price": suggested,
            })

    await db.commit()
    return {"applied_count": len(applied), "applied": applied}
