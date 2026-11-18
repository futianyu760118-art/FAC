"""EDP-only cross-system integration endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fac.contracts.common import EvidenceRef, ObjectRef
from fac.contracts.events import EventEnvelope
from fac.contracts.integration_events import FacIntegrationEventRequest
from fac.domain.events import deterministic_idempotency_key
from fac.infrastructure.db import get_session
from fac.infrastructure.repositories import CoreRepository

router = APIRouter(prefix="/api/v1/fac/integration", tags=["FAC Integration"])


class EventIngestResponse(BaseModel):
    event_id: str
    event_type: str
    created: bool
    idempotency_key: str


@router.post("/edp-events", response_model=EventIngestResponse)
def ingest_edp_event(
    payload: FacIntegrationEventRequest,
    session: Annotated[Session, Depends(get_session)],
) -> EventIngestResponse:
    object_ref = ObjectRef(
        object_type=payload.object_ref.object_type,
        object_id=payload.object_ref.object_id,
        source_system=payload.object_ref.source_system,
        revision=payload.object_ref.revision,
    )
    evidence_refs = [
        EvidenceRef(
            evidence_id=item.evidence_id,
            kind=item.kind,
            source_ref=item.source_ref,
            checksum=item.checksum,
            created_at=item.created_at,
        )
        for item in payload.evidence_refs
    ]

    try:
        idempotency_key = deterministic_idempotency_key(
            payload.event_type.value,
            object_ref,
            payload.version,
            payload.payload_version,
            payload.payload,
        )
        envelope = EventEnvelope(
            event_id=payload.event_id,
            event_type=payload.event_type.value,
            version=payload.version,
            object_ref=object_ref,
            source_system="M02",
            occurred_at=payload.occurred_at,
            actor_id=payload.actor_id,
            correlation_id=payload.correlation_id,
            causation_id=payload.causation_id,
            trace_id=payload.trace_id,
            payload_version=payload.payload_version,
            payload=payload.payload,
            evidence_refs=evidence_refs,
            idempotency_key=idempotency_key,
        )
        created = CoreRepository(session).add_event(payload.tenant_id, envelope)
        session.commit()
    except (TypeError, ValueError) as exc:
        session.rollback()
        message = str(exc)
        status = 409 if "conflict" in message else 422
        raise HTTPException(status_code=status, detail=message) from exc

    return EventIngestResponse(
        event_id=payload.event_id,
        event_type=payload.event_type.value,
        created=created,
        idempotency_key=idempotency_key,
    )
