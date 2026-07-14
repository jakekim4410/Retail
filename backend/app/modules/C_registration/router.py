"""
모듈 C — 쿠팡 상품 등록 API 라우터
반자동 흐름: 상세페이지 생성 완료 → 관리자 검수 대기 → 승인 후 쿠팡 등록
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any

from app.database import get_db
from app.models.product import Product, ProductStatus
from app.modules.C_registration.coupang import coupang_client
from app.modules.C_registration.mapper import resolve_category, build_coupang_payload
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/registration", tags=["C. 상품 등록"])


@router.get("/pending")
async def list_pending_products(
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """관리자 검수 대기 중인 상품 목록"""
    result = await db.execute(
        select(Product).where(Product.status == ProductStatus.PAGE_GENERATED)
    )
    products = result.scalars().all()
    return [
        {
            "id": p.id,
            "source_id": p.source_id,
            "name": p.name,
            "sale_price": p.sale_price,
            "margin_rate": round(p.margin_rate or 0, 2),
            "status": p.status.value,
            "has_detail_page": bool(p.detail_page_html),
            "coupang_category_id": p.coupang_category_id,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in products
    ]


@router.post("/approve/{product_id}")
async def approve_and_register(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    관리자 검수 승인 → 쿠팡 API로 상품 등록
    반자동 흐름의 핵심 단계
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")

    if not product.detail_page_html:
        raise HTTPException(status_code=400, detail="상세페이지를 먼저 생성해 주세요")

    # 카테고리 매핑
    category_info = await resolve_category(product.source_category_code or "", db)
    if not category_info:
        raise HTTPException(
            status_code=422,
            detail=f"카테고리 매핑이 없습니다: {product.source_category_code}. 수동 매핑이 필요합니다.",
        )

    product.coupang_category_id = category_info["coupang_category_id"]
    product.coupang_category_name = category_info["coupang_category_name"]

    # 쿠팡 페이로드 조립
    payload = build_coupang_payload(product, settings.coupang_vendor_id or "VENDOR001")

    # 쿠팡 API 호출
    api_result = await coupang_client.create_product(payload)

    if api_result.get("code") == "200":
        coupang_product_id = api_result["data"]["productId"]
        product.coupang_product_id = str(coupang_product_id)
        product.status = ProductStatus.REGISTERED
        await db.commit()
        return {
            "success": True,
            "product_id": product_id,
            "coupang_product_id": str(coupang_product_id),
            "status": "registered",
            "mock": api_result["data"].get("mock", False),
        }
    else:
        raise HTTPException(status_code=502, detail=f"쿠팡 API 오류: {api_result}")


@router.post("/manual-register/{product_id}")
async def manual_register(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    수동 등록 완료 처리
    쿠팡 API를 통하지 않고 수동으로 쿠팡 Wing에 등록을 완료한 경우 상태를 업데이트
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")

    # 수동 등록 시 coupang_product_id는 임시로 할당하거나 None 처리 (나중에 연동 가능)
    product.status = ProductStatus.REGISTERED
    await db.commit()
    return {
        "success": True,
        "product_id": product_id,
        "status": "registered",
        "message": "수동 등록 완료 상태로 변경되었습니다."
    }


@router.post("/set-on-sale/{product_id}")
async def set_on_sale(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """등록된 상품을 판매 중 상태로 전환"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product or not product.coupang_product_id:
        raise HTTPException(status_code=404, detail="등록된 쿠팡 상품이 없습니다")

    api_result = await coupang_client.update_product_status(product.coupang_product_id, "SALE")
    product.status = ProductStatus.ON_SALE
    await db.commit()
    return {"success": True, "product_id": product_id, "coupang_product_id": product.coupang_product_id}


@router.put("/price/{product_id}")
async def update_price(
    product_id: int,
    new_price: float = Query(..., ge=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """상품 가격 조정"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")

    old_price = product.sale_price
    product.sale_price = new_price

    if product.coupang_product_id:
        await coupang_client.update_price(product.coupang_product_id, int(new_price))

    if product.status == ProductStatus.PRICE_ADJUST:
        product.status = ProductStatus.ON_SALE

    await db.commit()
    return {"success": True, "product_id": product_id, "old_price": old_price, "new_price": new_price}


@router.post("/delist/{product_id}")
async def delist_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """상품 하차"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")

    if product.coupang_product_id:
        await coupang_client.delist_product(product.coupang_product_id)

    product.status = ProductStatus.DELISTED
    product.is_active = False
    await db.commit()
    return {"success": True, "product_id": product_id, "status": "delisted"}


@router.get("/category-map")
async def list_category_maps(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """카테고리 매핑 현황 조회"""
    from app.modules.C_registration.mapper import DEFAULT_CATEGORY_MAP
    return {
        "default_mappings": DEFAULT_CATEGORY_MAP,
        "note": "DB 매핑이 있으면 우선 사용됩니다",
    }
