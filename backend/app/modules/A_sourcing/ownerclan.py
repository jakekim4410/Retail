"""
모듈 A — 오너클랜 API 클라이언트
실제 API 키가 없을 때는 MOCK_MODE=true 로 샘플 데이터를 반환합니다.
"""
from __future__ import annotations
import httpx
import json
from datetime import datetime
from typing import Any
from app.config import get_settings

settings = get_settings()

# ── Mock 샘플 상품 데이터 ─────────────────────────────────────────────────────
MOCK_PRODUCTS = [
    {
        "source_id": "OC-001",
        "name": "프리미엄 무선 블루투스 이어폰 TWS5Pro",
        "brand": "소닉웨이브",
        "manufacturer": "(주)소닉웨이브",
        "origin": "대한민국",
        "wholesale_price": 18000,
        "source_category_code": "ELEC-AUDIO",
        "image_urls": [
            "https://picsum.photos/seed/earphone1/600/600",
            "https://picsum.photos/seed/earphone2/600/600",
        ],
        "specs": {
            "연결방식": "블루투스 5.3",
            "배터리": "이어폰 6시간 / 케이스 포함 30시간",
            "방수": "IPX5",
            "드라이버": "10mm 다이나믹",
            "무게": "이어폰 5g / 케이스 45g",
        },
        "options": {"색상": ["블랙", "화이트", "네이비"]},
        "stock": 350,
    },
    {
        "source_id": "OC-002",
        "name": "에코 스테인리스 보온보냉 텀블러 500ml",
        "brand": "그린라이프",
        "manufacturer": "(주)그린라이프",
        "origin": "대한민국",
        "wholesale_price": 6500,
        "source_category_code": "KITCHEN-CUP",
        "image_urls": [
            "https://picsum.photos/seed/tumbler1/600/600",
        ],
        "specs": {
            "용량": "500ml",
            "소재": "18-8 스테인리스",
            "보온보냉": "12시간",
            "사이즈": "직경 7cm × 높이 22cm",
            "무게": "280g",
        },
        "options": {"색상": ["실버", "블랙", "핑크", "그린"]},
        "stock": 1200,
    },
    {
        "source_id": "OC-003",
        "name": "인체공학 메모리폼 목베개 여행용",
        "brand": "슬리피",
        "manufacturer": "(주)슬리피코리아",
        "origin": "대한민국",
        "wholesale_price": 8800,
        "source_category_code": "TRAVEL-ACC",
        "image_urls": [
            "https://picsum.photos/seed/pillow1/600/600",
        ],
        "specs": {
            "소재": "메모리폼 + 밸벳 커버",
            "사이즈": "35cm × 30cm",
            "무게": "210g",
            "세탁": "커버 분리세탁 가능",
        },
        "options": {"색상": ["그레이", "네이비", "베이지"]},
        "stock": 580,
    },
    {
        "source_id": "OC-004",
        "name": "LED 독서등 USB 충전식 클립형",
        "brand": "루멘",
        "manufacturer": "(주)루멘테크",
        "origin": "중국",
        "wholesale_price": 5200,
        "source_category_code": "ELEC-LIGHT",
        "image_urls": [
            "https://picsum.photos/seed/lamp1/600/600",
        ],
        "specs": {
            "광원": "LED 36구",
            "밝기단계": "3단계 조절",
            "충전": "USB-C 충전 (배터리 내장)",
            "사용시간": "최대 8시간",
            "색온도": "4000K 자연광",
        },
        "options": {"색상": ["화이트", "블랙"]},
        "stock": 890,
    },
    {
        "source_id": "OC-005",
        "name": "천연라텍스 요가매트 6mm 논슬립",
        "brand": "요기플로우",
        "manufacturer": "(주)요기플로우",
        "origin": "대한민국",
        "wholesale_price": 22000,
        "source_category_code": "SPORTS-YOGA",
        "image_urls": [
            "https://picsum.photos/seed/yoga1/600/600",
        ],
        "specs": {
            "소재": "천연라텍스 + TPE",
            "두께": "6mm",
            "사이즈": "183cm × 61cm",
            "무게": "1.8kg",
            "특징": "논슬립 양면 패턴, 정렬선 인쇄",
        },
        "options": {"색상": ["퍼플", "블루", "블랙", "핑크"]},
        "stock": 240,
    },
    {
        "source_id": "OC-006",
        "name": "마이크로화이버 청소포 10매입 극세사",
        "brand": "클린킹",
        "manufacturer": "(주)클린킹",
        "origin": "대한민국",
        "wholesale_price": 3200,
        "source_category_code": "CLEAN-CLOTH",
        "image_urls": [
            "https://picsum.photos/seed/cloth1/600/600",
        ],
        "specs": {
            "소재": "극세사 80% + 폴리에스터 20%",
            "사이즈": "30cm × 30cm",
            "매수": "10매",
            "용도": "유리, 가전, 가구 등 다목적",
            "세탁": "기계세탁 가능",
        },
        "options": {},
        "stock": 3000,
    },
    {
        "source_id": "OC-007",
        "name": "아로마 디퓨저 초음파 가습기 300ml",
        "brand": "에센샤",
        "manufacturer": "(주)에센샤",
        "origin": "대한민국",
        "wholesale_price": 14500,
        "source_category_code": "HOME-DIFFUSER",
        "image_urls": [
            "https://picsum.photos/seed/diffuser1/600/600",
        ],
        "specs": {
            "용량": "300ml",
            "작동시간": "최대 10시간",
            "소음": "30dB 이하 저소음",
            "LED": "7가지 무드등 색상",
            "소재": "PP + 실리콘",
        },
        "options": {"색상": ["화이트", "우드브라운"]},
        "stock": 420,
    },
    {
        "source_id": "OC-008",
        "name": "스마트폰 거치대 차량용 송풍구 자석식",
        "brand": "그립스타",
        "manufacturer": "(주)그립스타",
        "origin": "중국",
        "wholesale_price": 4100,
        "source_category_code": "CAR-ACC",
        "image_urls": [
            "https://picsum.photos/seed/holder1/600/600",
        ],
        "specs": {
            "장착방식": "송풍구 클립 + 자석흡착",
            "호환": "4~7인치 스마트폰 전기종",
            "자석": "N52 네오디뮴 자석 6개",
            "소재": "ABS + 알루미늄합금",
        },
        "options": {"색상": ["실버", "블랙"]},
        "stock": 1500,
    },
]


