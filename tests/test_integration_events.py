from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fac.adapters.m13.port import AgentNotPublished, LocalM13RegistryAdapter
from fac.infrastructure.models import Base
from fac.main import create_app


def _factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _event(event_id: str = "EVT-001"):
    return {
        "tenant_id": "HENGJIAN",
        "ingress_system": "M02",
        "event_id": event_id,
        "event_type": "ProductConfigurationConfirmed",
        "version": 1,
        "object_ref": {
            "object_type": "ProductConfiguration",
            "object_id": "CFG-WL6000-V2",
            "source_system": "M04",
            "revision": 2,
        },
        "occurred_at": datetime.now(UTC).isoformat(),
        "actor_id": "M04",
        "correlation_id": "INQ-2026-0088",
        "causation_id": "EVT-INQUIRY-0088",
        "trace_id": "TRACE-0088",
        "payload_version": 1,
        "payload": {
            "specification_id": "SPEC-WL6000-V4",
            "bom_id": "BOM-WL6000-R12",
        },
        "evidence_refs": [],
    }


def test_integration_event_is_edp_only_and_idempotent():
    client = TestClient(create_app(_factory()))
    body = _event()
    first = client.post("/api/v1/fac/integration/edp-events", json=body)
    assert first.status_code == 200
    assert first.json()["created"] is True

    second = client.post("/api/v1/fac/integration/edp-events", json=body)
    assert second.status_code == 200
    assert second.json()["created"] is False

    body["ingress_system"] = "M05"
    bypass = client.post("/api/v1/fac/integration/edp-events", json=body)
    assert bypass.status_code == 422


def test_formal_finance_event_requires_evidence():
    client = TestClient(create_app(_factory()))
    body = _event("EVT-FIN-001")
    body["event_type"] = "QuoteFinanceCalculated"
    response = client.post("/api/v1/fac/integration/edp-events", json=body)
    assert response.status_code == 422


def test_m13_adapter_allows_only_published_agents():
    registry = LocalM13RegistryAdapter()
    assert registry.require_published("AG-FAC-001").name_zh == "财务总监智能体"

    try:
        registry.require_published("AG-FAC-005")
    except AgentNotPublished:
        pass
    else:
        raise AssertionError("testing agents must not be callable as published agents")
