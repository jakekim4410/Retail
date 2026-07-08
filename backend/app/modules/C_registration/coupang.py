"""
모듈 C — 쿠팡 Open API 클라이언트
인증: HMAC-SHA256 서명 (쿠팡 표준 방식)
Mock 모드: MOCK_MODE=true 이면 실제 API 호출 없이 성공 응답 반환
"""
from __future__ import annotations
import hashlib
import hmac
import time
import uuid
from datetime import datetime, timezone
from typing import Any
import httpx

from app.config import get_settings

settings = get_settings()


class CoupangClient:
    """쿠팡 Open API 클라이언트"""

    BASE = settings.coupang_base_url

    def __init__(self):
        self.access_key = settings.coupang_access_key
        self.secret_key = settings.coupang_secret_key
        self.vendor_id = settings.coupang_vendor_id
        self.mock_mode = settings.mock_mode or not self.access_key

    # ── 인증 ───────────────────────────────────────────────────────────────
    def _generate_hmac(self, method: str, path: str, query: str = "") -> dict[str, str]:
        """쿠팡 HMAC-SHA256 인증 헤더 생성 (쿠팡 Open API 표준)"""
        datetime_str = datetime.now(timezone.utc).strftime("%y%m%dT%H%M%SZ")
        # 쿠팡 공식 서명 메시지 형식: datetime + method + path + query
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
        if self.mock_mode:
            mock_id = f"MOCK-{uuid.uuid4().hex[:8].upper()}"
            return {
                "code": "200",
                "message": "SUCCESS",
                "data": {
                    "productId": mock_id,
                    "vendorId": self.vendor_id or "VENDOR001",
                    "statusName": "임시저장",
                    "mock": True,
                },
            }

        path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"
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
        if self.mock_mode:
            return {"code": "200", "message": "SUCCESS", "data": {"productId": product_id, "status": status, "mock": True}}

        path = f"/v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{product_id}/status/{status}"
        headers = self._generate_hmac("PUT", path)
        async with httpx.AsyncClient() as client:
            resp = await client.put(f"{self.BASE}{path}", headers=headers, timeout=30.0)
            resp.raise_for_status()
            return resp.json()

    async def update_price(self, product_id: str, sale_price: int) -> dict[str, Any]:
        """상품 가격 변경"""
        if self.mock_mode:
            return {"code": "200", "message": "SUCCESS", "data": {"productId": product_id, "salePrice": sale_price, "mock": True}}

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
        if self.mock_mode:
            return {"code": "200", "message": "SUCCESS", "data": {"productId": product_id, "status": "STOP_SALE", "mock": True}}

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
        if self.mock_mode:
            return _mock_orders()

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


def _mock_orders() -> dict[str, Any]:
    """Mock 주문 데이터 생성"""
    import random
    from datetime import timedelta

    product_ids = [
        ("OC-001", "MOCK-A1B2C3D4", "프리미엄 무선 블루투스 이어폰 TWS5Pro", 25200),
        ("OC-002", "MOCK-B2C3D4E5", "에코 스테인리스 보온보냉 텀블러 500ml", 9100),
        ("OC-003", "MOCK-C3D4E5F6", "인체공학 메모리폼 목베개 여행용", 12300),
        ("OC-005", "MOCK-E5F6G7H8", "천연라텍스 요가매트 6mm 논슬립", 30800),
        ("OC-007", "MOCK-G7H8I9J0", "아로마 디퓨저 초음파 가습기 300ml", 20300),
    ]

    orders = []
    base_date = datetime.now() - timedelta(days=30)
    for i in range(25):
        source_id, coupang_id, name, price = random.choice(product_ids)
        qty = random.randint(1, 3)
        ordered_at = base_date + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
        )
        orders.append({
            "orderId": f"ORDER-{10000 + i}",
            "orderItemId": f"ITEM-{20000 + i}",
            "productId": coupang_id,
            "sourceId": source_id,
            "productName": name,
            "quantity": qty,
            "salePrice": price,
            "shippingPrice": 0,
            "totalOrderPrice": price * qty,
            "settlementAmount": round(price * qty * 0.9),
            "commissionAmount": round(price * qty * 0.07),
            "status": random.choice(["ACCEPT", "INSTRUCT", "DEPARTURE", "DELIVERED"]),
            "orderedAt": ordered_at.strftime("%Y-%m-%dT%H:%M:%S"),
        })

    return {
        "code": "200",
        "message": "SUCCESS",
        "data": orders,
        "total": len(orders),
        "mock": True,
    }


# 싱글톤
coupang_client = CoupangClient()
