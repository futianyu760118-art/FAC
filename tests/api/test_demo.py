import importlib

from fastapi.testclient import TestClient

from fac.infrastructure.db import make_engine, make_session_factory
from fac.infrastructure.models import Base
from fac.main import create_app


def test_demo_route_is_hidden_when_demo_is_disabled(monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "false")
    response = TestClient(create_app()).get("/demo/fac")

    assert response.status_code == 404


def test_demo_route_is_exposed_when_demo_is_enabled(monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "true")
    response = TestClient(create_app()).get("/demo/fac")

    assert response.status_code == 200


def test_full_fac_workbench_is_exposed_when_demo_is_enabled(monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "true")
    response = TestClient(create_app()).get("/fac")

    assert response.status_code == 200
    for text in (
        "FAC 财经自治中心",
        "真实系统联调主干",
        "M02 EDP",
        "M13 Agent",
        "M01 Guard",
        "M10 POMS",
        "Event Ledger",
        "运行联调演示",
    ):
        assert text in response.text


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


def test_demo_api_runs_calculation_recalculation_and_replay(tmp_path, monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "true")
    engine = make_engine(f"sqlite:///{tmp_path / 'api.db'}")
    Base.metadata.create_all(engine)
    client = TestClient(create_app(make_session_factory(engine)))

    empty_state = client.get("/api/v1/demo/state")
    assert empty_state.status_code == 404
    blocked_reset = client.post(
        "/api/v1/demo/reset", headers={"Origin": "https://attacker.example"}
    )
    assert blocked_reset.status_code == 403

    reset = client.post("/api/v1/demo/reset")
    assert reset.status_code == 200
    assert len(reset.json()["seeded_refs"]) == 6
    seeded_state = client.get("/api/v1/demo/state")
    assert seeded_state.status_code == 200
    assert len(seeded_state.json()["input_refs"]) == 6
    unknown_replay = client.post(
        "/api/v1/demo/replay",
        json={
            "order_id": "ORD-1001",
            "price_revision": 2,
            "event_id": "unknown-event",
            "idempotency_key": "unknown-key",
            "trigger_type": "QuoteRecalculationRequired",
            "reason": "Unknown replay",
            "actor": "demo-user",
        },
    )
    assert unknown_replay.status_code == 404

    body = {
        "order_id": "ORD-1001",
        "price_revision": 1,
        "event_id": "demo-event-v1",
        "idempotency_key": "demo-key-v1",
        "trigger_type": "QuoteRecalculationRequired",
        "reason": "Initial quote",
        "actor": "demo-user",
    }
    first = client.post("/api/v1/demo/events/quote-recalculation", json=body)
    assert first.status_code == 200
    assert first.json()["result"]["total_cost"]["functional_amount"] == "46.00"
    assert first.json()["calculation"]["trigger_type"] == "QuoteRecalculationRequired"
    assert first.json()["calculation"]["reason"] == "Initial quote"
    assert first.json()["calculation"]["actor"] == "demo-user"

    second_body = {**body, "price_revision": 2, "event_id": "demo-event-v2", "idempotency_key": "demo-key-v2", "reason": "MaterialPriceRevision"}
    second = client.post("/api/v1/demo/events/quote-recalculation", json=second_body)
    assert second.status_code == 200
    assert second.json()["result"]["total_cost"]["functional_amount"] == "52.00"
    assert second.json()["result"]["previous_result_id"] == first.json()["result"]["result_id"]

    replay = client.post("/api/v1/demo/replay", json=second_body)
    assert replay.status_code == 200
    assert replay.json()["replayed"] is True
    assert replay.json()["result"]["result_id"] == second.json()["result"]["result_id"]

    third_body = {
        **second_body,
        "event_id": "demo-event-v2-followup",
        "idempotency_key": "demo-key-v2-followup",
        "actor": "demo-auditor",
    }
    third = client.post("/api/v1/demo/events/quote-recalculation", json=third_body)
    assert third.status_code == 200
    assert third.json()["replayed"] is False
    state_after_third = client.get("/api/v1/demo/state")
    assert len(state_after_third.json()["events"]) == 3
    third_replay = client.post("/api/v1/demo/replay", json=third_body)
    assert third_replay.status_code == 200
    assert third_replay.json()["replayed"] is True

    state = client.get("/api/v1/demo/state")
    assert state.status_code == 200
    assert len(state.json()["calculations"]) == 2
    assert len(state.json()["results"]) == 2


def test_demo_page_contains_the_finance_workbench_workflow(monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "true")
    response = TestClient(create_app()).get("/demo/fac")

    assert response.status_code == 200
    for text in (
        "FAC Demo",
        "ORD-1001",
        "初始化 Demo 数据",
        "运行初次计算",
        "价格修正并重算",
        "重放最近事件",
        "CalculationSnapshot",
        "V1",
        "V2",
        "checksum",
    ):
        assert text in response.text
    assert "textContent" in response.text
    assert "innerHTML" not in response.text
    assert '$("recalculate").disabled' in response.text
    assert '$("replay").disabled' in response.text
    assert "void refresh();" in response.text
