"""
모듈 A — 소싱·마진 API 라우터
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Any

from app.database import get_db
from app.models.product import Product, ProductStatus
from app.modules.A_sourcing.ownerclan import ownerclan_client
from app.modules.A_sourcing.margin import calculator, MarginCalculator
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/sourcing", tags=["A. 소싱·마진"])


class MarginCheckRequest(BaseModel):
    source_id: str
    wholesale_price: float
    sale_price: float
    source_category_code: str
    target_margin_pct: float | None = None


@router.get("/products")
async def list_source_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_code: str | None = None,
) -> dict[str, Any]:
    """도매처(오너클랜)에서 상품 목록 조회"""
    data = await ownerclan_client.get_new_products(
        page=page, page_size=page_size, category_code=category_code
    )
    return data


@router.post("/scan")
async def scan_and_filter(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    target_margin_pct: float = Query(settings.margin_threshold_percent),
    monthly_sales_estimate: float = Query(500_000),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    도매처 신상품 수집 → 마진 검증 → DB 저장
    통과 상품만 반환, 실패 상품도 필터링 이유와 함께 반환
    """
    calc = MarginCalculator(
        threshold_pct=target_margin_pct,
        monthly_sales_estimate=monthly_sales_estimate,
    )
    raw = await ownerclan_client.get_new_products(page=page, page_size=page_size)
    products = raw.get("products", [])

    passed_list = []
    filtered_list = []

    for p in products:
        # 권장 판매가 계산 (도매가의 140% 기준점)
        suggested_price = p["wholesale_price"] * 1.4
        # 100원 단위 반올림
        suggested_price = round(suggested_price / 100) * 100
        result = calc.calculate(
            source_id=p["source_id"],
            name=p["name"],
            wholesale_price=p["wholesale_price"],
            sale_price=suggested_price,
            source_category_code=p["source_category_code"],
        )
        margin_dict = result.to_dict()
        margin_dict["suggested_price"] = suggested_price

        # DB 저장/업데이트
        existing = await db.execute(
            select(Product).where(Product.source_id == p["source_id"])
        )
        existing_product = existing.scalar_one_or_none()

        if existing_product is None:
            db_product = Product(
                source_id=p["source_id"],
                source_name="ownerclan",
                name=p["name"],
                brand=p.get("brand"),
                manufacturer=p.get("manufacturer"),
                origin=p.get("origin"),
                wholesale_price=p["wholesale_price"],
                sale_price=suggested_price,
                source_category_code=p["source_category_code"],
                image_urls=p.get("image_urls", []),
                specs=p.get("specs"),
                options=p.get("options"),
                margin_rate=result.net_margin_rate,
                margin_amount=result.net_margin,
                commission_rate=result.commission_rate,
                status=ProductStatus.SOURCED if result.passed else ProductStatus.FILTERED,
            )
            db.add(db_product)
        else:
            existing_product.margin_rate = result.net_margin_rate
            existing_product.margin_amount = result.net_margin
            existing_product.status = (
                ProductStatus.SOURCED if result.passed else ProductStatus.FILTERED
            )

        if result.passed:
            passed_list.append({**p, "margin": margin_dict})
        else:
            filtered_list.append({**p, "margin": margin_dict, "filter_reason": "마진율 기준 미달"})

    await db.commit()

    return {
        "total_scanned": len(products),
        "passed": len(passed_list),
        "filtered": len(filtered_list),
        "passed_products": passed_list,
        "filtered_products": filtered_list,
        "mock": raw.get("mock", False),
    }


@router.post("/margin-check")
async def check_margin(req: MarginCheckRequest) -> dict[str, Any]:
    """단일 상품 마진 계산"""
    calc = MarginCalculator(threshold_pct=req.target_margin_pct or settings.margin_threshold_percent)
    result = calc.calculate(
        source_id=req.source_id,
        name="",
        wholesale_price=req.wholesale_price,
        sale_price=req.sale_price,
        source_category_code=req.source_category_code,
    )
    suggested = calc.suggest_sale_price(
        req.wholesale_price,
        req.source_category_code,
        req.target_margin_pct,
    )
    d = result.to_dict()
    d["suggested_sale_price"] = suggested
    return d


@router.get("/db-products")
async def list_db_products(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """DB에 저장된 상품 목록"""
    q = select(Product)
    if status:
        try:
            q = q.where(Product.status == ProductStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    result = await db.execute(q.order_by(Product.created_at.desc()))
    products = result.scalars().all()
    return [
        {
            "id": p.id,
            "source_id": p.source_id,
            "name": p.name,
            "brand": p.brand,
            "wholesale_price": p.wholesale_price,
            "sale_price": p.sale_price,
            "margin_rate": round(p.margin_rate or 0, 2),
            "status": p.status.value,
            "source_category_code": p.source_category_code,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in products
    ]
