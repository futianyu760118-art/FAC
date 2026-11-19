"""Contracts used by the local FAC browser demo."""

from typing import Any

from pydantic import BaseModel, Field

from fac.contracts.common import ObjectRef
from fac.contracts.ofa import CalculationResponse, PlanCostResponse


class DemoTriggerRequest(BaseModel):
    order_id: str = Field(min_length=1)
    price_revision: int = Field(ge=1)
    event_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    trigger_type: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    actor: str = Field(min_length=1)


class DemoResetResponse(BaseModel):
    tenant_id: str
    seeded_refs: tuple[ObjectRef, ...]


class DemoTriggerResponse(BaseModel):
    replayed: bool
    event_id: str
    calculation: CalculationResponse
    result: PlanCostResponse


class DemoStageState(BaseModel):
    module: str
    name: str
    status: str
    status_label: str
    mode: str
    input_refs: tuple[str, ...] = ()
    output_refs: tuple[str, ...] = ()


class DemoAgentState(BaseModel):
    agent_id: str
    name: str
    capabilities: tuple[str, ...]
    action_level: str
    dispatchable: bool
    status: str
    source: str


class DemoDecisionCaseState(BaseModel):
    case_id: str
    title: str
    risk_level: str
    decision: str
    status: str
    maker: str
    checker: str
    approver: str
    accountable_owner: str
    result_id: str | None = None


class DemoActionState(BaseModel):
    action_id: str
    title: str
    status: str
    owner: str
    due_date: str
    decision_case_id: str
    feedback: str
    evidence_ref: str | None = None


class DemoVerifyState(BaseModel):
    status: str
    status_label: str
    evidence_coverage: int
    result_id: str | None = None
    roi_value: str
    value_ledger_id: str
    evidence_refs: tuple[str, ...]


class DemoIntegrationState(BaseModel):
    correlation_id: str
    idempotency_enabled: bool
    mode: str
    stages: tuple[DemoStageState, ...]
    agents: tuple[DemoAgentState, ...]
    decision_cases: tuple[DemoDecisionCaseState, ...]
    actions: tuple[DemoActionState, ...]
    verify: DemoVerifyState
    ebms_status: str
    event_ledger: tuple[dict[str, Any], ...]

    def stage(self, module: str) -> DemoStageState:
        return next(stage for stage in self.stages if stage.module == module)


class DemoStateResponse(BaseModel):
    tenant_id: str
    input_refs: tuple[ObjectRef, ...]
    events: tuple[dict[str, Any], ...]
    calculations: tuple[CalculationResponse, ...]
    results: tuple[PlanCostResponse | None, ...]
    integration: DemoIntegrationState | None = None
