"""Small helpers for working with evidence references."""

from collections.abc import Sequence

from fac.contracts.common import EvidenceRef
from fac.domain.errors import EvidenceRequired


def require_evidence(evidence_refs: Sequence[EvidenceRef]) -> tuple[EvidenceRef, ...]:
    """Return immutable evidence refs or raise when a formal action has none."""
    refs = tuple(evidence_refs)
    if not refs:
        raise EvidenceRequired("at least one evidence reference is required")
    if any(not isinstance(ref, EvidenceRef) for ref in refs):
        raise TypeError("evidence_refs must contain EvidenceRef values")
    return refs
