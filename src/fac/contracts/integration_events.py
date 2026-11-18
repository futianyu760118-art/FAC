"""P0 cross-system event contracts entering FAC through M02/EDP."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class FacP0EventType(StrEnum):
    INQUIRY_CREATED = "InquiryCreated"
    PRODUCT_CONFIGURATION_CONFIRMED = "ProductConfigurationConfirmed"
    SPECIFICATION_CONFIRMED = "SpecificationConfirmed"
    BOM_RELEASED = "BOMReleased"
    QUOTE_FINANCE_CALCULATED = "QuoteFinanceCalculated"
    FINANCE_GUARD_EVALUATED = "FinanceGuardEvaluated"
    QUOTE_APPROVED_FOR_CUSTOMER = "QuoteApprovedForCustomer"
    SALES_ORDER_CONFIRMED = "SalesOrderConfirmed"


class IntegrationObjectRef(BaseModel):
    object_type: str
    object_id: str
    source_system: str
    revision: int = Field(ge=1)


class IntegrationEvidenceRef(BaseModel):
    evidence_id: str
    kind: str
    source_ref: str
    checksum: str
    created_at: datetime


class FacIntegrationEventRequest(BaseModel):
    tenant_id: str
    ingress_system: str = "M02"
    event_id: str
    event_type: FacP0EventType
    version: int = Field(default=1, ge=1)
    object_ref: IntegrationObjectRef
    occurred_at: datetime
    actor_id: str
    correlation_id: str
    causation_id: str
    trace_id: str
    payload_version: int = Field(default=1, ge=1)
    payload: dict[str, Any]
    evidence_refs: list[IntegrationEvidenceRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_ingress_and_evidence(self) -> "FacIntegrationEventRequest":
        if self.ingress_system != "M02":
            raise ValueError("FAC cross-system events must enter through M02/EDP")
        if self.event_type in {
            FacP0EventType.QUOTE_FINANCE_CALCULATED,
            FacP0EventType.FINANCE_GUARD_EVALUATED,
        } and not self.evidence_refs:
            raise ValueError("formal finance result events require evidence")
        return self
