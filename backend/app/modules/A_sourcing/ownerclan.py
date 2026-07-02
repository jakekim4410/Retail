"""
모듈 A — 오너클랜 GraphQL API 클라이언트
- JWT 인증 후 Bearer 토큰으로 요청
- Endpoint: https://api-sandbox.ownerclan.com/v1/graphql (sandbox)
               https://api.ownerclan.com/v1/graphql (production)
"""
from __future__ import annotations
import httpx
import json
import logging
from datetime import datetime
from typing import Any
from app.config import get_settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)
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
    """오너클랜 GraphQL API 클라이언트 (Mock 모드 포함)"""

    # Production: https://api.ownerclan.com/v1/graphql
    # Sandbox:    https://api-sandbox.ownerclan.com/v1/graphql
    GRAPHQL_URL = "https://api.ownerclan.com/v1/graphql"
    AUTH_URL = "https://api.ownerclan.com/v1/auth"

    def __init__(self):
        self.username = settings.ownerclan_username
        self.password = settings.ownerclan_password
        self.mock_mode = settings.mock_mode or not self.username or not self.password
        self._jwt_token: str | None = None
        self._token_expires_at: float = 0.0

    async def _authenticate(self) -> None:
        """ID/PW로 JWT 토큰 발급"""
        logger.info("[오너클랜] JWT 인증 요청")
        
        # Try standard auth endpoint first, fall back to sandbox pattern
        auth_payload = {
            "service": "ownerclan",
            "userType": "seller",
            "username": self.username,
            "password": self.password,
        }
        
        # GraphQL mutation for auth (some implementations use this)
        auth_query = """
        mutation Login($username: String!, $password: String!) {
          login(username: $username, password: $password) {
            token
            expiresAt
          }
        }
        """
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # First try REST auth endpoint
            try:
                resp = await client.post(
                    self.AUTH_URL,
                    json=auth_payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    token = data.get("token") or data.get("access_token") or data.get("jwt")
                    if token:
                        self._jwt_token = token
                        self._token_expires_at = datetime.now().timestamp() + (29 * 24 * 3600)
                        logger.info("[오너클랜] REST 인증 성공")
                        return
            except Exception as e:
                logger.warning(f"[오너클랜] REST 인증 실패: {e}")

            # Try GraphQL mutation for auth
            try:
                resp = await client.post(
                    self.GRAPHQL_URL,
                    json={"query": auth_query, "variables": {"username": self.username, "password": self.password}},
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    token = data.get("data", {}).get("login", {}).get("token")
                    if token:
                        self._jwt_token = token
                        self._token_expires_at = datetime.now().timestamp() + (23 * 3600)
                        logger.info("[오너클랜] GraphQL 인증 성공")
                        return
                    errors = data.get("errors")
                    if errors:
                        raise HTTPException(status_code=401, detail=f"오너클랜 인증 실패: {errors[0].get('message', '계정 정보를 확인해주세요.')}")
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"[오너클랜] GraphQL 인증 실패: {e}")
            
            raise HTTPException(
                status_code=401,
                detail="오너클랜 API 인증에 실패했습니다. Render 환경변수의 OWNERCLAN_USERNAME/PASSWORD를 확인해주세요."
            )

    async def _get_headers(self) -> dict[str, str]:
        if self._jwt_token is None or datetime.now().timestamp() > self._token_expires_at:
            await self._authenticate()
        return {
            "Authorization": f"Bearer {self._jwt_token}",
            "Content-Type": "application/json",
        }

    async def _graphql(self, query: str, variables: dict | None = None) -> dict[str, Any]:
        """GraphQL 요청 실행"""
        headers = await self._get_headers()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                self.GRAPHQL_URL,
                json={"query": query, "variables": variables or {}},
                headers=headers,
            )
            if resp.status_code == 401:
                # Token expired - re-authenticate once
                self._jwt_token = None
                headers = await self._get_headers()
                resp = await client.post(
                    self.GRAPHQL_URL,
                    json={"query": query, "variables": variables or {}},
                    headers=headers,
                )
            resp.raise_for_status()
            data = resp.json()
            if "errors" in data:
                raise HTTPException(status_code=400, detail=f"오너클랜 GraphQL 오류: {data['errors'][0].get('message')}")
            return data.get("data", {})

    def _parse_item(self, node: dict) -> dict[str, Any]:
        """GraphQL item 노드를 내부 상품 형식으로 변환"""
        # 오너클랜 GraphQL 응답 필드 매핑
        images = []
        if node.get("images"):
            images = [img.get("url", img) if isinstance(img, dict) else img for img in node["images"]]
        elif node.get("imageUrl"):
            images = [node["imageUrl"]]
        elif node.get("image"):
            images = [node["image"]]

        price = node.get("price") or node.get("supplyPrice") or node.get("wholesalePrice") or 0
        
        category = node.get("category", {})
        if isinstance(category, dict):
            category_code = category.get("code") or category.get("key") or category.get("id", "")
        else:
            category_code = str(category)

        return {
            "source_id": str(node.get("key") or node.get("id") or node.get("itemKey", "")),
            "name": node.get("name") or node.get("itemName", ""),
            "brand": node.get("brand") or node.get("brandName", ""),
            "manufacturer": node.get("manufacturer", ""),
            "origin": node.get("origin") or node.get("madeIn", ""),
            "wholesale_price": float(price),
            "source_category_code": category_code,
            "image_urls": images,
            "specs": node.get("specs") or node.get("attributes") or {},
            "options": node.get("options") or {},
            "stock": node.get("stock") or node.get("stockCount") or node.get("quantity", 0),
        }

    async def get_new_products(
        self,
        page: int = 1,
        page_size: int = 50,
        category_code: str | None = None,
    ) -> dict[str, Any]:
        """신상품 목록 조회 - GraphQL allItems"""
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

        # GraphQL cursor-based pagination
        # page → convert to cursor-based (approximate)
        first = page_size
        # Note: allItems uses cursor pagination; we compute offset via after cursor
        query = """
        query GetItems($first: Int, $after: String, $category: String) {
          allItems(first: $first, after: $after, category: $category) {
            edges {
              node {
                key
                name
                brand
                manufacturer
                origin
                price
                supplyPrice
                stock
                images { url }
                category { code name }
                specs
                options
              }
              cursor
            }
            pageInfo {
              hasNextPage
              endCursor
              totalCount
            }
          }
        }
        """
        
        variables: dict[str, Any] = {"first": first}
        if category_code:
            variables["category"] = category_code
        # For page > 1, we'd need cursor; for now just fetch first page
        # TODO: implement cursor caching for multi-page support
        
        try:
            data = await self._graphql(query, variables)
        except Exception:
            # Try alternative field name
            query2 = """
            query GetItems($first: Int) {
              items(first: $first) {
                edges {
                  node {
                    key
                    name
                    price
                    stock
                    category { code name }
                    images { url }
                  }
                }
                pageInfo { totalCount hasNextPage }
              }
            }
            """
            data = await self._graphql(query2, {"first": first})

        # Parse response - try different response shapes
        edges = (
            data.get("allItems", {}).get("edges")
            or data.get("items", {}).get("edges")
            or []
        )
        page_info = (
            data.get("allItems", {}).get("pageInfo")
            or data.get("items", {}).get("pageInfo")
            or {}
        )

        products = [self._parse_item(edge["node"]) for edge in edges if "node" in edge]

        return {
            "total": page_info.get("totalCount", len(products)),
            "page": page,
            "page_size": page_size,
            "products": products,
            "mock": False,
        }

    async def get_product_detail(self, source_id: str) -> dict[str, Any] | None:
        """상품 상세 조회 - GraphQL item(key:)"""
        if self.mock_mode:
            product = next((p for p in MOCK_PRODUCTS if p["source_id"] == source_id), None)
            if product:
                return {**product, "mock": True}
            return None

        query = """
        query GetItem($key: String!) {
          item(key: $key) {
            key
            name
            brand
            manufacturer
            origin
            price
            supplyPrice
            stock
            images { url }
            category { code name }
            specs
            options
          }
        }
        """
        data = await self._graphql(query, {"key": source_id})
        node = data.get("item")
        if not node:
            return None
        return self._parse_item(node)

    async def get_stock(self, source_id: str) -> int:
        """재고 수량 조회"""
        if self.mock_mode:
            product = next((p for p in MOCK_PRODUCTS if p["source_id"] == source_id), None)
            return product["stock"] if product else 0

        detail = await self.get_product_detail(source_id)
        return detail.get("stock", 0) if detail else 0


# 싱글톤
ownerclan_client = OwnerClanClient()
