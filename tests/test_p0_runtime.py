from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fac.domain.order_finance import (
    OrderCostComponents,
    OrderFinanceCompareInput,
    OrderFinanceSnapshotInput,
    OrderFinanceStage,
    compare_order_finance,
)
from fac.infrastructure.models import Base, CalculationRun
from fac.infrastructure.repositories import CoreRepository, RevisionConflict
from fac.main import create_app


def _components(material: str, quality: str = "15000", logistics: str = "36000"):
    return OrderCostComponents(
        material=Decimal(material),
        labor=Decimal(61000),
        processing=Decimal(42000),
        packaging=Decimal(28000),
        logistics=Decimal(logistics),
        quality=Decimal(quality),
        aftersales=Decimal(12000),
        fx=Decimal(9000),
    )


def _factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_order_finance_five_stage_variance():
    payload = OrderFinanceCompareInput(
        baseline=OrderFinanceSnapshotInput(
            order_id="HJ-2026-1188",
            stage=OrderFinanceStage.QUOTE,
            revenue_cny=Decimal(915840),
            components=_components("468000"),
            revision=1,
        ),
        current=OrderFinanceSnapshotInput(
            order_id="HJ-2026-1188",
            stage=OrderFinanceStage.FORECAST,
            revenue_cny=Decimal(902000),
            components=_components("486000", quality="22000", logistics="44000"),
            revision=2,
        ),
    )
    result = compare_order_finance(payload)
    assert result.total_cost_variance_cny == Decimal("33000.00")
    by_component = {item.component: item.variance_cny for item in result.component_variances}
    assert by_component["material"] == Decimal("18000.00")
    assert by_component["quality"] == Decimal("7000.00")
    assert by_component["logistics"] == Decimal("8000.00")


def test_core_repository_is_idempotent_but_rejects_revision_mutation():
    factory = _factory()
    with factory() as session:
        repo = CoreRepository(session)
        payload = {"skill_id": "quote_cost_calc", "result": {"total_cost": "671000.00"}}
        assert repo.add(CalculationRun, "HENGJIAN", "Q-1", "M09", 1, payload) is True
        assert repo.add(CalculationRun, "HENGJIAN", "Q-1", "M09", 1, payload) is False
        try:
            repo.add(
                CalculationRun,
                "HENGJIAN",
                "Q-1",
                "M09",
                1,
                {"skill_id": "quote_cost_calc", "result": {"total_cost": "672000.00"}},
            )
        except RevisionConflict:
            pass
        else:
            raise AssertionError("mutating a frozen revision must raise RevisionConflict")


def test_order_routes_are_registered():
    client = TestClient(create_app())
    payload = {
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
    }
    response = client.post("/api/v1/fac/order-finance/snapshot", json=payload)
    assert response.status_code == 200
    assert response.json()["total_cost_cny"] == "671000.00"


def test_quote_calculation_run_is_persisted_and_idempotent():
    factory = _factory()
    client = TestClient(create_app(factory))
    body = {
        "tenant_id": "HENGJIAN",
        "revision": 1,
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
            "material_cost_cny": "468000",
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

    first = client.post("/api/v1/fac/quote-finance/calculate-and-record", json=body)
    assert first.status_code == 200
    assert first.json()["calculation_created"] is True
    assert first.json()["snapshot_created"] is True

    second = client.post("/api/v1/fac/quote-finance/calculate-and-record", json=body)
    assert second.status_code == 200
    assert second.json()["calculation_created"] is False
    assert second.json()["snapshot_created"] is False

    body["input"]["material_cost_cny"] = "469000"
    conflict = client.post("/api/v1/fac/quote-finance/calculate-and-record", json=body)
    assert conflict.status_code == 409
