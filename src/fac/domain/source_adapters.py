"""Normalize source-native M05/M04 events into FAC canonical events."""

from fac.contracts.common import ObjectRef
from fac.contracts.events import EventEnvelope
from fac.contracts.source_events import CrmAeosEventV1, PlmEventV1
from fac.domain.events import deterministic_idempotency_key


def _canonical_event(
    *,
    event_id: str,
    event_type: str,
    object_type: str,
    object_id: str,
    source_system: str,
    revision: int,
    occurred_at,
    actor_id: str,
    correlation_id: str,
    causation_id: str,
    trace_id: str,
    payload: dict,
) -> EventEnvelope:
    object_ref = ObjectRef(
        object_type=object_type,
        object_id=object_id,
        source_system=source_system,
        revision=max(revision, 1),
    )
    idempotency_key = deterministic_idempotency_key(
        event_type,
        object_ref,
        1,
        1,
        payload,
    )
    return EventEnvelope(
        event_id=event_id,
        event_type=event_type,
        version=1,
        object_ref=object_ref,
        source_system=source_system,
        occurred_at=occurred_at,
        actor_id=actor_id,
        correlation_id=correlation_id,
        causation_id=causation_id,
        trace_id=trace_id,
        payload_version=1,
        payload=payload,
        evidence_refs=[],
        idempotency_key=idempotency_key,
    )


def normalize_crm_event(event: CrmAeosEventV1) -> EventEnvelope:
    if event.object_type != "Inquiry" or event.event_type != "inquiry.upserted":
        raise ValueError("FAC P0 CRM adapter currently accepts Inquiry inquiry.upserted only")
    status = str(event.payload.get("status") or "").upper()
    canonical_type = "InquirySubmitted" if status == "SUBMITTED" else "InquiryCreated"
    inquiry_no = str(event.payload.get("serial_number") or event.object_id)
    payload = dict(event.payload)
    payload["crm_contract_version"] = event.contract_version
    payload["crm_event_type"] = event.event_type
    payload["crm_operation"] = event.operation
    return _canonical_event(
        event_id=f"M05:{event.event_id}",
        event_type=canonical_type,
        object_type="Inquiry",
        object_id=event.object_id,
        source_system="M05",
        revision=1,
        occurred_at=event.occurred_at,
        actor_id="M05",
        correlation_id=inquiry_no,
        causation_id=event.event_id,
        trace_id=event.trace_id,
        payload=payload,
    )


def normalize_plm_event(event_id: str, event: PlmEventV1) -> EventEnvelope:
    event_type_map = {
        "BOMReleased": "BOMReleased",
        "bom.released": "BOMReleased",
        "ProductConfigurationConfirmed": "ProductConfigurationConfirmed",
        "SpecificationConfirmed": "SpecificationConfirmed",
    }
    canonical_type = event_type_map.get(event.event_type)
    if canonical_type is None:
        raise ValueError(f"unsupported PLM event_type: {event.event_type}")
    payload = dict(event.payload)
    if event.evidence_refs:
        payload["source_evidence_ids"] = list(event.evidence_refs)
    return _canonical_event(
        event_id=f"M04:{event_id}",
        event_type=canonical_type,
        object_type=event.object_type,
        object_id=event.object_id,
        source_system="M04",
        revision=max(event.version or 1, 1),
        occurred_at=event.occurred_at,
        actor_id="M04",
        correlation_id=event.correlation_id or event.object_id,
        causation_id=event_id,
        trace_id=event.correlation_id or event_id,
        payload=payload,
    )
