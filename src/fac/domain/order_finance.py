"""Five-stage order finance model and deterministic variance analysis."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


MONEY_Q = Decimal("0.01")
RATE_Q = Decimal("0.0001")
ROUNDING = "ROUND_HALF_UP"


class OrderFinanceStage(StrEnum):
    QUOTE = "QUOTE"
    PLAN = "PLAN"
    FORECAST = "FORECAST"
    FINAL = "FINAL"


class OrderCostComponents(BaseModel):
    material: Decimal = Field(ge=0)
    labor: Decimal = Field(ge=0)
    processing: Decimal = Field(ge=0)
    packaging: Decimal = Field(ge=0)
    logistics: Decimal = Field(ge=0)
    quality: Decimal = Field(ge=0)
    aftersales: Decimal = Field(ge=0)
    fx: Decimal = Field(ge=0)
    other: Decimal = Field(default=Decimal(0), ge=0)

    def total(self) -> Decimal:
        return sum(self.model_dump().values(), Decimal(0))


class OrderFinanceSnapshotInput(BaseModel):
    order_id: str
    stage: OrderFinanceStage
    revenue_cny: Decimal = Field(gt=0)
    components: OrderCostComponents
    revision: int = Field(ge=1)


class OrderFinanceSnapshotResult(BaseModel):
    order_id: str
    stage: OrderFinanceStage
    revision: int
    revenue_cny: Decimal
    total_cost_cny: Decimal
    gross_profit_cny: Decimal
    gross_margin_rate: Decimal
    calculation_method: str = "DETERMINISTIC"


class CostVariance(BaseModel):
    component: str
    baseline_cny: Decimal
    current_cny: Decimal
    variance_cny: Decimal


class OrderFinanceCompareInput(BaseModel):
    baseline: OrderFinanceSnapshotInput
    current: OrderFinanceSnapshotInput

    @model_validator(mode="after")
    def validate_order(self) -> OrderFinanceCompareInput:
        if self.baseline.order_id != self.current.order_id:
            raise ValueError("baseline and current must refer to the same order")
        return self


class OrderFinanceCompareResult(BaseModel):
    order_id: str
    baseline_stage: OrderFinanceStage
    current_stage: OrderFinanceStage
    total_cost_variance_cny: Decimal
    gross_margin_variance_rate: Decimal
    component_variances: list[CostVariance]
    calculation_method: str = "DETERMINISTIC"


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_Q, rounding=ROUNDING)


def _rate(value: Decimal) -> Decimal:
    return value.quantize(RATE_Q, rounding=ROUNDING)


def calculate_snapshot(payload: OrderFinanceSnapshotInput) -> OrderFinanceSnapshotResult:
    total_cost = payload.components.total()
    gross_profit = payload.revenue_cny - total_cost
    gross_margin = gross_profit / payload.revenue_cny
    return OrderFinanceSnapshotResult(
        order_id=payload.order_id,
        stage=payload.stage,
        revision=payload.revision,
        revenue_cny=_money(payload.revenue_cny),
        total_cost_cny=_money(total_cost),
        gross_profit_cny=_money(gross_profit),
        gross_margin_rate=_rate(gross_margin),
    )


def compare_order_finance(payload: OrderFinanceCompareInput) -> OrderFinanceCompareResult:
    baseline = calculate_snapshot(payload.baseline)
    current = calculate_snapshot(payload.current)
    variances: list[CostVariance] = []
    for component in payload.baseline.components.model_fields:
        base_value = getattr(payload.baseline.components, component)
        current_value = getattr(payload.current.components, component)
        variances.append(
            CostVariance(
                component=component,
                baseline_cny=_money(base_value),
                current_cny=_money(current_value),
                variance_cny=_money(current_value - base_value),
            )
        )
    return OrderFinanceCompareResult(
        order_id=payload.baseline.order_id,
        baseline_stage=payload.baseline.stage,
        current_stage=payload.current.stage,
        total_cost_variance_cny=_money(current.total_cost_cny - baseline.total_cost_cny),
        gross_margin_variance_rate=_rate(
            current.gross_margin_rate - baseline.gross_margin_rate
        ),
        component_variances=variances,
    )
