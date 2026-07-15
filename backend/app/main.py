"""
FastAPI 앱 진입점 — 위탁판매 통합 자동화 시스템
"""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.scheduler import setup_scheduler
from app.modules.A_sourcing.router import router as sourcing_router
from app.modules.B_detail_page.router import router as detail_page_router
from app.modules.C_registration.router import router as registration_router
from app.modules.D_monitoring.router import router as monitoring_router
from app.modules.E_optimizer.router import router as optimizer_router
from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작
    logger.info("🚀 위탁판매 자동화 시스템 시작 (실제 데이터 모드)")
    logger.info(f"   마진율 기준: {settings.margin_threshold_percent}%")
    await init_db()
    scheduler = setup_scheduler()
    scheduler.start()
    yield
    # 종료
    scheduler.shutdown()
    logger.info("👋 서버 종료")


app = FastAPI(
    title="위탁판매 통합 자동화 시스템",
    description="""
## 소싱 → 마진검증 → 상품등록 → 판매모니터링 → 최적화

| 모듈 | 기능 |
|---|---|
| A | 오너클랜 소싱·마진 검증 |
| B | 상세페이지 자동 생성 (LLM + HTML 템플릿) |
| C | 쿠팡 Open API 상품 등록 (반자동 승인 흐름) |
| D | 판매 성과 모니터링 |
| E | 최적화 루프 (자동 하차·가격조정) |
    """,
    version="2.0.0",
    lifespan=lifespan,
)

# CORS (React 개발 서버 및 Vercel 배포 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000", 
        "http://127.0.0.1:5173",
        "https://retail-xi-vert.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록

import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    err = traceback.format_exc()
    print('GLOBAL EXCEPTION:', err)
    return JSONResponse(status_code=500, content={'detail': 'Internal Server Error', 'traceback': err})

app.include_router(sourcing_router)
app.include_router(detail_page_router)
app.include_router(registration_router)
app.include_router(monitoring_router)
app.include_router(optimizer_router)


@app.get("/", tags=["상태"])
async def root():
    return {
        "service": "위탁판매 통합 자동화 시스템",
        "version": "2.0.0",
        "mode": "live",
        "modules": ["A.소싱", "B.상세페이지", "C.등록", "D.모니터링", "E.최적화"],
        "docs": "/docs",
    }


@app.get("/health", tags=["상태"])
async def health():
    return {"status": "ok"}


@app.get("/api/settings/status", tags=["설정"])
async def settings_status():
    """API 키 연동 현황 조회 (값 노출 없이 설정 여부만 반환)"""
    return {
        "mode": "live",
        "ownerclan": {
            "configured": bool(settings.ownerclan_username and settings.ownerclan_password),
        },
        "coupang": {
            "configured": bool(settings.coupang_access_key and settings.coupang_secret_key and settings.coupang_vendor_id),
            "vendor_id": settings.coupang_vendor_id or None,
        },
        "gemini": {
            "configured": bool(settings.gemini_api_key),
            "model": settings.gemini_model,
        },
        "slack": {
            "configured": bool(settings.slack_webhook_url),
        },
        "naver": {
            "configured": bool(settings.naver_client_id and settings.naver_client_secret),
        },
        "policy": {
            "margin_threshold_percent": settings.margin_threshold_percent,
            "poor_sales_days": settings.poor_sales_days,
        }
    }
