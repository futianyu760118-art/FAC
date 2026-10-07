from datetime import UTC, datetime
from decimal import Decimal

import pytest

from fac.contracts.common import ObjectRef
from fac.contracts.events import EventEnvelope
from fac.domain.events import deterministic_idempotency_key


def event_values() -> dict[str, object]:
    return {
        "event_id": "evt-1",
        "event_type": "PlanCostCalculated",
        "version": 1,
        "object_ref": ObjectRef(object_type="Order", object_id="order-1", source_system="EDP", revision=2),
        "source_system": "FAC",
        "occurred_at": datetime(2026, 10, 7, tzinfo=UTC),
        "actor_id": "actor-1",
        "correlation_id": "corr-1",
        "causation_id": "cause-1",
        "trace_id": "trace-1",
        "payload_version": 1,
        "payload": {"amount": Decimal("12.30")},
        "evidence_refs": [],
        "idempotency_key": "key-1",
    }


def test_event_envelope_accepts_catalog_v1_required_fields() -> None:
    event = EventEnvelope(**event_values())

    assert event.event_type == "PlanCostCalculated"
    assert event.object_ref.object_id == "order-1"


@pytest.mark.parametrize("field", list(event_values()))
def test_event_envelope_requires_each_catalog_field(field: str) -> None:
    values = event_values()
    del values[field]

    with pytest.raises((TypeError, ValueError)):
        EventEnvelope(**values)


def test_deterministic_idempotency_key_is_stable_for_same_inputs() -> None:
    inputs = {
        "event_type": "PlanCostCalculated",
        "object_ref": event_values()["object_ref"],
        "version": 1,
        "payload_version": 1,
        "payload": {"amount": Decimal("12.30")},
    }

    first = deterministic_idempotency_key(**inputs)  # type: ignore[arg-type]
    second = deterministic_idempotency_key(**inputs)  # type: ignore[arg-type]

    assert first == second
    assert first.startswith("sha256:")
