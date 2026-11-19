"""Transport contracts for versioned calculation and OFA plan cost."""

from decimal import Decimal

from pydantic import BaseModel

from fac.contracts.common import ObjectRef
from fac.domain.money import Money
from fac.modules.calculation.service import CalculationContext
from fac.modules.ofa.models import PlanCostResult


class MoneyValue(BaseModel):
    original_amount: Decimal
    original_currency: str
    functional_amount: Decimal
    functional_currency: str
    fx_rate: Decimal

    @classmethod
    def from_money(cls, money: Money | None) -> "MoneyValue | None":
        if money is None:
            return None
        return cls(
            original_amount=money.original_amount,
            original_currency=money.original_currency,
            functional_amount=money.to_functional(),
            functional_currency=money.functional_currency,
            fx_rate=money.fx_rate,
        )


class CalculationResponse(BaseModel):
    calculation_id: str
    snapshot_id: str
    tenant_id: str
    subject_type: str
    subject_id: str
    version: int
    rule_set_version: str
    checksum: str
    input_refs: tuple[ObjectRef, ...]
    trigger_type: str
    reason: str
    actor: str

    @classmethod
    def from_context(cls, context: CalculationContext) -> "CalculationResponse":
        return cls(
            calculation_id=context.calculation_id,
            snapshot_id=context.snapshot_id,
            tenant_id=context.tenant_id,
            subject_type=context.subject_type,
            subject_id=context.subject_id,
            version=context.version,
            rule_set_version=context.rule_set_version,
            checksum=context.checksum,
            input_refs=context.input_refs,
            trigger_type=context.trigger_type,
            reason=context.reason,
            actor=context.actor,
        )


class CostIssue(BaseModel):
    code: str
    object_id: str


class FxUsageResponse(BaseModel):
    cost_component: str
    object_id: str
    original_amount: Decimal
    base_currency: str
    quote_currency: str
    rate: Decimal
    rate_type: str
    effective_at: str
    source: str
    revision: int
    evidence_ref: str


class PlanCostResponse(BaseModel):
    result_id: str
    version: int
    calculation_id: str
    snapshot_id: str
    rule_set_version: str
    status: str
    cost_type: str
    material_cost: MoneyValue | None
    labor_cost: MoneyValue | None
    expense_cost: MoneyValue | None
    processing_cost: MoneyValue | None
    total_cost: MoneyValue | None
    errors: tuple[CostIssue, ...]
    evidence_refs: tuple[str, ...]
    fx_usages: tuple[FxUsageResponse, ...]
    previous_result_id: str | None

    @classmethod
    def from_result(cls, result: PlanCostResult) -> "PlanCostResponse":
        return cls(
            result_id=result.result_id,
            version=result.version,
            calculation_id=result.calculation_id,
            snapshot_id=result.snapshot_id,
            rule_set_version=result.rule_set_version,
            status=result.status,
            cost_type=result.cost_type,
            material_cost=MoneyValue.from_money(result.material_cost),
            labor_cost=MoneyValue.from_money(result.labor_cost),
            expense_cost=MoneyValue.from_money(result.expense_cost),
            processing_cost=MoneyValue.from_money(result.processing_cost),
            total_cost=MoneyValue.from_money(result.total_cost),
            errors=tuple(
                CostIssue(code=item.code, object_id=item.object_id) for item in result.errors
            ),
            evidence_refs=tuple(item.evidence_id for item in result.evidence_refs),
            fx_usages=tuple(
                FxUsageResponse(
                    cost_component=item.cost_component,
                    object_id=item.object_id,
                    original_amount=item.original_amount,
                    base_currency=item.rate.base_currency,
                    quote_currency=item.rate.quote_currency,
                    rate=item.rate.rate,
                    rate_type=item.rate.rate_type,
                    effective_at=item.rate.effective_at.isoformat(),
                    source=item.rate.source,
                    revision=item.rate.revision,
                    evidence_ref=item.rate.evidence_ref,
                )
                for item in result.fx_usages
            ),
            previous_result_id=result.previous_result_id,
        )
