from fastapi.testclient import TestClient

from fac.api.routes.fac import router
from fac.infrastructure.db import make_engine, make_session_factory
from fac.infrastructure.models import Base
from fac.main import create_app
from tests.api.test_fac_api import _seed_formal_order


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("FAC_DEMO_ENABLED", "false")
    engine = make_engine(f"sqlite:///{tmp_path / 'boundary.db'}")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session:
        _seed_formal_order(session)
    return TestClient(create_app(make_session_factory(engine)))


def test_formal_orders_are_edp_backed_and_tenant_scoped(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    formal_orders = client.get("/api/v1/fac/orders", params={"tenant_id": "tenant-a"})
    other_tenant_orders = client.get(
        "/api/v1/fac/orders", params={"tenant_id": "tenant-b"}
    )

    assert formal_orders.status_code == 200
    assert formal_orders.json()[0]["source_system"] == "m02-edp"
    assert {ref["object_type"] for ref in formal_orders.json()[0]["input_refs"]} >= {
        "Order",
        "BOM",
        "MaterialPrice",
        "Labor",
        "Expense",
    }
    assert other_tenant_orders.json() == []


def test_formal_write_rejects_cross_origin_and_missing_edp_refs(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    body = {
        "tenant_id": "tenant-a",
        "order_id": "ORD-1001",
        "period_id": "2026-11",
        "rule_id": "OFA_PLAN_COST",
        "rule_version": "v1",
        "input_refs": [
            {
                "object_type": "Order",
                "object_id": "ORD-1001",
                "source_system": "m02-edp",
                "revision": 1,
            },
            {
                "object_type": "BOM",
                "object_id": "MISSING-BOM",
                "source_system": "m02-edp",
                "revision": 1,
            },
        ],
        "actor": "regression-test",
        "idempotency_key": "boundary-missing-ref",
    }

    cross_origin = client.post(
        "/api/v1/fac/orders/ORD-1001/calculations",
        json=body,
        headers={"origin": "https://untrusted.example"},
    )
    missing_ref = client.post(
        "/api/v1/fac/orders/ORD-1001/calculations",
        json=body,
        headers={"origin": "http://testserver"},
    )

    assert cross_origin.status_code == 403
    assert missing_ref.status_code == 400
    assert "missing EDP reference" in missing_ref.json()["detail"]


def test_formal_integration_projection_keeps_unavailable_adapters_waiting(
    tmp_path, monkeypatch
):
    client = _client(tmp_path, monkeypatch)

    projection = client.get("/api/v1/fac/integration").json()
    stages = {stage["module"]: stage for stage in projection["stages"]}

    assert projection["mode"] == "FORMAL"
    assert stages["M13 Agent"]["status"] == "WAITING_EXTERNAL"
    assert stages["M10 POMS"]["status"] == "WAITING_EXTERNAL"
    assert stages["FAC Verify"]["status"] == "WAITING_EVIDENCE"
    assert projection["verify"]["evidence_coverage"] == 0


def test_formal_router_has_no_demo_api_dependency():
    paths = {route.path for route in router.routes}

    assert all("demo" not in path for path in paths)
    assert "/api/v1/fac/orders/{order_id}/calculations" in paths
