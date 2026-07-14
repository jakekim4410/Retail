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
from typing import Any, Optional
from app.config import get_settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Mock 카테고리 데이터 ───────────────────────────────────────────────────────
MOCK_CATEGORIES = [
    {"code": "ELEC-AUDIO",   "name": "이어폰/음향",   "icon": "🎧", "count": 124},
    {"code": "ELEC-LIGHT",   "name": "조명/LED",       "icon": "💡", "count": 87},
    {"code": "ELEC-ETC",     "name": "전자기기 기타",  "icon": "🔌", "count": 203},
    {"code": "KITCHEN-CUP",  "name": "컵/텀블러",      "icon": "☕", "count": 156},
    {"code": "KITCHEN-ETC",  "name": "주방용품",        "icon": "🍳", "count": 312},
    {"code": "TRAVEL-ACC",   "name": "여행소품",        "icon": "✈️", "count": 98},
    {"code": "SPORTS-YOGA",  "name": "요가/피트니스",  "icon": "🧘", "count": 145},
    {"code": "SPORTS-ETC",   "name": "스포츠 기타",    "icon": "⚽", "count": 267},
    {"code": "CLEAN-CLOTH",  "name": "청소/세탁용품",  "icon": "🧹", "count": 189},
    {"code": "HOME-DIFFUSER","name": "디퓨저/방향제", "icon": "🌸", "count": 76},
    {"code": "HOME-ETC",     "name": "홈데코/인테리어","icon": "🏠", "count": 421},
    {"code": "CAR-ACC",      "name": "차량용품",        "icon": "🚗", "count": 134},
    {"code": "BEAUTY",       "name": "뷰티/화장품",    "icon": "💄", "count": 389},
    {"code": "FASHION",      "name": "패션/의류",       "icon": "👕", "count": 512},
    {"code": "FOOD",         "name": "식품/건강",       "icon": "🥗", "count": 278},
]

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
    AUTH_URL = "https://auth.ownerclan.com/auth"  # 공식 인증 엔드포인트

    def __init__(self):
        self.username = settings.ownerclan_username
        self.password = settings.ownerclan_password
        self.mock_mode = settings.mock_mode or not self.username or not self.password
        self._jwt_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    async def _authenticate(self) -> None:
        """ID/PW로 JWT 토큰 발급 (공식 매뉴얼 기준)
        
        POST https://auth.ownerclan.com/auth
        Body: { service, userType, username, password }
        Response: JWT 토큰 문자열 (raw string)
        """
        logger.info("[오너클랜] JWT 인증 요청")
        auth_payload = {
            "service": "ownerclan",
            "userType": "seller",
            "username": self.username,
            "password": self.password,
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(
                    self.AUTH_URL,
                    json=auth_payload,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 200:
                    # 응답이 raw JWT 문자열이거나 JSON 객체일 수 있음
                    token = resp.text.strip()
                    # JSON 형태인 경우 파싱
                    if token.startswith('{'):
                        data = resp.json()
                        token = data.get("token") or data.get("access_token") or data.get("jwt", "")
                    self._jwt_token = token
                    # 토큰 만료: 30일 (exp 클레임 기준)
                    self._token_expires_at = datetime.now().timestamp() + (29 * 24 * 3600)
                    logger.info("[오너클랜] 인증 성공")
                    return
                else:
                    error_msg = resp.text
                    try:
                        error_msg = resp.json().get("message", resp.text)
                    except Exception:
                        pass
                    raise HTTPException(
                        status_code=401,
                        detail=f"오너클랜 인증 실패: {error_msg}"
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"[오너클랜] 인증 오류: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"오너클랜 API 연결 오류: {str(e)}"
                )

    async def _get_headers(self) -> dict[str, str]:
        if self._jwt_token is None or datetime.now().timestamp() > self._token_expires_at:
            await self._authenticate()
        return {
            "Authorization": f"Bearer {self._jwt_token}",
            "Content-Type": "application/json",
        }

    async def _graphql(self, query: str, variables: Optional[dict] = None) -> dict[str, Any]:
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
        # 이미지: images(size: large) 배열
        images = node.get("images") or []
        if isinstance(images, list):
            # 문자열 URL 배열 그대로 사용
            images = [img if isinstance(img, str) else img.get("url", "") for img in images]
        
        # 가격: price(currency: KRW) -> 정수
        price = node.get("price") or 0
        
        # 카테고리: {key, name}
        category = node.get("category") or {}
        category_code = category.get("key", "") if isinstance(category, dict) else str(category)
        category_name = category.get("name", "") if isinstance(category, dict) else ""
        
        # 옵션: [{price, quantity, key, optionAttributes: [{name, value}]}]
        raw_options = node.get("options") or []
        # 재고 = 옵션 수량 합계
        stock = sum(opt.get("quantity", 0) for opt in raw_options if isinstance(opt, dict))
        if stock == 0:
            stock = node.get("stock") or 0
        
        # 옵션을 {"선택속성명": ["val1", "val2"]} 형태로 정리
        options_dict: dict = {}
        for opt in raw_options:
            if not isinstance(opt, dict):
                continue
            for attr in (opt.get("optionAttributes") or []):
                name = attr.get("name", "")
                value = attr.get("value", "")
                if name:
                    options_dict.setdefault(name, [])
                    if value and value not in options_dict[name]:
                        options_dict[name].append(value)

        return {
            "source_id": str(node.get("key") or ""),
            "name": node.get("name") or "",
            "brand": node.get("brand") or "",
            "manufacturer": node.get("manufacturer") or "",
            "origin": node.get("origin") or "",
            "wholesale_price": float(price),
            "source_category_code": category_code,
            "source_category_name": category_name,
            "image_urls": images,
            "specs": node.get("attributes") or {},
            "options": options_dict,
            "stock": stock,
        }

    async def get_categories(self) -> list[dict[str, Any]]:
        """소싱 가능 카테고리 목록 반환"""
        if self.mock_mode:
            return MOCK_CATEGORIES
        try:
            query = """
            query {
              allCategories(first: 20) {
                edges {
                  node {
                    key
                    name
                  }
                }
              }
            }
            """
            data = await self._graphql(query)
            edges = data.get("allCategories", {}).get("edges", [])
            categories = []
            for e in edges:
                node = e.get("node", {})
                if node.get("key"):
                    categories.append({
                        "code": node.get("key"),
                        "name": node.get("name"),
                        "icon": "📦",
                        "count": 0
                    })
            return categories if categories else MOCK_CATEGORIES
        except Exception as e:
            logger.warning(f"[오너클랜] 카테고리 조회 실패, Mock fallback 사용: {e}")
            return MOCK_CATEGORIES

    async def get_new_products(
        self,
        page: int = 1,
        page_size: int = 50,
        category_code: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> dict[str, Any]:
        """신상품 목록 조회 - GraphQL allItems"""
        if self.mock_mode:
            return self._mock_products(page, page_size, category_code, keyword)

        # 실제 API 호출 — 실패 시 Mock fallback
        try:
            return await self._real_get_new_products(page, page_size, category_code, keyword)
        except Exception as e:
            logger.warning(f"[오너클랜] 실제 API 호출 실패, Mock fallback 사용: {e}")
            return self._mock_products(page, page_size, category_code, keyword)

    def _mock_products(self, page: int, page_size: int, category_code: Optional[str], keyword: Optional[str] = None) -> dict[str, Any]:
        """Mock 상품 목록 반환"""
        products = MOCK_PRODUCTS
        if category_code:
            products = [p for p in products if p["source_category_code"] == category_code]
        if keyword:
            products = [p for p in products if keyword.lower() in p["name"].lower() or keyword.lower() in p.get("specs", {}).values()]
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "total": len(products),
            "page": page,
            "page_size": page_size,
            "products": products[start:end],
            "mock": True,
        }

    async def _real_get_new_products(
        self,
        page: int = 1,
        page_size: int = 50,
        category_code: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> dict[str, Any]:
        """실제 오너클랜 GraphQL API 호출"""

        # GraphQL cursor-based pagination
        first = page_size
        query = """
        query GetItems($first: Int, $after: String, $category: String, $keyword: String) {
          allItems(first: $first, after: $after, category: $category, query: $keyword) {
            edges {
              node {
                key
                name
                origin
                price(currency: KRW)
                images(size: large)
                category { key name }
                options {
                  price(currency: KRW)
                  quantity
                  key
                  optionAttributes { name value }
                }
                attributes
                status
              }
              cursor
            }
            pageInfo {
              hasNextPage
              count
              startCursor
              endCursor
            }
          }
        }
        """
        variables: dict[str, Any] = {"first": first}
        if category_code:
            variables["category"] = category_code
        if keyword:
            variables["keyword"] = keyword
            
        data = await self._graphql(query, variables)

        edges = data.get("allItems", {}).get("edges") or []
        page_info = data.get("allItems", {}).get("pageInfo") or {}
        products = [self._parse_item(edge["node"]) for edge in edges if "node" in edge]

        return {
            "total": page_info.get("count", len(products)),
            "page": page,
            "page_size": page_size,
            "products": products,
            "mock": False,
        }

    async def get_product_detail(self, source_id: str) -> Optional[dict[str, Any]]:
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
