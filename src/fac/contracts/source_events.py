"""Source-native M05 CRM and M04 PLM event contracts delivered by M02."""

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator


class M02IngressMixin(BaseModel):
    tenant_id: str
    ingress_system: Literal["M02"] = "M02"


class CrmAeosEventV1(BaseModel):
    contract_version: Literal["AEOS.Event.V1"]
    event_id: str
    event_type: str
    source_system: str
    object_type: str
    object_id: str
    operation: Literal["UPSERT", "DELETE"]
    occurred_at: datetime
    trace_id: str
    payload: dict[str, Any]
    idempotency_key: str | None = None


class M02CrmEventRequest(M02IngressMixin):
    event: CrmAeosEventV1


class PlmEventV1(BaseModel):
    event_type: str = Field(alias="eventType")
    object_type: str = Field(alias="objectType")
    object_id: str = Field(alias="objectId")
    occurred_at: datetime = Field(alias="occurredAt")
    source_system: str | None = Field(default=None, alias="sourceSystem")
    correlation_id: str | None = Field(default=None, alias="correlationId")
    version: int | None = None
    evidence_refs: list[str] = Field(default_factory=list, alias="evidenceRefs")
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def normalize_version(self) -> Self:
        if self.version is not None and self.version < 0:
            raise ValueError("PLM event version must be >= 0")
        return self


class M02PlmEventRequest(M02IngressMixin):
    event_id: str
    event: PlmEventV1
