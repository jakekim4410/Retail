"""
모듈 C — 쿠팡 Open API 클라이언트 (실제 API 전용)
인증: HMAC-SHA256 서명 (쿠팡 표준 방식)
"""
from __future__ import annotations
import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Any, Optional
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CoupangClient:
    """쿠팡 Open API 클라이언트 — 실제 API 전용"""

    BASE = settings.coupang_base_url

    def __init__(self):
        self.access_key = settings.coupang_access_key
        self.secret_key = settings.coupang_secret_key
        self.vendor_id = settings.coupang_vendor_id
        if not self.access_key or not self.secret_key or not self.vendor_id:
            logger.error("[쿠팡] API 키가 .env에 설정되어 있지 않습니다!")

    # ── 인증 ───────────────────────────────────────────────────────────────
    def _generate_hmac(self, method: str, path: str, query: str = "") -> dict[str, str]:
        """쿠팡 HMAC-SHA256 인증 헤더 생성 (쿠팡 Open API 표준)"""
        datetime_str = datetime.now(timezone.utc).strftime("%y%m%dT%H%M%SZ")
        message = f"{datetime_str}{method}{path}{query}"
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {
            "Authorization": (
                f"CEA algorithm=HmacSHA256, access-key={self.access_key}, "
                f"signed-date={datetime_str}, signature={signature}"
            ),
            "X-Coupang-Target-Market": "KR",
            "Content-Type": "application/json;charset=UTF-8",
        }

    # ── 상품 등록 ───────────────────────────────────────────────────────────
    async def create_product(self, payload: dict[str, Any]) -> dict[str, Any]:
        """상품 임시저장 (등록 요청)"""
        path = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
        headers = self._generate_hmac("POST", path)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE}{path}",
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def update_product_status(
        self, product_id: str, status: str = "SALE"
    ) -> dict[str, Any]:
        """상품 판매 상태 변경 (임시저장 → 판매 중)"""
        path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{product_id}/status/{status}"
        headers = self._generate_hmac("PUT", path)
        async with httpx.AsyncClient() as client:
            resp = await client.put(f"{self.BASE}{path}", headers=headers, timeout=30.0)
            resp.raise_for_status()
            return resp.json()

    async def update_price(self, product_id: str, sale_price: int) -> dict[str, Any]:
        """상품 가격 변경"""
        path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{product_id}/prices"
        headers = self._generate_hmac("PUT", path)
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{self.BASE}{path}",
                headers=headers,
                json={"vendorItemId": product_id, "price": sale_price},
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def delist_product(self, product_id: str) -> dict[str, Any]:
        """상품 하차 (판매 중단)"""
        path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{product_id}/status/STOP_SALE"
        headers = self._generate_hmac("PUT", path)
        async with httpx.AsyncClient() as client:
            resp = await client.put(f"{self.BASE}{path}", headers=headers, timeout=30.0)
            resp.raise_for_status()
            return resp.json()

    async def get_orders(
        self,
        status: str = "ACCEPT",
        created_at_from: Optional[str] = None,
        created_at_to: Optional[str] = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """주문 목록 조회"""
        path = f"/v2/providers/openapi/apis/api/v4/vendors/{self.vendor_id}/ordersheets"
        query = f"?status={status}&pageSize={page_size}"
        if created_at_from:
            query += f"&createdAtFrom={created_at_from}"
        if created_at_to:
            query += f"&createdAtTo={created_at_to}"
        headers = self._generate_hmac("GET", path, query)
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE}{path}{query}",
                headers=headers,
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()


# 싱글톤
coupang_client = CoupangClient()
