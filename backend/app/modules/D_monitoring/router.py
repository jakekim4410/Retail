"""
모듈 D — 판매 성과 모니터링 API 라우터
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.database import get_db
from app.modules.D_monitoring.collector import collect_orders
from app.modules.D_monitoring.metrics import (
    get_dashboard_summary,
    get_product_performance_list,
    get_daily_sales_trend,
)

router = APIRouter(prefix="/api/monitoring", tags=["D. 판매 성과 모니터링"])


@router.post("/collect")
async def trigger_collection(
    days_back: int = Query(1, ge=1, le=90, description="수집할 과거 일수"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """주문 데이터 수동 수집 (스케줄러가 자동 실행하지만 수동 트리거도 가능)"""
    result = await collect_orders(db, days_back=days_back)
    return result


@router.get("/dashboard")
async def dashboard_summary(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """대시보드 핵심 KPI"""
    return await get_dashboard_summary(db)


@router.get("/products")
async def product_performance(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    """상품별 판매 성과 목록"""
    return await get_product_performance_list(db)


@router.get("/trend")
async def daily_trend(
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """일별 매출 트렌드"""
    return await get_daily_sales_trend(db, days=days)
