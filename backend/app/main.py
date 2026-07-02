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
    logger.info("🚀 위탁판매 자동화 시스템 시작")
    logger.info(f"   Mock 모드: {settings.mock_mode}")
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

# CORS (React 개발 서버 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
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
        "mock_mode": settings.mock_mode,
        "modules": ["A.소싱", "B.상세페이지", "C.등록", "D.모니터링", "E.최적화"],
        "docs": "/docs",
    }


@app.get("/health", tags=["상태"])
async def health():
    return {"status": "ok"}
