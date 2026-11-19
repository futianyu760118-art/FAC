from fastapi.testclient import TestClient

from fac.contracts.common import ObjectRef
from fac.infrastructure.db import make_engine, make_session_factory
from fac.infrastructure.models import Base, CalculationResult
from fac.infrastructure.repositories import EdpRepository
from fac.main import create_app


def _seed_formal_order(session):
    repository = EdpRepository(session)
    source = "m02-edp"
    payloads = (
        (ObjectRef("Order", "ORD-1001", source, 1), {
            "object_id": "ORD-1001", "product_id": "PROD-1001", "quantity": "2",
            "order_date": "2026-10-07", "functional_currency": "CNY",
        }),
        (ObjectRef("BOM", "BOM-1001", source, 1), {
            "product_id": "PROD-1001",
            "lines": [{"material_id": "STEEL-1001", "quantity": "3", "uom": "kg"}],
        }),
        (ObjectRef("MaterialPrice", "PRICE-1001", source, 1), {
            "material_id": "STEEL-1001", "unit_price": {"amount": "4", "currency": "CNY"},
            "uom": "kg", "effective_at": "2026-01-01",
        }),
        (ObjectRef("Labor", "LABOR-1001", source, 1), {
            "product_id": "PROD-1001", "hours_per_unit": "2",
            "hourly_rate": {"amount": "5", "currency": "CNY"},
        }),
        (ObjectRef("Expense", "EXPENSE-1001", source, 1), {
            "product_id": "PROD-1001", "expense_per_unit": {"amount": "1", "currency": "CNY"},
        }),
    )
    for ref, payload in payloads:
        repository.add("tenant-a", ref, payload)
    session.commit()


def test_formal_fac_workbench_is_available_when_demo_routes_are_disabled(monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "false")

    client = TestClient(create_app())

    workbench = client.get("/fac")
    demo = client.get("/demo/fac")

    assert workbench.status_code == 200
    assert "FAC 财经自治中心" in workbench.text
    assert demo.status_code == 404


def test_formal_fac_overview_returns_ready_state_without_demo_initialization(monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "false")

    response = TestClient(create_app()).get("/api/v1/fac/overview")

    assert response.status_code == 200
    assert response.json() == {
        "service": "fac",
        "status": "ready",
        "environment": "development",
        "demo_enabled": False,
    }


def test_formal_fac_api_exposes_business_collections_without_demo_initialization(monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "false")

    client = TestClient(create_app())

    for path in ("orders", "rules", "periods", "events", "external-requests"):
        response = client.get(f"/api/v1/fac/{path}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_formal_fac_calculation_api_uses_edp_refs_and_returns_versioned_result(tmp_path, monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "false")
    engine = make_engine(f"sqlite:///{tmp_path / 'formal-api.db'}")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session:
        _seed_formal_order(session)

    client = TestClient(create_app(make_session_factory(engine)))
    body = {
        "tenant_id": "tenant-a",
        "order_id": "ORD-1001",
        "period_id": "2026-11",
        "rule_id": "OFA_PLAN_COST",
        "rule_version": "v1",
        "input_refs": [
            {"object_type": "Order", "object_id": "ORD-1001", "source_system": "m02-edp", "revision": 1},
            {"object_type": "BOM", "object_id": "BOM-1001", "source_system": "m02-edp", "revision": 1},
            {"object_type": "MaterialPrice", "object_id": "PRICE-1001", "source_system": "m02-edp", "revision": 1},
            {"object_type": "Labor", "object_id": "LABOR-1001", "source_system": "m02-edp", "revision": 1},
            {"object_type": "Expense", "object_id": "EXPENSE-1001", "source_system": "m02-edp", "revision": 1},
        ],
        "actor": "user-001",
        "idempotency_key": "formal-api-v1",
    }

    response = client.post("/api/v1/fac/orders/ORD-1001/calculations", json=body)

    assert response.status_code == 200
    assert response.json()["result"]["total_cost"]["functional_amount"] == "46.00"
    assert response.json()["result"]["version"] == 1


def test_formal_integration_projection_reflects_calculated_result(tmp_path, monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "false")
    engine = make_engine(f"sqlite:///{tmp_path / 'formal-integration.db'}")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session:
        _seed_formal_order(session)

    client = TestClient(create_app(make_session_factory(engine)))
    body = {
        "tenant_id": "tenant-a",
        "order_id": "ORD-1001",
        "period_id": "2026-11",
        "rule_id": "OFA_PLAN_COST",
        "rule_version": "v1",
        "input_refs": [
            {"object_type": "Order", "object_id": "ORD-1001", "source_system": "m02-edp", "revision": 1},
            {"object_type": "BOM", "object_id": "BOM-1001", "source_system": "m02-edp", "revision": 1},
            {"object_type": "MaterialPrice", "object_id": "PRICE-1001", "source_system": "m02-edp", "revision": 1},
            {"object_type": "Labor", "object_id": "LABOR-1001", "source_system": "m02-edp", "revision": 1},
            {"object_type": "Expense", "object_id": "EXPENSE-1001", "source_system": "m02-edp", "revision": 1},
        ],
        "actor": "integration-test",
        "idempotency_key": "formal-integration-v1",
    }

    calculated = client.post("/api/v1/fac/orders/ORD-1001/calculations", json=body)
    projection = client.get("/api/v1/fac/integration", params={"tenant_id": "tenant-a"})

    assert calculated.status_code == 200
    fac_stage = next(stage for stage in projection.json()["stages"] if stage["module"] == "M09 FAC")
    assert fac_stage["status"] == "WAITING_EVIDENCE"
    assert fac_stage["output_refs"] == ["Order:ORD-1001:plan:v1"]


def test_formal_evidence_does_not_verify_unknown_references(tmp_path, monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "false")
    engine = make_engine(f"sqlite:///{tmp_path / 'formal-evidence.db'}")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session:
        session.add(
            CalculationResult(
                tenant_id="tenant-a",
                object_id="Order:ORD-1001:plan:v1",
                source_system="fac",
                revision=1,
                payload={"evidence_refs": ["missing-evidence"]},
            )
        )
        session.commit()

    response = TestClient(create_app(make_session_factory(engine))).get(
        "/api/v1/fac/results/Order%3AORD-1001%3Aplan%3Av1/evidence",
        params={"tenant_id": "tenant-a"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "WAITING_EVIDENCE"
    assert response.json()["evidence_coverage"] == 0
