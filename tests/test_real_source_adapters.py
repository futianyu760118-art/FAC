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


def test_real_crm_and_plm_events_resolve_bom_to_submitted_inquiry():
    client = TestClient(create_app(_factory()))
    now = datetime.now(UTC).isoformat()
    crm = {
        "tenant_id": "HENGJIAN",
        "ingress_system": "M02",
        "event": {
            "contract_version": "AEOS.Event.V1",
            "event_id": "CRM-EVT-001",
            "event_type": "inquiry.upserted",
            "source_system": "CRM",
            "object_type": "Inquiry",
            "object_id": "7ecb53aa-c26a-4f28-a8c7-111111111111",
            "operation": "UPSERT",
            "occurred_at": now,
            "trace_id": "TRACE-CRM-001",
            "payload": {
                "serial_number": "INQ-2026-0088",
                "status": "SUBMITTED",
                "customer_name": "Northstar Tools",
                "items": [
                    {
                        "internal_model": "WL6000",
                        "product_name": "Rechargeable Work Light",
                        "quantity": "8000",
                    }
                ],
            },
            "idempotency_key": "EBMS:inquiry.upserted:7ecb53aa:test",
        },
    }
    crm_result = client.post("/api/v1/fac/integration/m02/crm-aeos-event", json=crm)
    assert crm_result.status_code == 200
    assert crm_result.json()["event_type"] == "InquirySubmitted"

    plm = {
        "tenant_id": "HENGJIAN",
        "ingress_system": "M02",
        "event_id": "PLM-EVT-BOM-013",
        "event": {
            "eventType": "BOMReleased",
            "objectType": "BOM",
            "objectId": "BOM-WL6000-R13",
            "occurredAt": now,
            "sourceSystem": "PLM2",
            "correlationId": "PLM-BOM-WL6000",
            "version": 13,
            "evidenceRefs": ["PLM-EV-BOM-R13"],
            "payload": {
                "rootPartNo": "WL6000",
                "bomNo": "BOM-WL6000",
                "versionNo": "R13",
                "status": "RELEASED",
            },
        },
    }
    plm_result = client.post("/api/v1/fac/integration/m02/plm-event", json=plm)
    assert plm_result.status_code == 200
    body = plm_result.json()
    assert body["event_type"] == "BOMReleased"
    assert body["affected_inquiries"] == ["INQ-2026-0088"]
    assert len(body["requirement_event_ids"]) == 1
    assert body["requirement_event_ids"][0].endswith(":INQ-2026-0088")


def test_native_adapters_cannot_bypass_m02():
    client = TestClient(create_app(_factory()))
    now = datetime.now(UTC).isoformat()
    crm = {
        "tenant_id": "HENGJIAN",
        "ingress_system": "M05",
        "event": {
            "contract_version": "AEOS.Event.V1",
            "event_id": "CRM-EVT-002",
            "event_type": "inquiry.upserted",
            "source_system": "CRM",
            "object_type": "Inquiry",
            "object_id": "x",
            "operation": "UPSERT",
            "occurred_at": now,
            "trace_id": "t",
            "payload": {"serial_number": "INQ-X", "status": "SUBMITTED"},
        },
    }
    assert client.post("/api/v1/fac/integration/m02/crm-aeos-event", json=crm).status_code == 422


def test_draft_crm_inquiry_does_not_enter_submitted_resolution_pool():
    client = TestClient(create_app(_factory()))
    now = datetime.now(UTC).isoformat()
    crm = {
        "tenant_id": "HENGJIAN",
        "event": {
            "contract_version": "AEOS.Event.V1",
            "event_id": "CRM-EVT-DRAFT",
            "event_type": "inquiry.upserted",
            "source_system": "CRM",
            "object_type": "Inquiry",
            "object_id": "draft-id",
            "operation": "UPSERT",
            "occurred_at": now,
            "trace_id": "trace-draft",
            "payload": {
                "serial_number": "INQ-DRAFT",
                "status": "DRAFT",
                "items": [{"internal_model": "WL6000"}],
            },
        },
    }
    assert client.post("/api/v1/fac/integration/m02/crm-aeos-event", json=crm).status_code == 200

    plm = {
        "tenant_id": "HENGJIAN",
        "event_id": "PLM-EVT-BOM-DRAFT-CHECK",
        "event": {
            "eventType": "BOMReleased",
            "objectType": "BOM",
            "objectId": "BOM-WL6000-R14",
            "occurredAt": now,
            "version": 14,
            "payload": {"rootPartNo": "WL6000"},
        },
    }
    result = client.post("/api/v1/fac/integration/m02/plm-event", json=plm)
    assert result.status_code == 200
    assert result.json()["affected_inquiries"] == []
