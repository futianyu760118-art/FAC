import json
from pathlib import Path

from fastapi.testclient import TestClient

from fac.adapters.edp_mock.adapter import EdpAdapter
from fac.adapters.edp_mock.models import EdpFixture
from fac.contracts.common import ObjectRef
from fac.infrastructure.db import make_engine, make_session_factory
from fac.infrastructure.models import Base
from fac.infrastructure.repositories import EdpRepository
from fac.main import create_app


def _payload():
    return json.loads(
        (Path(__file__).resolve().parents[2] / "fixtures/edp/sample_phase1.json").read_text()
    )


def _session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'import.db'}")
    Base.metadata.create_all(engine)
    return make_session_factory(engine)


def test_fixture_import_preserves_all_kinds_and_revision(tmp_path):
    factory = _session(tmp_path)
    payload = EdpFixture.model_validate(_payload())
    with factory() as session:
        report = EdpAdapter(session).import_fixture(payload)
        assert report.accepted_count == 7
        assert report.rejected_count == 0
        for kind, object_id in [
            ("Order", "ORD-001"),
            ("BOM", "BOM-001"),
            ("MaterialPrice", "PRICE-001"),
            ("Labor", "LABOR-001"),
            ("Expense", "EXP-001"),
            ("FX", "FX-USD-CNY"),
            ("FX", "FX-EUR-CNY"),
        ]:
            record = EdpRepository(session).get(
                "tenant-a", ObjectRef(kind, object_id, "edp-mock", 1)
            )
            assert record is not None
            assert record.source_system == "edp-mock"
            assert record.revision == 1


def test_malformed_object_is_rejected_without_partial_record(tmp_path):
    factory = _session(tmp_path)
    raw = _payload()
    raw["orders"].append({"object_id": "BAD-ORDER", "revision": 1, "currency": "US"})
    with factory() as session:
        report = EdpAdapter(session).import_fixture(EdpFixture.model_validate(raw))
        assert report.accepted_count == 7
        assert report.rejected_count == 1
        assert report.rejected[0].object_id == "BAD-ORDER"
        assert report.rejected[0].reasons
        assert (
            EdpRepository(session).get("tenant-a", ObjectRef("Order", "BAD-ORDER", "edp-mock", 1))
            is None
        )


def test_reimport_is_idempotent_and_other_tenant_cannot_read(tmp_path):
    factory = _session(tmp_path)
    payload = EdpFixture.model_validate(_payload())
    with factory() as session:
        first = EdpAdapter(session).import_fixture(payload)
        second = EdpAdapter(session).import_fixture(payload)
        assert first.accepted_count == 7
        assert second.accepted_count == 0
        assert second.skipped_count == 7
        ref = ObjectRef("Order", "ORD-001", "edp-mock", 1)
        repo = EdpRepository(session)
        assert repo.get("tenant-a", ref) is not None
        assert repo.get("tenant-b", ref) is None


def test_import_route_returns_counts_and_reasons(tmp_path):
    factory = _session(tmp_path)
    app = create_app(session_factory=factory)
    raw = _payload()
    raw["orders"].append({"object_id": "BAD-ORDER", "revision": 1})
    response = TestClient(app).post("/api/v1/import/edp-fixture", json=raw)
    assert response.status_code == 200
    assert response.json()["accepted_count"] == 7
    assert response.json()["rejected_count"] == 1
    assert response.json()["rejected"][0]["object_id"] == "BAD-ORDER"
