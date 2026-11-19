from decimal import Decimal

from sqlalchemy import select

from fac.contracts.common import ObjectRef
from fac.contracts.fac import FacCalculationRequest
from fac.contracts.ofa import PlanCostResponse
from fac.infrastructure.db import make_engine, make_session_factory
from fac.infrastructure.models import Base, CalculationResult, CalculationRun
from fac.infrastructure.repositories import EdpRepository
from fac.modules.fac.service import FacService


def _session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'fac.db'}")
    Base.metadata.create_all(engine)
    return make_session_factory(engine)()


def _refs(price_revision: int) -> tuple[ObjectRef, ...]:
    source = "m02-edp"
    return (
        ObjectRef("Order", "ORD-1001", source, 1),
        ObjectRef("BOM", "BOM-1001", source, 1),
        ObjectRef("MaterialPrice", "PRICE-1001", source, price_revision),
        ObjectRef("Labor", "LABOR-1001", source, 1),
        ObjectRef("Expense", "EXPENSE-1001", source, 1),
    )


def _seed(session):
    repository = EdpRepository(session)
    source = "m02-edp"
    payloads = (
        (ObjectRef("Order", "ORD-1001", source, 1), {
            "object_id": "ORD-1001",
            "product_id": "PROD-1001",
            "quantity": "2",
            "order_date": "2026-10-07",
            "functional_currency": "CNY",
        }),
        (ObjectRef("BOM", "BOM-1001", source, 1), {
            "product_id": "PROD-1001",
            "lines": [{"material_id": "STEEL-1001", "quantity": "3", "uom": "kg"}],
        }),
        (ObjectRef("MaterialPrice", "PRICE-1001", source, 1), {
            "material_id": "STEEL-1001",
            "unit_price": {"amount": "4", "currency": "CNY"},
            "uom": "kg",
            "effective_at": "2026-01-01",
        }),
        (ObjectRef("MaterialPrice", "PRICE-1001", source, 2), {
            "material_id": "STEEL-1001",
            "unit_price": {"amount": "5", "currency": "CNY"},
            "uom": "kg",
            "effective_at": "2026-10-07",
        }),
        (ObjectRef("Labor", "LABOR-1001", source, 1), {
            "product_id": "PROD-1001",
            "hours_per_unit": "2",
            "hourly_rate": {"amount": "5", "currency": "CNY"},
        }),
        (ObjectRef("Expense", "EXPENSE-1001", source, 1), {
            "product_id": "PROD-1001",
            "expense_per_unit": {"amount": "1", "currency": "CNY"},
        }),
    )
    for ref, payload in payloads:
        repository.add("tenant-a", ref, payload)
    session.commit()


def _request(price_revision: int, key: str) -> FacCalculationRequest:
    return FacCalculationRequest(
        tenant_id="tenant-a",
        order_id="ORD-1001",
        period_id="2026-11",
        rule_id="OFA_PLAN_COST",
        rule_version="v1",
        input_refs=_refs(price_revision),
        actor="user-001",
        idempotency_key=key,
    )


def test_formal_fac_service_calculates_immutable_versions_and_replays(tmp_path):
    with _session(tmp_path) as session:
        _seed(session)
        service = FacService(session, "tenant-a")

        first = service.calculate_order(_request(1, "calc-v1"))
        second = service.calculate_order(_request(2, "calc-v2"))
        replay = service.replay(_request(2, "calc-v2"))

        assert isinstance(first, PlanCostResponse)
        assert first.total_cost.functional_amount == Decimal("46.00")
        assert second.total_cost.functional_amount == Decimal("52.00")
        assert second.previous_result_id == first.result_id
        assert replay.result_id == second.result_id
        assert session.scalars(select(CalculationRun)).all().__len__() == 2
        assert session.scalars(select(CalculationResult)).all().__len__() == 2
