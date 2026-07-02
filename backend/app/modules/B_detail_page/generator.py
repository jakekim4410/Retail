"""
모듈 B — 상세페이지 HTML 생성기
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.modules.B_detail_page.llm_writer import generate_product_description

TEMPLATE_DIR = Path(__file__).parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)

# ── 카테고리별 상품정보제공고시 기본 템플릿 ──────────────────────────────────
NOTICE_TEMPLATES: dict[str, dict[str, str]] = {
    "ELEC": {
        "품명 및 모델명": "상품 상세 참조",
        "KC 인증 필 유무": "해당 없음 (해당되는 경우 인증번호 기재)",
        "정격전압/소비전력": "상품 상세 참조",
        "동일모델 출시년월": "상품 상세 참조",
        "제조자/수입자": "상품 상세 참조",
        "제조국": "상품 상세 참조",
        "크기": "상품 상세 참조",
        "무게": "상품 상세 참조",
        "주요 사양": "상품 상세 참조",
        "품질보증기준": "구입일로부터 1년",
        "A/S 책임자 및 전화번호": "판매자 문의",
    },
    "KITCHEN": {
        "품명 및 모델명": "상품 상세 참조",
        "재질": "상품 상세 참조",
        "용량": "상품 상세 참조",
        "치수": "상품 상세 참조",
        "제조자/수입자": "상품 상세 참조",
        "제조국": "상품 상세 참조",
        "세탁방법 및 취급시 주의사항": "제품 라벨 참조",
        "품질보증기준": "구입일로부터 1년",
        "A/S 책임자 및 전화번호": "판매자 문의",
    },
    "DEFAULT": {
        "품명 및 모델명": "상품 상세 참조",
        "제조자/수입자": "상품 상세 참조",
        "제조국": "상품 상세 참조",
        "크기, 무게, 색상": "상품 상세 참조",
        "재질": "상품 상세 참조",
        "품질보증기준": "구입일로부터 1년",
        "A/S 책임자 및 전화번호": "판매자 문의",
    },
}


def _get_notice_template(source_category_code: str, product_data: dict[str, Any]) -> dict[str, str]:
    """카테고리에 맞는 고시정보 템플릿 반환 (실제 값으로 치환)"""
    if "ELEC" in source_category_code:
        template = dict(NOTICE_TEMPLATES["ELEC"])
    elif "KITCHEN" in source_category_code:
        template = dict(NOTICE_TEMPLATES["KITCHEN"])
    else:
        template = dict(NOTICE_TEMPLATES["DEFAULT"])

    # 실제 상품 데이터로 치환 가능한 필드 치환
    if product_data.get("manufacturer"):
        for key in template:
            if "제조자" in key or "수입자" in key:
                template[key] = product_data["manufacturer"]
    if product_data.get("origin"):
        for key in template:
            if "제조국" in key:
                template[key] = product_data["origin"]

    specs = product_data.get("specs", {})
    if specs:
        if "무게" in specs:
            for key in template:
                if "무게" in key:
                    template[key] = specs["무게"]
        if "용량" in specs:
            for key in template:
                if "용량" in key:
                    template[key] = specs["용량"]
        if "소재" in specs or "재질" in specs:
            mat = specs.get("소재") or specs.get("재질", "상품 상세 참조")
            for key in template:
                if "재질" in key or "소재" in key:
                    template[key] = mat

    return template


async def generate_detail_page(product_data: dict[str, Any]) -> str:
    """
    상품 데이터를 받아 쿠팡 등록용 HTML 상세페이지를 생성합니다.
    Returns: HTML string
    """
    # 1. LLM 설명 생성
    description = await generate_product_description(product_data)

    # 2. 고시정보 템플릿
    notice_info = _get_notice_template(
        product_data.get("source_category_code", "DEFAULT"),
        product_data,
    )

    # 3. Jinja2 렌더링
    template = _jinja_env.get_template("product_detail.html")
    html = template.render(
        name=product_data.get("name", ""),
        brand=product_data.get("brand", ""),
        origin=product_data.get("origin", ""),
        manufacturer=product_data.get("manufacturer", ""),
        image_urls=product_data.get("image_urls", []),
        description=description,
        specs=product_data.get("specs") or {},
        options=product_data.get("options") or {},
        notice_info=notice_info,
    )
    return html
