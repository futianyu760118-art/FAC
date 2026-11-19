"""Formal FAC orchestration over EDP-backed OFA calculations."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from fac.contracts.events import EventEnvelope
from fac.contracts.fac import FacCalculationRequest
from fac.contracts.ofa import PlanCostResponse
from fac.infrastructure.repositories import CoreRepository, EdpRepository
from fac.modules.calculation.service import CalculationService
from fac.modules.ofa.engine import OFAEngine
from fac.modules.ofa.ports import EdpOFAPorts


class FacService:
    """Own formal FAC calculation orchestration for one tenant."""

    def __init__(self, session: Session, tenant_id: str):
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")
        self.session = session
        self.tenant_id = tenant_id

    def calculate_order(self, request: FacCalculationRequest) -> PlanCostResponse:
        if request.tenant_id != self.tenant_id:
            raise ValueError("request tenant does not match the FAC service tenant")
        order_ref = next(
            (ref for ref in request.input_refs if ref.object_type == "Order"), None
        )
        if order_ref is None or order_ref.object_id != request.order_id:
            raise ValueError("request must contain the requested Order EDP reference")
        if EdpRepository(self.session).get(self.tenant_id, order_ref) is None:
            raise ValueError(f"missing EDP reference: {order_ref}")

        event_id = request.event_id or f"fac-calculation-{request.idempotency_key}"
        repository = CoreRepository(self.session)
        stored_event = repository.get_event_by_id(self.tenant_id, event_id)
        if stored_event is not None:
            stored_payload = stored_event.payload.get("payload", {})
            expected_payload = {
                "order_id": request.order_id,
                "period_id": request.period_id,
                "rule_id": request.rule_id,
                "rule_version": request.rule_version,
                "reason": request.reason,
            }
            if stored_event.idempotency_key != request.idempotency_key or stored_payload != expected_payload:
                raise ValueError("event identity conflict")
            event_type = stored_event.payload.get("event_type", request.trigger_type)
        else:
            event = EventEnvelope(
                event_id=event_id,
                event_type=request.trigger_type,
                version=1,
                object_ref=order_ref,
                source_system="fac",
                occurred_at=datetime.now(UTC),
                actor_id=request.actor,
                correlation_id=f"fac-correlation-{request.idempotency_key}",
                causation_id=f"fac-causation-{request.idempotency_key}",
                trace_id=f"fac-trace-{request.idempotency_key}",
                payload_version=1,
                payload={
                    "order_id": request.order_id,
                    "period_id": request.period_id,
                    "rule_id": request.rule_id,
                    "rule_version": request.rule_version,
                    "reason": request.reason,
                },
                evidence_refs=[],
                idempotency_key=request.idempotency_key,
            )
            repository.add_event(self.tenant_id, event)
            event_type = event.event_type
        context = CalculationService(self.session, self.tenant_id).start(
            "Order",
            request.order_id,
            list(request.input_refs),
            request.rule_version,
            event_type,
            request.reason,
            request.actor,
        )
        ports = EdpOFAPorts(self.session, self.tenant_id)
        result = OFAEngine(self.session).calculate_plan_cost(
            ports.get_order(order_ref, context), ports, context
        )
        self.session.commit()
        return PlanCostResponse.from_result(result)

    def replay(self, request: FacCalculationRequest) -> PlanCostResponse:
        event_id = request.event_id or f"fac-calculation-{request.idempotency_key}"
        event = CoreRepository(self.session).get_event_by_id(self.tenant_id, event_id)
        if event is None:
            raise LookupError(f"FAC calculation event not found: {event_id}")
        if event.idempotency_key != request.idempotency_key:
            raise ValueError("FAC replay identity does not match the stored event")
        return self.calculate_order(request)
