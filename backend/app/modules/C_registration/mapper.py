"""
모듈 C — 카테고리 매핑 및 쿠팡 등록 페이로드 조립
"""
from __future__ import annotations
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.category_map import CategoryMapping
from app.models.product import Product


# 기본 카테고리 매핑 (DB에 없을 때 사용)
DEFAULT_CATEGORY_MAP: dict[str, dict[str, Any]] = {
    "ELEC-AUDIO":    {"coupang_id": 497009, "name": "이어폰/헤드폰", "commission": 0.068},
    "ELEC-LIGHT":    {"coupang_id": 497023, "name": "조명/등기구",   "commission": 0.068},
    "KITCHEN-CUP":   {"coupang_id": 497079, "name": "컵/텀블러",     "commission": 0.070},
    "TRAVEL-ACC":    {"coupang_id": 497110, "name": "여행용 소품",   "commission": 0.075},
    "SPORTS-YOGA":   {"coupang_id": 497145, "name": "요가/필라테스", "commission": 0.080},
    "CLEAN-CLOTH":   {"coupang_id": 497162, "name": "청소용품",      "commission": 0.075},
    "HOME-DIFFUSER": {"coupang_id": 497178, "name": "디퓨저/향초",   "commission": 0.075},
    "CAR-ACC":       {"coupang_id": 497195, "name": "차량용 거치대", "commission": 0.070},
    "SPORTS-ETC":    {"coupang_id": 497140, "name": "스포츠/레저",   "commission": 0.080},
    "HOME-ETC":      {"coupang_id": 497170, "name": "생활용품",      "commission": 0.075},
    "ELEC-ETC":      {"coupang_id": 497010, "name": "전자제품",      "commission": 0.068},
    "FOOD":          {"coupang_id": 497200, "name": "식품",          "commission": 0.040},
}


async def resolve_category(
    source_category_code: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """
    도매처 카테고리 코드 → 쿠팡 카테고리 정보 반환
    1. DB 매핑 테이블 우선 조회
    2. 없으면 DEFAULT_CATEGORY_MAP 사용
    3. 둘 다 없으면 None 반환 (등록 불가, 수동 매핑 필요)
    """
    result = await db.execute(
        select(CategoryMapping).where(
            CategoryMapping.source_category_code == source_category_code,
            CategoryMapping.is_active == True,
        )
    )
    mapping = result.scalar_one_or_none()

    if mapping:
        return {
            "coupang_category_id": mapping.coupang_category_id,
            "coupang_category_name": mapping.coupang_category_name,
            "commission_rate": mapping.commission_rate,
        }

    default = DEFAULT_CATEGORY_MAP.get(source_category_code)
    if default:
        return {
            "coupang_category_id": default["coupang_id"],
            "coupang_category_name": default["name"],
            "commission_rate": default["commission"],
        }

    return {}  # 매핑 없음


def build_coupang_payload(product: Product, vendor_id: str) -> dict[str, Any]:
    """
    쿠팡 Open API 상품등록 페이로드 조립
    실제 착수 전 최신 쿠팡 API 가이드 확인 필수
    """
    items = []
    options = product.options or {}

    if options:
        # 옵션 있는 상품
        first_opt_name = next(iter(options))
        for opt_value in options[first_opt_name]:
            items.append({
                "itemName": f"{product.name} [{opt_value}]",
                "originalPrice": int(product.sale_price * 1.1),  # 소비자가
                "salePrice": int(product.sale_price),
                "maximumBuyCount": 10,
                "maximumBuyForPerson": 10,
                "unitCount": 1,
                "attributes": [{"attributeTypeName": first_opt_name, "attributeValueName": opt_value}],
                "images": [
                    {"imageOrder": idx, "imageType": "DETAIL" if idx > 0 else "MAIN", "cdnPath": url}
                    for idx, url in enumerate(product.image_urls or [])
                ],
            })
    else:
        # 단일 옵션
        items.append({
            "itemName": product.name,
            "originalPrice": int(product.sale_price * 1.1),
            "salePrice": int(product.sale_price),
            "maximumBuyCount": 10,
            "maximumBuyForPerson": 10,
            "unitCount": 1,
            "attributes": [],
            "images": [
                {"imageOrder": idx, "imageType": "DETAIL" if idx > 0 else "MAIN", "cdnPath": url}
                for idx, url in enumerate(product.image_urls or [])
            ],
        })

    return {
        "displayCategoryCode": product.coupang_category_id or 497009,
        "sellerProductName": product.name,
        "vendorId": vendor_id,
        "saleStartedAt": "2020-01-01T00:00:00",
        "saleEndedAt": "2099-01-01T00:00:00",
        "displayProductName": product.name,
        "brand": product.brand or "",
        "manufacture": product.manufacturer or "",
        "origin": product.origin or "대한민국",
        "productGroup": product.coupang_category_name or "기타",
        "deliveryMethod": "SEQUENCIAL",
        "deliveryCompanyCode": "CJGLS",
        "deliveryChargeType": "FREE",
        "deliveryCharge": 0,
        "freeShipOverAmount": 0,
        "returnChargeVendor": "",
        "returnCharge": 5000,
        "outboundShippingTimeDay": 2,
        "returnCenterCode": "",
        "items": items,
        "contents": {
            "contentsType": "HTML",
            "contentsBody": product.detail_page_html or "",
        },
        "notices": [],
        "attributes": [],
        "requiredDocuments": [],
    }
