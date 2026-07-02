"""
APScheduler — 자동 실행 작업 등록
"""
from __future__ import annotations
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


def setup_scheduler():
    """스케줄 등록"""
    from app.database import AsyncSessionLocal

    # ── 매일 오전 6시: 전일 주문 수집 ─────────────────────────────────
    @scheduler.scheduled_job(CronTrigger(hour=6, minute=0))
    async def collect_daily_orders():
        logger.info("[스케줄러] 전일 주문 수집 시작")
        async with AsyncSessionLocal() as db:
            from app.modules.D_monitoring.collector import collect_orders
            result = await collect_orders(db, days_back=2)
            logger.info(f"[스케줄러] 주문 수집 완료: {result}")

    # ── 매일 오전 7시: 최적화 루프 실행 ───────────────────────────────
    @scheduler.scheduled_job(CronTrigger(hour=7, minute=0))
    async def run_daily_optimization():
        logger.info("[스케줄러] 최적화 루프 시작")
        async with AsyncSessionLocal() as db:
            from app.modules.E_optimizer.optimizer import run_optimization_loop
            from app.modules.E_optimizer.notifier import notify_delist_candidates, notify_price_adjustments
            results = await run_optimization_loop(db)
            if results["delist_tagged"]:
                await notify_delist_candidates(results["delist_tagged"])
            if results["price_adjust_tagged"]:
                await notify_price_adjustments(results["price_adjust_tagged"])
            logger.info(f"[스케줄러] 최적화 완료: {results}")

    # ── 매주 월요일 오전 8시: 주간 리포트 Slack 발송 ──────────────────
    @scheduler.scheduled_job(CronTrigger(day_of_week="mon", hour=8, minute=0))
    async def weekly_report():
        logger.info("[스케줄러] 주간 리포트 발송")
        async with AsyncSessionLocal() as db:
            from app.modules.D_monitoring.metrics import get_dashboard_summary
            from app.modules.E_optimizer.notifier import notify_daily_report
            summary = await get_dashboard_summary(db)
            await notify_daily_report(summary)

    logger.info("[스케줄러] 모든 작업 등록 완료")
    return scheduler
