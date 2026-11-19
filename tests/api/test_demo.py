import importlib

from fastapi.testclient import TestClient

from fac.main import create_app


def test_demo_route_is_hidden_when_demo_is_disabled(monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "false")
    response = TestClient(create_app()).get("/demo/fac")

    assert response.status_code == 404


def test_demo_route_is_exposed_when_demo_is_enabled(monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "true")
    response = TestClient(create_app()).get("/demo/fac")

    assert response.status_code == 200


def test_demo_trigger_contract_contains_version_and_audit_fields():
    assert importlib.util.find_spec("fac.contracts.demo") is not None
    contracts = importlib.import_module("fac.contracts.demo")

    request = contracts.DemoTriggerRequest(
        order_id="ORD-1001",
        price_revision=2,
        event_id="event-v2",
        idempotency_key="key-v2",
        trigger_type="QuoteRecalculationRequired",
        reason="MaterialPriceRevision",
        actor="demo-user",
    )

    assert request.price_revision == 2
    assert request.trigger_type == "QuoteRecalculationRequired"
    assert request.reason == "MaterialPriceRevision"
    assert request.actor == "demo-user"
