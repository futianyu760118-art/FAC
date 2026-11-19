from __future__ import annotations

from fastapi.testclient import TestClient

from fac.adapters.m01 import http as m01_http
from fac.adapters.m13 import http as m13_http
from fac.domain.m01_guard import FinanceGuardAction
from fac.main import create_app


def _m13_payload(*, dispatchable: bool = True, m01_agent_id: str | None = "A_M01_FAC_001"):
    return {
        "registrySystem": "M13",
        "revision": 9,
        "generatedAt": "2026-11-19T02:10:00.000Z",
        "items": [
            {
                "agentId": "AG-FAC-001",
                "harborAgentId": "agent-harbor-1",
                "name": "财务总监智能体",
                "role": "综合财经",
                "skills": ["finance_review_pack"],
                "autonomyLevel": "A1",
                "status": "idle",
                "runtimeId": "runtime-1",
                "runtimeStatus": "online",
                "m01State": "active" if dispatchable else "pending",
                "m01AgentId": m01_agent_id,
                "effectiveScopes": ["task:execute"] if dispatchable else [],
                "dispatchable": dispatchable,
                "updatedAt": "2026-11-19T02:00:00.000Z",
            }
        ],
    }


def _configure(monkeypatch):
    monkeypatch.setenv("FAC_M13_REGISTRY_URL", "http://m13.local")
    monkeypatch.setenv("FAC_M13_REGISTRY_KEY_ID", "fac-m09")
    monkeypatch.setenv("FAC_M13_REGISTRY_SECRET", "m13-secret")
    monkeypatch.setenv("FAC_M01_KERNEL_URL", "http://m01.local")
    monkeypatch.setenv("FAC_M01_ACCESS_TOKEN", "m01-token")
    monkeypatch.setattr(m13_http, "_fetch_json", lambda *args, **kwargs: _m13_payload())


def test_general_execution_is_allowed_after_m13_and_m01_guard(monkeypatch):
    _configure(monkeypatch)

    def fake_post(url, payload, headers, timeout):
        assert url.endswith("/kernel/v1/authorize")
        assert payload == {
            "tenant_id": "HENGJIAN",
            "principal_id": "A_M01_FAC_001",
            "resource": "task",
            "action": "execute",
        }
        assert headers["Authorization"] == "Bearer m01-token"
        return {
            "trace_id": "TRACE-M01-ALLOW",
            "tenant_id": "HENGJIAN",
            "principal_id": "A_M01_FAC_001",
            "resource": "task",
            "action": "execute",
            "decision": "ALLOW",
            "reason": "agent scope task:execute",
        }

    monkeypatch.setattr(m01_http, "_post_json", fake_post)
    response = TestClient(create_app()).post(
        "/api/v1/fac/m01/guard",
        json={
            "tenant_id": "HENGJIAN",
            "agent_id": "AG-FAC-001",
            "action_type": "TASK_EXECUTE",
            "object_id": "INQ-2026-0088",
            "parameters": {"quote_version": "V2"},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "ALLOW"
    assert body["execution_allowed"] is True
    assert body["requires_human_approval"] is False
    assert body["m01_agent_id"] == "A_M01_FAC_001"


def test_payment_execution_auto_creates_approval_and_stays_blocked(monkeypatch):
    _configure(monkeypatch)
    calls = []

    def fake_post(url, payload, headers, timeout):
        calls.append((url, payload))
        if url.endswith("/kernel/v1/authorize"):
            assert payload["resource"] == "payment"
            assert payload["action"] == "execute"
            return {
                "trace_id": "TRACE-M01-PAY",
                "tenant_id": "HENGJIAN",
                "principal_id": "A_M01_FAC_001",
                "resource": "payment",
                "action": "execute",
                "decision": "REQUIRE_APPROVAL",
                "reason": "high risk action needs approval ticket before execution",
            }
        assert url.endswith("/kernel/v1/approvals")
        assert payload["object_id"] == "PAY-2026-001"
        assert payload["parameters"] == {"amount_cny": "150000.00"}
        return {
            "ok": True,
            "approval": {
                "approval_id": "APR-001",
                "tenant_id": "HENGJIAN",
                "requester_id": "FAC-SERVICE",
                "resource": "payment",
                "action": "execute",
                "object_id": "PAY-2026-001",
                "parameters_hash": "abc123",
                "status": "PENDING",
                "created_at": "2026-11-19T02:10:00.000Z",
                "decided_at": None,
                "decided_by": None,
                "comment": None,
                "consumed_at": None,
            },
        }

    monkeypatch.setattr(m01_http, "_post_json", fake_post)
    response = TestClient(create_app()).post(
        "/api/v1/fac/m01/guard",
        json={
            "tenant_id": "HENGJIAN",
            "agent_id": "AG-FAC-001",
            "action_type": "PAYMENT_EXECUTE",
            "object_id": "PAY-2026-001",
            "parameters": {"amount_cny": "150000.00"},
            "auto_create_approval": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "REQUIRE_APPROVAL"
    assert body["execution_allowed"] is False
    assert body["requires_human_approval"] is True
    assert body["approval"]["approval_id"] == "APR-001"
    assert body["approval"]["status"] == "PENDING"
    assert len(calls) == 2


def test_denied_action_never_creates_approval(monkeypatch):
    _configure(monkeypatch)
    calls = []

    def fake_post(url, payload, headers, timeout):
        calls.append(url)
        return {
            "trace_id": "TRACE-M01-DENY",
            "tenant_id": "HENGJIAN",
            "principal_id": "A_M01_FAC_001",
            "resource": "data",
            "action": "export",
            "decision": "DENY",
            "reason": "scope data:export not granted to agent (no implicit inheritance)",
        }

    monkeypatch.setattr(m01_http, "_post_json", fake_post)
    response = TestClient(create_app()).post(
        "/api/v1/fac/m01/guard",
        json={
            "tenant_id": "HENGJIAN",
            "agent_id": "AG-FAC-001",
            "action_type": "DATA_EXPORT",
            "object_id": "REPORT-001",
        },
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "DENY"
    assert response.json()["approval"] is None
    assert calls == ["http://m01.local/kernel/v1/authorize"]


def test_missing_m01_principal_id_fails_closed(monkeypatch):
    _configure(monkeypatch)
    monkeypatch.setattr(
        m13_http,
        "_fetch_json",
        lambda *args, **kwargs: _m13_payload(m01_agent_id=None),
    )
    response = TestClient(create_app()).post(
        "/api/v1/fac/m01/guard",
        json={
            "tenant_id": "HENGJIAN",
            "agent_id": "AG-FAC-001",
            "action_type": FinanceGuardAction.TASK_EXECUTE.value,
            "object_id": "TASK-001",
        },
    )
    assert response.status_code == 502
    assert "no M01 principal id" in response.json()["detail"]


def test_guard_fails_closed_when_m01_not_configured(monkeypatch):
    monkeypatch.setenv("FAC_M13_REGISTRY_URL", "http://m13.local")
    monkeypatch.setenv("FAC_M13_REGISTRY_SECRET", "m13-secret")
    monkeypatch.setenv("FAC_M01_KERNEL_URL", "")
    monkeypatch.setenv("FAC_M01_ACCESS_TOKEN", "")
    response = TestClient(create_app()).post(
        "/api/v1/fac/m01/guard",
        json={
            "tenant_id": "HENGJIAN",
            "agent_id": "AG-FAC-001",
            "object_id": "TASK-001",
        },
    )
    assert response.status_code == 503
