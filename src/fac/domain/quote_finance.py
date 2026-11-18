"""Quote-finance domain contracts and deterministic calculations."""

from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


MONEY_Q = Decimal("0.01")
RATE_Q = Decimal("0.0001")
ROUNDING = "ROUND_HALF_UP"


class SourceKind(StrEnum):
    AUTO = "AUTO"
    CALCULATED = "CALCULATED"
    RECOMMENDED = "RECOMMENDED"
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    ESCALATE = "ESCALATE"


class QuoteFinanceInput(BaseModel):
    inquiry_id: str
    quote_version: str = "V1"
    customer_id: str
    product_id: str
    configuration_id: str
    specification_id: str
    bom_id: str

    quantity: Decimal = Field(gt=0)
    unit_price_original: Decimal = Field(gt=0)
    currency: str = "USD"
    fx_rate_to_cny: Decimal = Field(gt=0)

    material_cost_cny: Decimal = Field(ge=0)
    labor_cost_cny: Decimal = Field(ge=0)
    processing_cost_cny: Decimal = Field(ge=0)
    packaging_cost_cny: Decimal = Field(ge=0)
    logistics_cost_cny: Decimal = Field(ge=0)
    quality_reserve_cny: Decimal = Field(ge=0)
    aftersales_reserve_cny: Decimal = Field(ge=0)
    fx_reserve_cny: Decimal = Field(ge=0)

    payment_days: int = Field(default=60, ge=0, le=365)
    floor_margin_rate: Decimal = Field(default=Decimal("0.15"), ge=0, lt=1)
    target_margin_rate: Decimal = Field(default=Decimal("0.25"), ge=0, lt=1)
    recommended_margin_rate: Decimal = Field(default=Decimal("0.28"), ge=0, lt=1)

    @model_validator(mode="after")
    def validate_margin_order(self) -> Self:
        if not (
            self.floor_margin_rate
            <= self.target_margin_rate
            <= self.recommended_margin_rate
        ):
            raise ValueError("margin thresholds must satisfy floor <= target <= recommended")
        return self


class QuoteFinanceResult(BaseModel):
    inquiry_id: str
    quote_version: str
    revenue_cny: Decimal
    total_cost_cny: Decimal
    gross_profit_cny: Decimal
    gross_margin_rate: Decimal
    floor_unit_price_original: Decimal
    target_unit_price_original: Decimal
    recommended_unit_price_original: Decimal
    risk_level: RiskLevel
    guard_message: str
    rule_id: str = "FAC-QUOTE-PRICE-001"
    rule_version: str = "1.0"
    calculation_method: str = "DETERMINISTIC"


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_Q, rounding=ROUNDING)


def _rate(value: Decimal) -> Decimal:
    return value.quantize(RATE_Q, rounding=ROUNDING)


def _unit_price_for_margin(
    total_cost_cny: Decimal,
    quantity: Decimal,
    fx_rate_to_cny: Decimal,
    margin_rate: Decimal,
) -> Decimal:
    denominator = quantity * fx_rate_to_cny * (Decimal(1) - margin_rate)
    return _money(total_cost_cny / denominator)


def calculate_quote_finance(payload: QuoteFinanceInput) -> QuoteFinanceResult:
    """Compute quote finance deterministically; no LLM arithmetic is permitted."""
    total_cost = sum(
        (
            payload.material_cost_cny,
            payload.labor_cost_cny,
            payload.processing_cost_cny,
            payload.packaging_cost_cny,
            payload.logistics_cost_cny,
            payload.quality_reserve_cny,
            payload.aftersales_reserve_cny,
            payload.fx_reserve_cny,
        ),
        Decimal(0),
    )
    revenue = payload.quantity * payload.unit_price_original * payload.fx_rate_to_cny
    gross_profit = revenue - total_cost
    gross_margin = gross_profit / revenue if revenue else Decimal(0)

    if gross_margin < payload.floor_margin_rate:
        risk = RiskLevel.ESCALATE
        message = "低于财务底线，必须升级审批"
    elif gross_margin < payload.target_margin_rate:
        risk = RiskLevel.HIGH
        message = "低于目标毛利，需财务与业务联合评审"
    elif payload.payment_days > 90:
        risk = RiskLevel.MEDIUM
        message = "毛利达标，但账期导致资金占用风险"
    else:
        risk = RiskLevel.LOW
        message = "通过财务门禁"

    return QuoteFinanceResult(
        inquiry_id=payload.inquiry_id,
        quote_version=payload.quote_version,
        revenue_cny=_money(revenue),
        total_cost_cny=_money(total_cost),
        gross_profit_cny=_money(gross_profit),
        gross_margin_rate=_rate(gross_margin),
        floor_unit_price_original=_unit_price_for_margin(
            total_cost, payload.quantity, payload.fx_rate_to_cny, payload.floor_margin_rate
        ),
        target_unit_price_original=_unit_price_for_margin(
            total_cost, payload.quantity, payload.fx_rate_to_cny, payload.target_margin_rate
        ),
        recommended_unit_price_original=_unit_price_for_margin(
            total_cost,
            payload.quantity,
            payload.fx_rate_to_cny,
            payload.recommended_margin_rate,
        ),
        risk_level=risk,
        guard_message=message,
    )
