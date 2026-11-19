import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from fac.adapters.m13 import http as m13_http
from fac.adapters.m13.http import (
    AgentNotDispatchable,
    AgentNotPublished,
    AgentNotRegistered,
    HttpM13RegistryAdapter,
    M13RegistryConfigurationError,
    _signed_headers,
)
from fac.main import create_app


def _payload(*, dispatchable: bool = True):
    return {
        "registrySystem": "M13",
        "revision": 7,
        "generatedAt": "2026-11-19T01:30:00.000Z",
        "items": [
            {
                "agentId": "AG-FAC-001",
                "harborAgentId": "agent-harbor-1",
                "name": "财务总监智能体",
                "role": "综合财经",
                "skills": ["finance_review_pack", "finance_opportunity"],
                "autonomyLevel": "A1",
                "status": "idle",
                "runtimeId": "runtime-1",
                "runtimeStatus": "online",
                "m01State": "active" if dispatchable else "pending",
                "m01AgentId": "agent-harbor-1" if dispatchable else None,
                "effectiveScopes": ["task:execute"] if dispatchable else [],
                "dispatchable": dispatchable,
                "updatedAt": "2026-11-19T01:20:00.000Z",
            }
        ],
    }


def test_hmac_headers_match_m13_contract():
    headers = _signed_headers("fac-m09", "secret-1", now_ms=1763517000000)
    expected = hmac.new(
        b"secret-1",
        b"1763517000000.",
        hashlib.sha256,
    ).hexdigest()
    assert headers["x-aeos-key-id"] == "fac-m09"
    assert headers["x-aeos-timestamp"] == "1763517000000"
    assert headers["x-aeos-signature"] == f"sha256={expected}"


def test_http_registry_requires_real_m13_and_m01_dispatchability(monkeypatch):
    monkeypatch.setattr(m13_http, "_fetch_json", lambda *args, **kwargs: _payload())
    adapter = HttpM13RegistryAdapter(
        base_url="http://m13.local",
        key_id="fac-m09",
        secret="secret-1",
    )
    assert adapter.require_published("AG-FAC-001").name_zh == "财务总监智能体"

    monkeypatch.setattr(
        m13_http,
        "_fetch_json",
        lambda *args, **kwargs: _payload(dispatchable=False),
    )
    with pytest.raises(AgentNotDispatchable):
        adapter.require_published("AG-FAC-001")


def test_fac_catalog_testing_status_still_blocks_even_if_m13_dispatchable(monkeypatch):
    monkeypatch.setattr(m13_http, "_fetch_json", lambda *args, **kwargs: _payload())
    adapter = HttpM13RegistryAdapter(
        base_url="http://m13.local",
        key_id="fac-m09",
        secret="secret-1",
    )
    with pytest.raises(AgentNotPublished):
        adapter.require_published("AG-FAC-005")


def test_missing_m13_agent_fails_closed(monkeypatch):
    payload = _payload()
    payload["items"] = []
    monkeypatch.setattr(m13_http, "_fetch_json", lambda *args, **kwargs: payload)
    adapter = HttpM13RegistryAdapter(
        base_url="http://m13.local",
        key_id="fac-m09",
        secret="secret-1",
    )
    with pytest.raises(AgentNotRegistered):
        adapter.require_published("AG-FAC-001")


def test_missing_registry_configuration_is_rejected():
    with pytest.raises(M13RegistryConfigurationError):
        HttpM13RegistryAdapter(base_url="", key_id="fac-m09", secret="")


def test_live_registry_endpoint_fails_closed_without_configuration(monkeypatch):
    monkeypatch.setenv("FAC_M13_REGISTRY_URL", "")
    monkeypatch.setenv("FAC_M13_REGISTRY_SECRET", "")
    client = TestClient(create_app())
    response = client.get("/api/v1/fac/m13/finance-agents/runtime")
    assert response.status_code == 503


def test_live_registry_endpoint_returns_m13_projection(monkeypatch):
    monkeypatch.setenv("FAC_M13_REGISTRY_URL", "http://m13.local")
    monkeypatch.setenv("FAC_M13_REGISTRY_KEY_ID", "fac-m09")
    monkeypatch.setenv("FAC_M13_REGISTRY_SECRET", "secret-1")
    monkeypatch.setattr(m13_http, "_fetch_json", lambda *args, **kwargs: _payload())
    client = TestClient(create_app())
    response = client.get("/api/v1/fac/m13/finance-agents/runtime")
    assert response.status_code == 200
    body = response.json()
    assert body["registry_system"] == "M13"
    assert body["items"][0]["agent_id"] == "AG-FAC-001"
    assert body["items"][0]["m01_agent_id"] == "agent-harbor-1"
    assert body["items"][0]["dispatchable"] is True
