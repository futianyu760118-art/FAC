"""M01 Guard action vocabulary owned by FAC P0."""

from enum import StrEnum

from pydantic import BaseModel


class FinanceGuardAction(StrEnum):
    TASK_EXECUTE = "TASK_EXECUTE"
    PAYMENT_EXECUTE = "PAYMENT_EXECUTE"
    DATA_EXPORT = "DATA_EXPORT"


ACTION_RESOURCE_MAP: dict[FinanceGuardAction, tuple[str, str]] = {
    FinanceGuardAction.TASK_EXECUTE: ("task", "execute"),
    FinanceGuardAction.PAYMENT_EXECUTE: ("payment", "execute"),
    FinanceGuardAction.DATA_EXPORT: ("data", "export"),
}


class M01Approval(BaseModel):
    approval_id: str
    tenant_id: str
    requester_id: str
    resource: str
    action: str
    object_id: str
    parameters_hash: str
    status: str
    created_at: str
    decided_at: str | None = None
    decided_by: str | None = None
    comment: str | None = None
    consumed_at: str | None = None


class M01GuardResult(BaseModel):
    agent_id: str
    m01_agent_id: str
    tenant_id: str
    action_type: FinanceGuardAction
    resource: str
    action: str
    object_id: str
    decision: str
    reason: str
    trace_id: str
    approval: M01Approval | None = None
    execution_allowed: bool
    requires_human_approval: bool
    guard_source: str = "M01"
