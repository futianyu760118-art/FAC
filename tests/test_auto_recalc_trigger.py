from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fac.infrastructure.models import Base
from fac.main import create_app


def _factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _event(event_id: str, event_type: str, source_system: str = "M04"):
    return {
        "tenant_id": "HENGJIAN",
        "ingress_system": "M02",
        "event_id": event_id,
        "event_type": event_type,
        "version": 1,
        "object_ref": {
            "object_type": "BOM" if event_type == "BOMReleased" else "ProductConfiguration",
            "object_id": "BOM-WL6000-R13",
            "source_system": source_system,
            "revision": 13,
        },
        "occurred_at": datetime.now(UTC).isoformat(),
        "actor_id": source_system,
        "correlation_id": "INQ-2026-0088",
        "causation_id": "EVT-ROOT-0088",
        "trace_id": "TRACE-0088",
        "payload_version": 1,
        "payload": {"bom_id": "BOM-WL6000-R13"},
        "evidence_refs": [],
    }


def test_m04_bom_event_automatically_creates_quote_recalculation_requirement():
    client = TestClient(create_app(_factory()))
    body = _event("EVT-BOM-R13", "BOMReleased")

    first = client.post("/api/v1/fac/integration/edp-events", json=body)
    assert first.status_code == 200
    assert first.json()["recalculation_required"] is True
    assert first.json()["requirement_created"] is True
    assert first.json()["requirement_event_id"] == "FAC-QUOTE-RECALC:EVT-BOM-R13"

    duplicate = client.post("/api/v1/fac/integration/edp-events", json=body)
    assert duplicate.status_code == 200
    assert duplicate.json()["created"] is False
    assert duplicate.json()["requirement_created"] is False

    requirements = client.get(
        "/api/v1/fac/quote-finance/recalculation-requirements/INQ-2026-0088",
        params={"tenant_id": "HENGJIAN"},
    )
    assert requirements.status_code == 200
    items = requirements.json()
    assert len(items) == 1
    assert items[0]["trigger_event_type"] == "BOMReleased"
    assert items[0]["status"] == "OPEN"


def test_non_m04_quote_driver_event_does_not_create_recalculation_requirement():
    client = TestClient(create_app(_factory()))
    body = _event("EVT-INQ-NEW", "InquiryCreated", source_system="M05")

    response = client.post("/api/v1/fac/integration/edp-events", json=body)
    assert response.status_code == 200
    assert response.json()["recalculation_required"] is False
    assert response.json()["requirement_event_id"] is None
