"""Common value contracts shared by FAC domains and adapters."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class FXRate:
    """A sourced, directional exchange rate from base currency to quote currency."""

    base_currency: str
    quote_currency: str
    rate: Decimal
    rate_type: str
    effective_at: date
    source: str
    revision: int
    evidence_ref: str

    def __post_init__(self) -> None:
        for field_name in ("base_currency", "quote_currency"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or len(value) != 3 or not value.isalpha():
                raise ValueError(f"{field_name} must be a three-letter currency code")
            object.__setattr__(self, field_name, value.upper())
        if not isinstance(self.rate, Decimal) or not self.rate.is_finite() or self.rate <= 0:
            raise ValueError("rate must be a finite positive Decimal")
        for field_name in ("rate_type", "source", "evidence_ref"):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not isinstance(self.effective_at, date) or isinstance(self.effective_at, datetime):
            raise TypeError("effective_at must be a date")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 1:
            raise ValueError("revision must be a positive integer")


@dataclass(frozen=True)
class EvidenceRef:
    """A portable reference to evidence stored outside the domain contract."""

    evidence_id: str
    kind: str
    source_ref: str
    checksum: str
    created_at: datetime

    def __post_init__(self) -> None:
        for field_name in ("evidence_id", "kind", "source_ref", "checksum"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime")


@dataclass(frozen=True)
class ObjectRef:
    """Stable reference to a revisioned business object."""

    object_type: str
    object_id: str
    source_system: str
    revision: int

    def __post_init__(self) -> None:
        for field_name in ("object_type", "object_id", "source_system"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 1:
            raise ValueError("revision must be a positive integer")


# Shared identifier values are intentionally opaque strings at this boundary.
EventId = str
ActorId = str
CorrelationId = str
CausationId = str
TraceId = str
IdempotencyKey = str
