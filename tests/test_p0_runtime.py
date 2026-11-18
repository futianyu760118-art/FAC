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
from fac.infrastructure.models import Base, CalculationRun, CalculationSnapshot
from fac.infrastructure.repositories import CoreRepository, RevisionConflict
from fac.main import create_app


def _components(material: str, quality: str = "15000", logistics: str = "36000"):
    return OrderCostComponents(
        material=Decimal(material),
        labor=Decimal("61000"),
        processing=Decimal("42000"),
        packaging=Decimal("28000"),
        logistics=Decimal(logistics),
        quality=Decimal(quality),
        aftersales=Decimal("12000"),
        fx=Decimal("9000"),
    )


def test_order_finance_five_stage_variance():
    payload = OrderFinanceCompareInput(
        baseline=OrderFinanceSnapshotInput(
            order_id="HJ-2026-1188",
            stage=OrderFinanceStage.QUOTE,
            revenue_cny=Decimal("915840"),
            components=_components("468000"),
            revision=1,
        ),
        current=OrderFinanceSnapshotInput(
            order_id="HJ-2026-1188",
            stage=OrderFinanceStage.FORECAST,
            revenue_cny=Decimal("902000"),
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
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
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
            "other": "0"
        }
    }
    response = client.post("/api/v1/fac/order-finance/snapshot", json=payload)
    assert response.status_code == 200
    assert response.json()["total_cost_cny"] == "671000.00"
