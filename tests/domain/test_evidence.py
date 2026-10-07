from datetime import UTC, datetime

from fac.contracts.common import EvidenceRef
from fac.domain.errors import EvidenceRequired
from fac.domain.evidence import require_evidence


def test_evidence_reference_preserves_all_catalog_fields() -> None:
    created_at = datetime(2026, 10, 7, 12, tzinfo=UTC)
    evidence = EvidenceRef(
        evidence_id="ev-123",
        kind="invoice",
        source_ref="edp://invoice/123",
        checksum="sha256:abc123",
        created_at=created_at,
    )

    assert evidence.evidence_id == "ev-123"
    assert evidence.kind == "invoice"
    assert evidence.source_ref == "edp://invoice/123"
    assert evidence.checksum == "sha256:abc123"
    assert evidence.created_at == created_at


def test_require_evidence_rejects_empty_references_with_stable_error() -> None:
    try:
        require_evidence([])
    except EvidenceRequired as exc:
        assert exc.code == "EVIDENCE_REQUIRED"
    else:
        raise AssertionError("Expected EvidenceRequired")
