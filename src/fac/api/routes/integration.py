"""EDP-only cross-system integration endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fac.contracts.common import EvidenceRef, ObjectRef
from fac.contracts.events import EventEnvelope
from fac.contracts.integration_events import FacIntegrationEventRequest
from fac.contracts.source_events import M02CrmEventRequest, M02PlmEventRequest
from fac.domain.events import deterministic_idempotency_key
from fac.domain.recalculation import build_quote_recalculation_requirement
from fac.domain.source_adapters import normalize_crm_event, normalize_plm_event
from fac.infrastructure.db import get_session
from fac.infrastructure.repositories import CoreRepository

router = APIRouter(prefix="/api/v1/fac/integration", tags=["FAC Integration"])


class EventIngestResponse(BaseModel):
    event_id: str
    event_type: str
    created: bool
    idempotency_key: str
    recalculation_required: bool = False
    requirement_created: bool = False
    requirement_event_id: str | None = None


class NativeEventIngestResponse(BaseModel):
    event_id: str
    event_type: str
    created: bool
    affected_inquiries: list[str] = []
    requirement_event_ids: list[str] = []


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
        repo = CoreRepository(session)
        created = repo.add_event(payload.tenant_id, envelope)
        requirement = build_quote_recalculation_requirement(
            envelope,
            target_inquiry_id=envelope.correlation_id,
        )
        requirement_created = False
        if requirement is not None:
            requirement_created = repo.add_event(payload.tenant_id, requirement)
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
        recalculation_required=requirement is not None,
        requirement_created=requirement_created,
        requirement_event_id=requirement.event_id if requirement is not None else None,
    )


@router.post("/m02/crm-aeos-event", response_model=NativeEventIngestResponse)
def ingest_crm_aeos_event(
    payload: M02CrmEventRequest,
    session: Annotated[Session, Depends(get_session)],
) -> NativeEventIngestResponse:
    try:
        envelope = normalize_crm_event(payload.event)
        created = CoreRepository(session).add_event(payload.tenant_id, envelope)
        session.commit()
    except (TypeError, ValueError) as exc:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return NativeEventIngestResponse(
        event_id=envelope.event_id,
        event_type=envelope.event_type,
        created=created,
    )


@router.post("/m02/plm-event", response_model=NativeEventIngestResponse)
def ingest_plm_event(
    payload: M02PlmEventRequest,
    session: Annotated[Session, Depends(get_session)],
) -> NativeEventIngestResponse:
    try:
        envelope = normalize_plm_event(payload.event_id, payload.event)
        repo = CoreRepository(session)
        created = repo.add_event(payload.tenant_id, envelope)
        affected: list[str] = []
        requirement_ids: list[str] = []
        if envelope.event_type == "BOMReleased":
            part_no = str(
                envelope.payload.get("rootPartNo")
                or envelope.payload.get("root_part_no")
                or ""
            )
            if part_no:
                affected = repo.find_submitted_inquiries_by_part_no(
                    payload.tenant_id,
                    part_no,
                )
                for inquiry_id in affected:
                    requirement = build_quote_recalculation_requirement(
                        envelope,
                        target_inquiry_id=inquiry_id,
                    )
                    if requirement is not None:
                        repo.add_event(payload.tenant_id, requirement)
                        requirement_ids.append(requirement.event_id)
        elif envelope.event_type in {
            "ProductConfigurationConfirmed",
            "SpecificationConfirmed",
        }:
            inquiry_id = str(envelope.payload.get("inquiry_id") or "")
            if inquiry_id:
                affected = [inquiry_id]
                requirement = build_quote_recalculation_requirement(
                    envelope,
                    target_inquiry_id=inquiry_id,
                )
                if requirement is not None:
                    repo.add_event(payload.tenant_id, requirement)
                    requirement_ids.append(requirement.event_id)
        session.commit()
    except (TypeError, ValueError) as exc:
        session.rollback()
        message = str(exc)
        status = 409 if "conflict" in message else 422
        raise HTTPException(status_code=status, detail=message) from exc

    return NativeEventIngestResponse(
        event_id=envelope.event_id,
        event_type=envelope.event_type,
        created=created,
        affected_inquiries=affected,
        requirement_event_ids=requirement_ids,
    )
