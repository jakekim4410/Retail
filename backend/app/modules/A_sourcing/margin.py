"""
모듈 A — 마진 계산 엔진

공식:
  순마진 = 판매가 - 도매가 - 쿠팡수수료 - VAT - 서비스이용료(일할) - 예상반품비
  순마진율 = 순마진 / 판매가 × 100

쿠팡 수수료율 (카테고리별):
  가전/전자: 6.8% | 주방: 7.0% | 스포츠/레저: 8.0%
  생활용품: 7.5% | 뷰티: 9.0% | 패션: 10.9% | 기본: 7.0%
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

# 카테고리별 쿠팡 수수료율 (source_category_code 기준)
CATEGORY_COMMISSION_RATES: dict[str, float] = {
    "ELEC-AUDIO": 0.068,
    "ELEC-LIGHT": 0.068,
    "ELEC-ETC": 0.068,
    "KITCHEN-CUP": 0.070,
    "KITCHEN-ETC": 0.070,
    "TRAVEL-ACC": 0.075,
    "SPORTS-YOGA": 0.080,
    "SPORTS-ETC": 0.080,
    "CLEAN-CLOTH": 0.075,
    "HOME-DIFFUSER": 0.075,
    "HOME-ETC": 0.075,
    "CAR-ACC": 0.070,
    "BEAUTY": 0.090,
    "FASHION": 0.109,
    "FOOD": 0.040,
}
DEFAULT_COMMISSION_RATE = 0.070

# 반품율 기본값 (카테고리별, 없으면 3%)
CATEGORY_RETURN_RATES: dict[str, float] = {
    "FASHION": 0.15,
    "BEAUTY": 0.05,
    "ELEC-AUDIO": 0.04,
    "ELEC-LIGHT": 0.03,
    "SPORTS-YOGA": 0.04,
}
DEFAULT_RETURN_RATE = 0.03
RETURN_SHIPPING_COST = 5000  # 반품 발생 시 평균 배송비 (원)

# 쿠팡 서비스이용료
MONTHLY_SERVICE_FEE_THRESHOLD = 1_000_000  # 100만원
MONTHLY_SERVICE_FEE = 55_000              # 55,000원/월
DAYS_IN_MONTH = 30


@dataclass
class MarginResult:
    source_id: str
    name: str
    wholesale_price: float
    sale_price: float
    commission_rate: float
    commission_amount: float
    vat_amount: float
    service_fee_daily: float
    estimated_return_cost: float
    net_margin: float
    net_margin_rate: float
    passed: bool                  # 마진율 기준 통과 여부
    source_category_code: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "wholesale_price": round(self.wholesale_price),
            "sale_price": round(self.sale_price),
            "commission_rate_pct": round(self.commission_rate * 100, 2),
            "commission_amount": round(self.commission_amount),
            "vat_amount": round(self.vat_amount),
            "service_fee_daily": round(self.service_fee_daily),
            "estimated_return_cost": round(self.estimated_return_cost),
            "net_margin": round(self.net_margin),
            "net_margin_rate_pct": round(self.net_margin_rate, 2),
            "passed": self.passed,
            "source_category_code": self.source_category_code,
        }


class MarginCalculator:
    """
    마진 계산기
    threshold_pct: 합격 최소 마진율 (%)
    monthly_sales_estimate: 월 예상 매출 (서비스이용료 계산용)
    """

    def __init__(self, threshold_pct: float = 10.0, monthly_sales_estimate: float = 500_000):
        self.threshold_pct = threshold_pct
        self.monthly_sales_estimate = monthly_sales_estimate

    def calculate(
        self,
        source_id: str,
        name: str,
        wholesale_price: float,
        sale_price: float,
        source_category_code: str,
    ) -> MarginResult:
        # 수수료율
        commission_rate = CATEGORY_COMMISSION_RATES.get(
            source_category_code, DEFAULT_COMMISSION_RATE
        )
        commission_amount = sale_price * commission_rate

        # VAT (공급가액 기준 10%)
        # 쿠팡 정산 기준: 판매가에서 수수료 제외한 금액에서 VAT 계산
        supply_amount = sale_price - commission_amount
        vat_amount = supply_amount * 10 / 110  # 부가세 역산

        # 서비스이용료 일할 계산
        daily_service_fee = 0.0
        if self.monthly_sales_estimate > MONTHLY_SERVICE_FEE_THRESHOLD:
            daily_service_fee = MONTHLY_SERVICE_FEE / DAYS_IN_MONTH

        # 예상 반품비
        return_rate = CATEGORY_RETURN_RATES.get(source_category_code, DEFAULT_RETURN_RATE)
        estimated_return_cost = sale_price * return_rate * RETURN_SHIPPING_COST / sale_price
        # 더 정확히: 반품건당 배송비 × 반품율
        estimated_return_cost = return_rate * RETURN_SHIPPING_COST

        # 순마진
        net_margin = (
            sale_price
            - wholesale_price
            - commission_amount
            - vat_amount
            - daily_service_fee
            - estimated_return_cost
        )
        net_margin_rate = (net_margin / sale_price * 100) if sale_price > 0 else 0.0

        return MarginResult(
            source_id=source_id,
            name=name,
            wholesale_price=wholesale_price,
            sale_price=sale_price,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            vat_amount=vat_amount,
            service_fee_daily=daily_service_fee,
            estimated_return_cost=estimated_return_cost,
            net_margin=net_margin,
            net_margin_rate=net_margin_rate,
            passed=(net_margin_rate >= self.threshold_pct),
            source_category_code=source_category_code,
        )

    def suggest_sale_price(
        self,
        wholesale_price: float,
        source_category_code: str,
        target_margin_pct: Optional[float] = None,
    ) -> float:
        """목표 마진율 달성을 위한 최소 판매가 역산"""
        target = target_margin_pct if target_margin_pct is not None else self.threshold_pct
        commission_rate = CATEGORY_COMMISSION_RATES.get(
            source_category_code, DEFAULT_COMMISSION_RATE
        )
        return_rate = CATEGORY_RETURN_RATES.get(source_category_code, DEFAULT_RETURN_RATE)
        # 연립방정식 근사 풀이 (반복)
        for markup in range(110, 300):
            sp = wholesale_price * markup / 100
            result = self.calculate("", "", wholesale_price, sp, source_category_code)
            if result.net_margin_rate >= target:
                return round(sp / 100) * 100  # 100원 단위 올림
        return round(wholesale_price * 2 / 100) * 100


calculator = MarginCalculator()
