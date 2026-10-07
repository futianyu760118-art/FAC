from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from fac.contracts.common import EvidenceRef, ObjectRef
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


def test_event_envelope_defensively_freezes_nested_payload_and_evidence_refs() -> None:
    payload_source = {"items": [{"amount": Decimal("12.30")}]}
    evidence_source = [
        EvidenceRef(
            evidence_id="ev-1",
            kind="invoice",
            source_ref="edp://invoice/1",
            checksum="sha256:abc",
            created_at=datetime(2026, 10, 7, tzinfo=UTC),
        )
    ]
    values = event_values()
    values["payload"] = payload_source
    values["evidence_refs"] = evidence_source
    event = EventEnvelope(**values)
    key_before_mutation = deterministic_idempotency_key(
        event.event_type,
        event.object_ref,
        event.version,
        event.payload_version,
        event.payload,
    )

    payload_source["items"][0]["amount"] = Decimal("99.99")
    evidence_source.clear()

    assert event.payload["items"][0]["amount"] == Decimal("12.30")
    assert len(event.evidence_refs) == 1
    assert deterministic_idempotency_key(
        event.event_type,
        event.object_ref,
        event.version,
        event.payload_version,
        event.payload,
    ) == key_before_mutation
    with pytest.raises(TypeError):
        event.payload["new"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        event.payload["items"][0]["amount"] = Decimal(0)  # type: ignore[index]
    with pytest.raises(AttributeError):
        event.evidence_refs.append(evidence_source)  # type: ignore[attr-defined]


def test_idempotency_canonicalizes_dataclass_fields_recursively() -> None:
    @dataclass
    class NestedPayload:
        amount: Decimal
        effective_date: date
        captured_at: datetime

    payload = {
        "evidence": NestedPayload(
            amount=Decimal("4.25"),
            effective_date=date(2026, 10, 7),
            captured_at=datetime(2026, 10, 7, tzinfo=UTC),
        )
    }
    event = event_values()

    key = deterministic_idempotency_key(
        "EvidenceAttached", event["object_ref"], 1, 1, payload  # type: ignore[arg-type]
    )

    assert key.startswith("sha256:")
