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


class DemoStateResponse(BaseModel):
    tenant_id: str
    input_refs: tuple[ObjectRef, ...]
    events: tuple[dict[str, Any], ...]
    calculations: tuple[CalculationResponse, ...]
    results: tuple[PlanCostResponse, ...]
