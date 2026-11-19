from fastapi.testclient import TestClient

from fac.main import create_app


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
