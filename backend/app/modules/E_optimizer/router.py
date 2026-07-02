"""
모듈 E — 최적화 루프 API 라우터
"""
from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.database import get_db
from app.modules.E_optimizer.optimizer import run_optimization_loop, auto_apply_price_adjustments
from app.modules.E_optimizer.notifier import (
    notify_delist_candidates,
    notify_price_adjustments,
    notify_daily_report,
)
from app.modules.D_monitoring.metrics import get_dashboard_summary

router = APIRouter(prefix="/api/optimizer", tags=["E. 최적화 루프"])


@router.post("/run")
async def run_optimizer(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    최적화 루프 수동 실행
    (스케줄러가 매일 자동 실행하지만 수동 트리거도 가능)
    """
    results = await run_optimization_loop(db)

    # Slack 알림
    if results["delist_tagged"]:
        await notify_delist_candidates(results["delist_tagged"])
    if results["price_adjust_tagged"]:
        await notify_price_adjustments(results["price_adjust_tagged"])

    return results


@router.post("/auto-price-adjust")
async def auto_price_adjust(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    가격 조정 자동 적용 (승인 없이 바로 쿠팡에 반영)
    주의: 이 기능은 신중하게 사용하세요
    """
    result = await auto_apply_price_adjustments(db)
    return result


@router.post("/daily-report")
async def send_daily_report(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """일일 성과 리포트 발송 (수동 트리거)"""
    summary = await get_dashboard_summary(db)
    await notify_daily_report(summary)
    return {"sent": True, "summary": summary}