class OwnerClanClient:
    """오너클랜 API 클라이언트 (Mock 모드 포함)"""

    def __init__(self):
        self.api_key = settings.ownerclan_api_key
        self.api_secret = settings.ownerclan_api_secret
        self.base_url = settings.ownerclan_base_url
        self.mock_mode = settings.mock_mode or not self.api_key

    async def get_new_products(
        self,
        page: int = 1,
        page_size: int = 50,
        category_code: str | None = None,
    ) -> dict[str, Any]:
        """신상품 목록 조회"""
        if self.mock_mode:
            products = MOCK_PRODUCTS
            if category_code:
                products = [p for p in products if p["source_category_code"] == category_code]
            start = (page - 1) * page_size
            end = start + page_size
            return {
                "total": len(products),
                "page": page,
                "page_size": page_size,
                "products": products[start:end],
                "mock": True,
            }

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/v1/products/new",
                headers=self._auth_headers(),
                params={"page": page, "pageSize": page_size, "categoryCode": category_code},
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_product_detail(self, source_id: str) -> dict[str, Any] | None:
        """상품 상세 조회"""
        if self.mock_mode:
            product = next((p for p in MOCK_PRODUCTS if p["source_id"] == source_id), None)
            if product:
                return {**product, "mock": True}
            return None

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/v1/products/{source_id}",
                headers=self._auth_headers(),
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_stock(self, source_id: str) -> int:
        """재고 수량 조회"""
        if self.mock_mode:
            product = next((p for p in MOCK_PRODUCTS if p["source_id"] == source_id), None)
            return product["stock"] if product else 0

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/v1/products/{source_id}/stock",
                headers=self._auth_headers(),
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json().get("stock", 0)

    def _auth_headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "X-API-Secret": self.api_secret,
            "Content-Type": "application/json",
        }


# 싱글톤
ownerclan_client = OwnerClanClient()
