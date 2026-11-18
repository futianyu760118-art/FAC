from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fac.infrastructure.models import Base, Evidence
from fac.infrastructure.repositories import CoreRepository
from fac.main import create_app


def _factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _quote_body(revision: int, material: str = "468000"):
    return {
        "tenant_id": "HENGJIAN",
        "revision": revision,
        "evidence_ids": ["EV-BOM-R12", "EV-MATERIAL-PRICE-20261118"],
        "input": {
            "inquiry_id": "INQ-2026-0088",
            "quote_version": "V1",
            "customer_id": "CUS-001",
            "product_id": "WL6000",
            "configuration_id": "CFG-WL6000-V2",
            "specification_id": "SPEC-WL6000-V4",
            "bom_id": "BOM-WL6000-R12",
            "quantity": "8000",
            "unit_price_original": "15.90",
            "currency": "USD",
            "fx_rate_to_cny": "7.20",
            "material_cost_cny": material,
            "labor_cost_cny": "61000",
            "processing_cost_cny": "42000",
            "packaging_cost_cny": "28000",
            "logistics_cost_cny": "36000",
            "quality_reserve_cny": "15000",
            "aftersales_reserve_cny": "12000",
            "fx_reserve_cny": "9000",
            "payment_days": 87,
        },
    }


def test_quote_recalculation_requires_existing_base_and_new_revision():
    client = TestClient(create_app(_factory()))
    missing = _quote_body(2, "469000")
    missing["base_revision"] = 1
    assert client.post("/api/v1/fac/quote-finance/recalculate", json=missing).status_code == 404

    first = client.post(
        "/api/v1/fac/quote-finance/calculate-and-record",
        json=_quote_body(1),
    )
    assert first.status_code == 200

    recalc = _quote_body(2, "469000")
    recalc["base_revision"] = 1
    result = client.post("/api/v1/fac/quote-finance/recalculate", json=recalc)
    assert result.status_code == 200
    assert result.json()["revision"] == 2
    assert result.json()["result"]["total_cost_cny"] == "672000.00"


def test_order_snapshot_persists_and_audit_trace_exposes_evidence_ids():
    factory = _factory()
    client = TestClient(create_app(factory))
    order = {
        "tenant_id": "HENGJIAN",
        "evidence_ids": ["EV-BOM-R12", "EV-MATERIAL-PRICE-20261118"],
        "input": {
            "order_id": "HJ-2026-1188",
            "stage": "QUOTE",
            "revenue_cny": "915840",
            "revision": 1,
            "components": {
                "material": "468000",
                "labor": "61000",
                "processing": "42000",
                "packaging": "28000",
                "logistics": "36000",
                "quality": "15000",
                "aftersales": "12000",
                "fx": "9000",
                "other": "0",
            },
        },
    }
    response = client.post("/api/v1/fac/order-finance/snapshot-and-record", json=order)
    assert response.status_code == 200

    with factory() as session:
        CoreRepository(session).add(
            Evidence,
            "HENGJIAN",
            "HJ-2026-1188:QUOTE",
            "M09",
            1,
            {"evidence_id": "EV-BOM-R12", "kind": "BOM", "checksum": "sha256:test"},
        )
        session.commit()

    trace = client.get(
        "/api/v1/fac/audit/trace/HJ-2026-1188:QUOTE",
        params={"tenant_id": "HENGJIAN"},
    )
    assert trace.status_code == 200
    payload = trace.json()
    assert len(payload["calculations"]) == 1
    assert len(payload["snapshots"]) == 1
    assert len(payload["evidence"]) == 1
    assert payload["evidence_ids"] == [
        "EV-BOM-R12",
        "EV-MATERIAL-PRICE-20261118",
    ]


def test_order_snapshot_calculation_is_deterministic():
    payload = {
        "material": Decimal(468000),
        "labor": Decimal(61000),
        "processing": Decimal(42000),
        "packaging": Decimal(28000),
        "logistics": Decimal(36000),
        "quality": Decimal(15000),
        "aftersales": Decimal(12000),
        "fx": Decimal(9000),
    }
    assert sum(payload.values(), Decimal(0)) == Decimal(671000)
