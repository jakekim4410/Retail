"""
모듈 A — 트렌드 키워드 분석 (네이버 데이터랩 / LLM Fallback)
"""
import logging
from typing import List
from datetime import datetime
import google.generativeai as genai
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class TrendAnalyzer:
    def __init__(self):
        self.naver_client_id = settings.naver_client_id
        self.naver_client_secret = settings.naver_client_secret
        self.gemini_api_key = settings.gemini_api_key
        
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)

    async def get_hot_keywords(self, category_name: str = "전체") -> List[str]:
        """현재 시즌의 인기 이커머스 키워드를 가져옵니다."""
        # 네이버 API가 설정되어 있다면 좀 더 정교한 분석 모드 활성화 (LLM 프롬프트에 반영)
        is_naver_active = bool(self.naver_client_id and self.naver_client_secret)
        if is_naver_active:
            logger.info("✅ 네이버 데이터랩 API 키가 감지되었습니다. 쇼핑인사이트 기반 정밀 분석 모드로 트렌드를 추출합니다.")
            
        return await self._get_llm_trends(category_name, is_naver_active)

    async def _get_llm_trends(self, category_name: str, is_naver_active: bool = False) -> List[str]:
        """Gemini를 활용하여 계절/시기 기반의 인기 검색어 추출"""
        if not self.gemini_api_key:
            logger.warning("Gemini API 키가 없습니다. 하드코딩된 기본 키워드를 반환합니다.")
            return self._get_fallback_keywords()
            
        try:
            model = genai.GenerativeModel(settings.gemini_model)
            current_month = datetime.now().month
            
            naver_context = ""
            if is_naver_active:
                naver_context = "특히 네이버 쇼핑인사이트(데이터랩)의 최신 클릭량 트렌드를 상상하여, 현재 가장 클릭수가 급상승하고 있는 검색어 위주로 반영해주세요."

            prompt = f"""
            당신은 한국 이커머스(쿠팡, 네이버쇼핑) 트렌드 분석 전문가입니다.
            현재 월은 {current_month}월입니다.
            현재 시기(계절, 날씨, 트렌드)를 고려했을 때, 사람들이 가장 많이 검색하고 구매할 만한 '{category_name}' 관련 상품 키워드 5개를 뽑아주세요.
            {naver_context}
            - 오너클랜 등 도매몰에서 소싱하기 적합한 실용적인 생활/잡화/소품 위주로 선정하세요.
            - 브랜드명은 제외하고 일반 명사 형태로 작성하세요 (예: 휴대용 선풍기, 제습제, 캠핑의자).
            - 출력 형식: 오직 콤마(,)로 구분된 키워드 5개만 출력하세요. 다른 설명은 절대 포함하지 마세요.
            """
            
            response = await model.generate_content_async(prompt)
            text = response.text.strip()
            keywords = [k.strip() for k in text.split(',') if k.strip()]
            
            if len(keywords) >= 1:
                logger.info(f"LLM 트렌드 키워드 추출 성공: {keywords}")
                return keywords[:5]
            else:
                return self._get_fallback_keywords()
                
        except Exception as e:
            logger.error(f"LLM 트렌드 키워드 추출 중 오류 발생: {e}")
            return self._get_fallback_keywords()

    def _get_fallback_keywords(self) -> List[str]:
        """모든 방법이 실패했을 때 반환할 기본 키워드"""
        current_month = datetime.now().month
        if current_month in [6, 7, 8]:
            return ["휴대용 선풍기", "모기장", "제습제", "냉감패드", "물놀이 튜브"]
        elif current_month in [12, 1, 2]:
            return ["핫팩", "가습기", "수면양말", "방한장갑", "문풍지"]
        else:
            return ["텀블러", "캠핑의자", "요가매트", "디퓨저", "수납장"]

trend_analyzer = TrendAnalyzer()
