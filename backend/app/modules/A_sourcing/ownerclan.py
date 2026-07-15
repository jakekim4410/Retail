"""
모듈 A — 오너클랜 GraphQL API 클라이언트 (실제 API 전용)
- JWT 인증 후 Bearer 토큰으로 요청
- Endpoint: https://api.ownerclan.com/v1/graphql
"""
from __future__ import annotations
import httpx
import logging
from datetime import datetime
from typing import Any, Optional
from app.config import get_settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)
settings = get_settings()


class OwnerClanClient:
    """오너클랜 GraphQL API 클라이언트 — 실제 API 전용"""

    GRAPHQL_URL = "https://api.ownerclan.com/v1/graphql"
    AUTH_URL = "https://auth.ownerclan.com/auth"

    def __init__(self):
        self.username = settings.ownerclan_username
        self.password = settings.ownerclan_password
        self._jwt_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        if not self.username or not self.password:
            logger.error("[오너클랜] ID/PW가 .env에 설정되어 있지 않습니다!")

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
                    token = resp.text.strip()
                    if token.startswith('{'):
                        data = resp.json()
                        token = data.get("token") or data.get("access_token") or data.get("jwt", "")
                    self._jwt_token = token
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
        images = node.get("images") or []
        if isinstance(images, list):
            images = [img if isinstance(img, str) else img.get("url", "") for img in images]

        price = node.get("price") or 0

        category = node.get("category") or {}
        category_code = category.get("key", "") if isinstance(category, dict) else str(category)
        category_name = category.get("name", "") if isinstance(category, dict) else ""

        raw_options = node.get("options") or []
        stock = sum(opt.get("quantity", 0) for opt in raw_options if isinstance(opt, dict))
        if stock == 0:
            stock = node.get("stock") or 0

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
        try:
            query = """
            query {
              allCategories(first: 50) {
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
            return categories
        except Exception as e:
            logger.error(f"[오너클랜] 카테고리 조회 실패: {e}")
            raise

    async def get_new_products(
        self,
        page: int = 1,
        page_size: int = 50,
        category_code: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> dict[str, Any]:
        """신상품 목록 조회 - GraphQL allItems"""
        return await self._real_get_new_products(page, page_size, category_code, keyword)

    async def _real_get_new_products(
        self,
        page: int = 1,
        page_size: int = 50,
        category_code: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> dict[str, Any]:
        """실제 오너클랜 GraphQL API 호출"""

        first = page_size
        query = """
        query GetItems($first: Int, $after: String, $category: String, $keyword: String) {
          allItems(first: $first, after: $after, category: $category, search: $keyword) {
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
        }

    async def get_product_detail(self, source_id: str) -> Optional[dict[str, Any]]:
        """상품 상세 조회 - GraphQL item(key:)"""
        query = """
        query GetItem($key: String!) {
          item(key: $key) {
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
        }
        """
        data = await self._graphql(query, {"key": source_id})
        node = data.get("item")
        if not node:
            return None
        return self._parse_item(node)

    async def get_stock(self, source_id: str) -> int:
        """재고 수량 조회"""
        detail = await self.get_product_detail(source_id)
        return detail.get("stock", 0) if detail else 0


# 싱글톤
ownerclan_client = OwnerClanClient()
