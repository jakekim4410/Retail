"""
모듈 B — 상세페이지 생성 API 라우터
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any

from app.database import get_db
from app.models.product import Product, ProductStatus
from app.modules.B_detail_page.generator import generate_detail_page

router = APIRouter(prefix="/api/detail-page", tags=["B. 상세페이지 생성"])


class GenerateRequest(BaseModel):
    product_id: Optional[int] = None   # DB 상품 ID
    product_data: Optional[dict] = None  # 또는 직접 상품 데이터 전달


@router.post("/generate")
async def generate_page(
    req: GenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    상세페이지 HTML 생성
    - product_id 지정 시 DB에서 상품 로드
    - product_data 직접 전달도 가능 (테스트용)
    """
    if req.product_id is not None:
        result = await db.execute(select(Product).where(Product.id == req.product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")

        product_data = {
            "source_id": product.source_id,
            "name": product.name,
            "brand": product.brand,
            "manufacturer": product.manufacturer,
            "origin": product.origin,
            "image_urls": product.image_urls or [],
            "specs": product.specs or {},
            "options": product.options or {},
            "source_category_code": product.source_category_code or "DEFAULT",
        }
    elif req.product_data:
        product_data = req.product_data
        product = None
    else:
        raise HTTPException(status_code=400, detail="product_id 또는 product_data 중 하나는 필수입니다")

    html = await generate_detail_page(product_data)

    # DB에 저장
    if product:
        product.detail_page_html = html
        product.status = ProductStatus.PAGE_GENERATED
        await db.commit()

    return {
        "product_id": req.product_id,
        "html_length": len(html),
        "status": "generated",
        "preview_available": True,
    }


@router.get("/preview/{product_id}", response_class=HTMLResponse)
async def preview_page(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """생성된 상세페이지 HTML 미리보기"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    if not product.detail_page_html:
        raise HTTPException(status_code=404, detail="상세페이지가 아직 생성되지 않았습니다")
    return HTMLResponse(content=product.detail_page_html)


class UpdateHtmlRequest(BaseModel):
    html: str


@router.put("/{product_id}")
async def update_detail_page(
    product_id: int,
    req: UpdateHtmlRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """생성된 상세페이지 HTML 원문 수정"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
    
    product.detail_page_html = req.html
    await db.commit()
    
    return {"success": True, "product_id": product_id}


@router.post("/generate-batch")
async def generate_batch(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """PAGE_GENERATED 단계가 아닌 SOURCED 상품 전체 상세페이지 일괄 생성"""
    result = await db.execute(
        select(Product).where(Product.status == ProductStatus.SOURCED)
    )
    products = result.scalars().all()

    success = 0
    failed = 0
    for product in products:
        try:
            product_data = {
                "source_id": product.source_id,
                "name": product.name,
                "brand": product.brand,
                "manufacturer": product.manufacturer,
                "origin": product.origin,
                "image_urls": product.image_urls or [],
                "specs": product.specs or {},
                "options": product.options or {},
                "source_category_code": product.source_category_code or "DEFAULT",
            }
            html = await generate_detail_page(product_data)
            product.detail_page_html = html
            product.status = ProductStatus.PAGE_GENERATED
            success += 1
        except Exception as e:
            print(f"[상세페이지 생성 실패] {product.source_id}: {e}")
            failed += 1

    await db.commit()
    return {"total": len(products), "success": success, "failed": failed}
