"""
모듈 E — Slack/로그 알림 발송
Slack Webhook URL이 없으면 콘솔 로그로 대체
"""
from __future__ import annotations
import json
import logging
from typing import Any
import httpx

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def send_slack(message: str, blocks: Optional[list] = None) -> bool:
    """Slack Webhook으로 메시지 발송"""
    if not settings.slack_webhook_url:
        logger.info(f"[SLACK 시뮬레이션] {message}")
        return True

    payload: dict[str, Any] = {"text": message}
    if blocks:
        payload["blocks"] = blocks

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.slack_webhook_url,
                json=payload,
                timeout=10.0,
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"[Slack 발송 실패] {e}")
        return False


async def notify_delist_candidates(products: list[dict[str, Any]]) -> None:
    """하차 후보 상품 알림"""
    if not products:
        return

    lines = [f"• [{p['source_id']}] {p['name']} — {p['reason']}" for p in products[:10]]
    message = (
        f"🚨 *하차 후보 상품 {len(products)}건*\n"
        + "\n".join(lines)
        + (f"\n... 외 {len(products) - 10}건" if len(products) > 10 else "")
    )
    await send_slack(message)


async def notify_price_adjustments(products: list[dict[str, Any]]) -> None:
    """가격 조정 필요 상품 알림"""
    if not products:
        return

    lines = [
        f"• [{p['source_id']}] {p['name']} — 현재 {int(p['current_price']):,}원 → 권장 {int(p['suggested_price']):,}원 ({p['reason']})"
        for p in products[:10]
    ]
    message = (
        f"💰 *가격 조정 필요 상품 {len(products)}건*\n"
        + "\n".join(lines)
        + (f"\n... 외 {len(products) - 10}건" if len(products) > 10 else "")
    )
    await send_slack(message)


async def notify_daily_report(summary: dict[str, Any]) -> None:
    """일일 성과 리포트 알림"""
    message = (
        f"📊 *일일 성과 리포트*\n"
        f"• 월 매출: {int(summary.get('monthly_revenue', 0)):,}원\n"
        f"• 월 순이익: {int(summary.get('monthly_net_profit', 0)):,}원\n"
        f"• 월 주문수: {summary.get('monthly_orders', 0)}건\n"
        f"• 순마진율: {summary.get('net_margin_rate', 0)}%\n"
        f"• 하차 후보: {summary.get('delist_candidate_count', 0)}건\n"
        f"• 가격 조정 필요: {summary.get('price_adjust_count', 0)}건"
    )
    await send_slack(message)
