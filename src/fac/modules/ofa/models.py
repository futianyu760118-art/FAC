"""Typed, Decimal-only inputs and plan-cost output."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from fac.contracts.common import EvidenceRef, FXRate, ObjectRef
from fac.domain.money import Money


@dataclass(frozen=True)
class MoneyInput:
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class OrderInput:
    order_id: str
    product_id: str
    quantity: Decimal
    order_date: date
    functional_currency: str
    ref: ObjectRef


@dataclass(frozen=True)
class BOMLineInput:
    component_id: str
    quantity: Decimal
    uom: str
    kind: str = "MATERIAL"
    conversion_factor: Decimal = Decimal(1)
    processing_price: MoneyInput | None = None
    price_uom: str | None = None


@dataclass(frozen=True)
class BOMInput:
    product_id: str
    lines: tuple[BOMLineInput, ...]


@dataclass(frozen=True)
class MaterialPriceInput:
    material_id: str
    unit_price: MoneyInput
    uom: str
    effective_at: date
    ref: ObjectRef
    override: bool = False
    fallback: bool = False


@dataclass(frozen=True)
class LaborInput:
    product_id: str
    hours_per_unit: Decimal
    hourly_rate: MoneyInput


@dataclass(frozen=True)
class ExpenseInput:
    product_id: str
    expense_per_unit: MoneyInput


@dataclass(frozen=True)
class CostError:
    code: str
    object_id: str


@dataclass(frozen=True)
class CostLine:
    component_id: str
    quantity: Decimal
    uom: str
    money: Money
    price_ref: ObjectRef | None


@dataclass(frozen=True)
class FxUsage:
    cost_component: str
    object_id: str
    original_amount: Decimal
    rate: FXRate


@dataclass(frozen=True)
class PlanCostResult:
    result_id: str
    version: int
    calculation_id: str
    snapshot_id: str
    rule_set_version: str
    status: str
    material_cost: Money | None
    labor_cost: Money | None
    expense_cost: Money | None
    processing_cost: Money | None
    total_cost: Money | None
    material_lines: tuple[CostLine, ...] = ()
    errors: tuple[CostError, ...] = ()
    evidence_refs: tuple[EvidenceRef, ...] = ()
    previous_result_id: str | None = None
    cost_type: str = "PLAN"
    fx_usages: tuple[FxUsage, ...] = ()
