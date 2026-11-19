"""Seed and run the local FAC finance demo through real domain services."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from fac.contracts.common import ObjectRef
from fac.contracts.demo import (
    DemoResetResponse,
    DemoStateResponse,
    DemoTriggerRequest,
    DemoTriggerResponse,
)
from fac.contracts.events import EventEnvelope
from fac.contracts.ofa import CalculationResponse, PlanCostResponse
from fac.infrastructure.models import (
    CalculationResult,
    CalculationRun,
    CalculationSnapshot,
    EdpProjection,
    EventRecord,
    Evidence,
)
from fac.infrastructure.repositories import CoreRepository, EdpRepository
from fac.modules.calculation.service import CalculationService
from fac.modules.ofa.engine import OFAEngine
from fac.modules.ofa.ports import EdpOFAPorts

DEMO_TENANT_ID = "demo-tenant"
DEMO_SOURCE_SYSTEM = "demo-edp"
DEMO_ORDER_ID = "ORD-1001"
DEMO_OCCURRED_AT = datetime(2026, 11, 19, tzinfo=UTC)


class DemoService:
    """Own the fixed, tenant-isolated scenario used by the browser Demo."""

    def __init__(self, session: Session):
        self.session = session

    def reset(self) -> DemoResetResponse:
        for model in (
            EdpProjection,
            CalculationRun,
            CalculationSnapshot,
            CalculationResult,
            Evidence,
            EventRecord,
        ):
            self.session.execute(delete(model).where(model.tenant_id == DEMO_TENANT_ID))
        repository = EdpRepository(self.session)
        seeded = self._seed(repository)
        self.session.commit()
        return DemoResetResponse(tenant_id=DEMO_TENANT_ID, seeded_refs=tuple(seeded))

    def trigger(self, request: DemoTriggerRequest) -> DemoTriggerResponse:
        if request.order_id != DEMO_ORDER_ID:
            raise ValueError(f"unknown Demo order: {request.order_id}")
        refs = self._refs_for_price(request.price_revision)
        event = EventEnvelope(
            event_id=request.event_id,
            event_type=request.trigger_type,
            version=1,
            object_ref=refs[0],
            source_system="fac-demo",
            occurred_at=DEMO_OCCURRED_AT,
            actor_id=request.actor,
            correlation_id=f"demo-correlation-{request.event_id}",
            causation_id=f"demo-causation-{request.event_id}",
            trace_id=f"demo-trace-{request.event_id}",
            payload_version=1,
            payload={
                "order_id": request.order_id,
                "price_revision": request.price_revision,
                "reason": request.reason,
            },
            evidence_refs=[],
            idempotency_key=request.idempotency_key,
        )
        inserted = CoreRepository(self.session).add_event(DEMO_TENANT_ID, event)
        context = CalculationService(self.session, DEMO_TENANT_ID).start(
            "Order",
            DEMO_ORDER_ID,
            refs,
            "v1",
            request.trigger_type,
            request.reason,
            request.actor,
        )
        ports = EdpOFAPorts(self.session, DEMO_TENANT_ID)
        result = OFAEngine(self.session).calculate_plan_cost(
            ports.get_order(refs[0], context), ports, context
        )
        return DemoTriggerResponse(
            replayed=not inserted,
            event_id=request.event_id,
            calculation=CalculationResponse.from_context(context),
            result=PlanCostResponse.from_result(result),
        )

    def state(self) -> DemoStateResponse:
        calculation_service = CalculationService(self.session, DEMO_TENANT_ID)
        runs = self.session.scalars(
            select(CalculationRun)
            .where(
                CalculationRun.tenant_id == DEMO_TENANT_ID,
                CalculationRun.source_system == "fac",
            )
            .order_by(CalculationRun.revision)
        ).all()
        contexts = tuple(
            calculation_service.get("Order", DEMO_ORDER_ID, run.revision)
            for run in runs
        )
        contexts = tuple(context for context in contexts if context is not None)
        results = tuple(
            PlanCostResponse.from_result(OFAEngine(self.session).get_result(context))
            for context in contexts
        )
        events = tuple(
            self._event_data(event)
            for event in self.session.scalars(
                select(EventRecord)
                .where(EventRecord.tenant_id == DEMO_TENANT_ID)
                .order_by(EventRecord.id)
            ).all()
        )
        latest_refs = contexts[-1].input_refs if contexts else ()
        return DemoStateResponse(
            tenant_id=DEMO_TENANT_ID,
            input_refs=latest_refs,
            events=events,
            calculations=tuple(CalculationResponse.from_context(context) for context in contexts),
            results=results,
        )

    @staticmethod
    def _seed(repository: EdpRepository) -> list[ObjectRef]:
        refs = [
            ObjectRef("Order", DEMO_ORDER_ID, DEMO_SOURCE_SYSTEM, 1),
            ObjectRef("BOM", "BOM-1001", DEMO_SOURCE_SYSTEM, 1),
            ObjectRef("MaterialPrice", "PRICE-1001", DEMO_SOURCE_SYSTEM, 1),
            ObjectRef("MaterialPrice", "PRICE-1001", DEMO_SOURCE_SYSTEM, 2),
            ObjectRef("Labor", "LABOR-1001", DEMO_SOURCE_SYSTEM, 1),
            ObjectRef("Expense", "EXPENSE-1001", DEMO_SOURCE_SYSTEM, 1),
        ]
        payloads = [
            {
                "object_id": DEMO_ORDER_ID,
                "product_id": "PROD-1001",
                "quantity": "2",
                "order_date": "2026-10-07",
                "functional_currency": "CNY",
            },
            {
                "product_id": "PROD-1001",
                "lines": [{"material_id": "STEEL-1001", "quantity": "3", "uom": "kg"}],
            },
            {
                "material_id": "STEEL-1001",
                "unit_price": {"amount": "4", "currency": "CNY"},
                "uom": "kg",
                "effective_at": "2026-01-01",
            },
            {
                "material_id": "STEEL-1001",
                "unit_price": {"amount": "5", "currency": "CNY"},
                "uom": "kg",
                "effective_at": "2026-10-07",
            },
            {
                "product_id": "PROD-1001",
                "hours_per_unit": "2",
                "hourly_rate": {"amount": "5", "currency": "CNY"},
            },
            {
                "product_id": "PROD-1001",
                "expense_per_unit": {"amount": "1", "currency": "CNY"},
            },
        ]
        for ref, payload in zip(refs, payloads, strict=True):
            repository.add(DEMO_TENANT_ID, ref, payload)
        return refs

    @staticmethod
    def _refs_for_price(price_revision: int) -> list[ObjectRef]:
        if price_revision not in (1, 2):
            raise ValueError("Demo price_revision must be 1 or 2")
        return [
            ObjectRef("Order", DEMO_ORDER_ID, DEMO_SOURCE_SYSTEM, 1),
            ObjectRef("BOM", "BOM-1001", DEMO_SOURCE_SYSTEM, 1),
            ObjectRef("MaterialPrice", "PRICE-1001", DEMO_SOURCE_SYSTEM, price_revision),
            ObjectRef("Labor", "LABOR-1001", DEMO_SOURCE_SYSTEM, 1),
            ObjectRef("Expense", "EXPENSE-1001", DEMO_SOURCE_SYSTEM, 1),
        ]

    @staticmethod
    def _event_data(event: EventRecord) -> dict[str, Any]:
        payload = event.payload
        object_ref = payload.get("object_ref", {})
        return {
            "event_id": event.event_id,
            "event_type": payload.get("event_type"),
            "idempotency_key": event.idempotency_key,
            "object_ref": {
                "object_type": object_ref.get("object_type", "Order"),
                "object_id": event.object_id,
                "source_system": event.source_system,
                "revision": event.revision,
            },
            "payload": payload.get("payload", payload),
        }
