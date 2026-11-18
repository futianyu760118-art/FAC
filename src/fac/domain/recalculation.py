"""Automatic quote-recalculation requirement generation."""

from fac.contracts.common import ObjectRef
from fac.contracts.events import EventEnvelope
from fac.domain.events import deterministic_idempotency_key

QUOTE_RECALC_TRIGGER_TYPES = {
    "ProductConfigurationConfirmed",
    "SpecificationConfirmed",
    "BOMReleased",
}


def build_quote_recalculation_requirement(
    source_event: EventEnvelope,
) -> EventEnvelope | None:
    """Create an immutable FAC requirement when M04 changes quote-driving product data."""
    if source_event.event_type not in QUOTE_RECALC_TRIGGER_TYPES:
        return None

    object_ref = ObjectRef(
        object_type="QuoteRecalculationRequirement",
        object_id=source_event.correlation_id,
        source_system="M09",
        revision=source_event.object_ref.revision,
    )
    payload = {
        "status": "OPEN",
        "reason": "M04产品配置、规格书或BOM发生确认/发布变更",
        "trigger_event_id": source_event.event_id,
        "trigger_event_type": source_event.event_type,
        "changed_object": source_event.object_ref.model_dump(mode="json"),
    }
    event_type = "QuoteRecalculationRequired"
    event_id = f"FAC-QUOTE-RECALC:{source_event.event_id}"
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
        source_system="M09",
        occurred_at=source_event.occurred_at,
        actor_id="M09",
        correlation_id=source_event.correlation_id,
        causation_id=source_event.event_id,
        trace_id=source_event.trace_id,
        payload_version=1,
        payload=payload,
        evidence_refs=source_event.evidence_refs,
        idempotency_key=idempotency_key,
    )
