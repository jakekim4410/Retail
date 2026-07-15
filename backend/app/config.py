"""
앱 설정 — 환경변수 로드 (pydantic-settings)
실제 데이터 전용 — Mock 모드 없음
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # 오너클랜
    ownerclan_username: str = Field(default="", alias="OWNERCLAN_USERNAME")
    ownerclan_password: str = Field(default="", alias="OWNERCLAN_PASSWORD")
    ownerclan_base_url: str = Field(default="https://api.ownerclan.com", alias="OWNERCLAN_BASE_URL")

    # 쿠팡
    coupang_access_key: str = Field(default="", alias="COUPANG_ACCESS_KEY")
    coupang_secret_key: str = Field(default="", alias="COUPANG_SECRET_KEY")
    coupang_vendor_id: str = Field(default="", alias="COUPANG_VENDOR_ID")
    coupang_base_url: str = Field(default="https://api-gateway.coupang.com", alias="COUPANG_BASE_URL")

    # Gemini (Google)
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    # Slack
    slack_webhook_url: str = Field(default="", alias="SLACK_WEBHOOK_URL")

    # Naver DataLab API
    naver_client_id: str = Field(default="", alias="NAVER_CLIENT_ID")
    naver_client_secret: str = Field(default="", alias="NAVER_CLIENT_SECRET")

    # DB
    database_url: str = Field(
        default="sqlite+aiosqlite:///./sales_automation.db",
        alias="DATABASE_URL",
    )

    # 시스템
    margin_threshold_percent: float = Field(default=10.0, alias="MARGIN_THRESHOLD_PERCENT")
    poor_sales_days: int = Field(default=14, alias="POOR_SALES_DAYS")
    port: int = Field(default=8000, alias="PORT")
    app_env: str = Field(default="development", alias="APP_ENV")

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
