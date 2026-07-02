"""
모듈 B — Gemini API를 이용한 상품 설명 문구 생성
API 키 없을 경우 규칙 기반 템플릿 문구 반환
"""
from __future__ import annotations
import hashlib
import json
from typing import Any
from app.config import get_settings

settings = get_settings()

# 메모리 캐시 (프로세스 내)
_cache: dict[str, str] = {}


def _cache_key(data: dict[str, Any]) -> str:
    serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(serialized.encode()).hexdigest()


def _rule_based_description(product_data: dict[str, Any]) -> str:
    """Gemini API 없을 때 규칙 기반 설명 생성"""
    name = product_data.get("name", "상품")
    brand = product_data.get("brand", "")
    origin = product_data.get("origin", "")
    specs = product_data.get("specs", {})

    spec_lines = "\n".join(f"• {k}: {v}" for k, v in specs.items())
    brand_text = f"{brand}의 " if brand else ""
    origin_text = f"{origin}에서 생산된 " if origin else ""

    desc = f"""
{brand_text}{name}을 소개합니다.

{origin_text}엄선된 소재와 뛰어난 품질로 제작된 {name}은
일상에서 편리하게 사용할 수 있도록 설계되었습니다.

【 주요 특징 】
{spec_lines}

꼼꼼하게 검수된 제품으로 믿고 구매하실 수 있습니다.
궁금하신 점은 문의 주시면 친절하게 안내해 드리겠습니다.
    """.strip()
    return desc


async def generate_product_description(product_data: dict[str, Any]) -> str:
    """
    상품 설명 문구 생성
    - Gemini API 사용 가능하면 → LLM 생성
    - 불가능하면 → 규칙 기반 템플릿
    """
    key = _cache_key(product_data)
    if key in _cache:
        return _cache[key]

    if not settings.gemini_api_key:
        result = _rule_based_description(product_data)
        _cache[key] = result
        return result

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)

        specs_text = "\n".join(
            f"- {k}: {v}" for k, v in (product_data.get("specs") or {}).items()
        )
        options_text = ""
        for opt_name, opt_vals in (product_data.get("options") or {}).items():
            if isinstance(opt_vals, list):
                options_text += f"- {opt_name}: {', '.join(str(v) for v in opt_vals)}\n"

        prompt = f"""당신은 쿠팡 상품 상세페이지 전문 카피라이터입니다.
아래 상품 정보를 바탕으로 구매 전환율을 높이는 매력적인 상품 설명을 작성해 주세요.

[상품명] {product_data.get('name', '')}
[브랜드] {product_data.get('brand', '')}
[제조국] {product_data.get('origin', '')}
[제조사] {product_data.get('manufacturer', '')}

[스펙]
{specs_text}

[옵션]
{options_text}

작성 규칙:
1. 500~800자 분량
2. 이모지 활용으로 가독성 향상
3. 주요 특징 3~5가지 강조
4. SEO 키워드 자연스럽게 포함
5. 고객 혜택 중심으로 작성 (스펙 나열보다 실제 사용 경험 강조)
6. 마지막에 구매 유도 문구 포함
7. HTML 태그 없이 순수 텍스트로 작성"""

        # Gemini는 비동기 생성을 지원합니다 (generate_content_async)
        response = await model.generate_content_async(prompt)
        result = response.text.strip()

    except Exception as e:
        print(f"[LLM] Gemini API 오류, 규칙 기반으로 대체: {e}")
        result = _rule_based_description(product_data)

    _cache[key] = result
    return result
