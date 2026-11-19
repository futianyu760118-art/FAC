"""Formal FAC product contracts for finance governance and calculations."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from fac.contracts.common import ObjectRef

FinanceRuleStatus = Literal["DRAFT", "ACTIVE", "RETIRED"]
FinancePeriodStatus = Literal[
    "OPEN", "CALCULATED", "REVIEWED", "VERIFIED", "CLOSED", "REOPENED", "RESTATED"
]
ExternalRequestStatus = Literal[
    "PENDING", "WAITING_EXTERNAL", "DELIVERED", "FAILED", "RECONCILED"
]


class FacCalculationRequest(BaseModel):
    """Request for a versioned calculation over frozen EDP references."""

    tenant_id: str = Field(min_length=1)
    order_id: str = Field(min_length=1)
    period_id: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    input_refs: tuple[ObjectRef, ...] = Field(min_length=1)
    actor: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)


class FinanceRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    rule_id: str
    version: str
    rule_name: str
    status: FinanceRuleStatus
    effective_from: date
    effective_to: date | None = None
    owner: str
    approval_status: str
    source_fields: tuple[str, ...] = ()
    evidence_required: bool


class FinancePeriodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    period_id: str
    functional_currency: str
    status: FinancePeriodStatus
    closed_at: datetime | None = None


class ExternalRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    request_id: str
    correlation_id: str
    target_system: str
    request_type: str
    idempotency_key: str
    status: ExternalRequestStatus
    attempts: int
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
