"""Versioned event envelope contract."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Any

from fac.contracts.common import EvidenceRef, ObjectRef


@dataclass(frozen=True)
class EventEnvelope:
    event_id: str
    event_type: str
    version: int
    object_ref: ObjectRef
    source_system: str
    occurred_at: datetime
    actor_id: str
    correlation_id: str
    causation_id: str
    trace_id: str
    payload_version: int
    payload: Mapping[str, Any]
    evidence_refs: Sequence[EvidenceRef]
    idempotency_key: str

    def __post_init__(self) -> None:
        for field_name in (
            "event_id",
            "event_type",
            "source_system",
            "actor_id",
            "correlation_id",
            "causation_id",
            "trace_id",
            "idempotency_key",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        for field_name in ("version", "payload_version"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{field_name} must be a positive integer")
        if not isinstance(self.object_ref, ObjectRef):
            raise TypeError("object_ref must be an ObjectRef")
        if not isinstance(self.occurred_at, datetime):
            raise TypeError("occurred_at must be a datetime")
        if not isinstance(self.payload, Mapping):
            raise TypeError("payload must be a mapping")
        if not isinstance(self.evidence_refs, (list, tuple)) or any(
            not isinstance(ref, EvidenceRef) for ref in self.evidence_refs
        ):
            raise ValueError("evidence_refs must be a sequence of EvidenceRef values")
        object.__setattr__(self, "payload", _freeze(self.payload))
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))


def _freeze(value: Any) -> Any:
    """Copy supported event values into recursively immutable containers."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    if is_dataclass(value) and not isinstance(value, type):
        return MappingProxyType({field.name: _freeze(getattr(value, field.name)) for field in fields(value)})
    if value is None or isinstance(value, (str, int, bool, Decimal, date, datetime)):
        return value
    raise TypeError(f"unsupported mutable event payload value: {type(value).__name__}")
