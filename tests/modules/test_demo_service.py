import importlib
from decimal import Decimal

from sqlalchemy import select

from fac.contracts.common import ObjectRef
from fac.contracts.demo import DemoTriggerRequest
from fac.infrastructure.db import make_engine, make_session_factory
from fac.infrastructure.models import (
    Base,
    CalculationResult,
    CalculationRun,
    EventRecord,
)
from fac.infrastructure.repositories import EdpRepository
from fac.modules.calculation.service import CalculationService


def _demo_service(session):
    try:
        spec = importlib.util.find_spec("fac.modules.demo.service")
    except ModuleNotFoundError:
        spec = None
    assert spec is not None
    return importlib.import_module("fac.modules.demo.service").DemoService(session)


def _session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'demo.db'}")
    Base.metadata.create_all(engine)
    return make_session_factory(engine)()


def _request(price_revision, event_id, key, reason):
    return DemoTriggerRequest(
        order_id="ORD-1001",
        price_revision=price_revision,
        event_id=event_id,
        idempotency_key=key,
        trigger_type="QuoteRecalculationRequired",
        reason=reason,
        actor="demo-user",
    )


def test_reset_seeds_demo_objects_without_touching_other_tenants(tmp_path):
    with _session(tmp_path) as session:
        other_ref = ObjectRef("Order", "ORD-OTHER", "other-edp", 1)
        EdpRepository(session).add("other-tenant", other_ref, {"state": "keep"})
        session.commit()

        response = _demo_service(session).reset()

        assert response.tenant_id == "demo-tenant"
        assert len(response.seeded_refs) == 6
        assert EdpRepository(session).get("other-tenant", other_ref).payload == {"state": "keep"}


def test_demo_calculation_recalculation_and_replay_are_versioned_and_idempotent(tmp_path):
    with _session(tmp_path) as session:
        service = _demo_service(session)
        service.reset()

        first = service.trigger(_request(1, "demo-event-v1", "demo-key-v1", "Initial quote"))
        second = service.trigger(
            _request(2, "demo-event-v2", "demo-key-v2", "MaterialPriceRevision")
        )
        replay = service.trigger(
            _request(2, "demo-event-v2", "demo-key-v2", "MaterialPriceRevision")
        )

        assert first.replayed is False
        assert first.result.total_cost.functional_amount == Decimal("46.00")
        assert first.calculation.version == 1
        assert second.replayed is False
        assert second.result.total_cost.functional_amount == Decimal("52.00")
        assert second.calculation.version == 2
        assert second.result.previous_result_id == first.result.result_id
        assert replay.replayed is True
        assert replay.result.result_id == second.result.result_id

        assert session.scalars(select(EventRecord)).all().__len__() == 2
        assert session.scalars(select(CalculationRun)).all().__len__() == 2
        assert session.scalars(select(CalculationResult)).all().__len__() == 2

        state = service.state()
        assert len(state.calculations) == 2
        assert len(state.results) == 2
        assert state.results[0].total_cost.functional_amount == Decimal("46.00")
        assert state.events[0]["object_ref"]["object_type"] == "Order"


def test_demo_state_tolerates_a_run_without_a_persisted_result(tmp_path):
    with _session(tmp_path) as session:
        service = _demo_service(session)
        service.reset()
        CalculationService(session, "demo-tenant").start(
            "Order",
            "ORD-1001",
            service._refs_for_price(1),
            "v1",
            "QuoteRecalculationRequired",
            "Interrupted before result persistence",
            "demo-user",
        )

        state = service.state()

        assert len(state.calculations) == 1
        assert state.results == (None,)


def test_integration_state_exposes_complete_workflow_and_guarded_payment(tmp_path):
    with _session(tmp_path) as session:
        service = _demo_service(session)
        service.reset()

        waiting = service.integration_state()
        assert waiting.correlation_id == "FAC-DEMO-2025-01"
        assert [stage.module for stage in waiting.stages] == [
            "M02 EDP",
            "M09 FAC",
            "M13 Agent",
            "M01 Guard",
            "M10 POMS",
            "FAC Verify",
            "EBMS",
        ]
        assert all(stage.status == "WAITING" for stage in waiting.stages)

        service.trigger(_request(1, "demo-event-v1", "demo-key-v1", "Initial quote"))
        after_v1 = service.integration_state()
        assert after_v1.stage("M02 EDP").status == "COMPLETED"
        assert after_v1.stage("M09 FAC").status == "COMPLETED"
        assert after_v1.stage("M13 Agent").status == "READY"
        assert after_v1.stage("M01 Guard").status == "WAITING"

        service.trigger(
            _request(2, "demo-event-v2", "demo-key-v2", "MaterialPriceRevision")
        )
        completed = service.integration_state()
        assert all(stage.status == "COMPLETED" for stage in completed.stages)
        assert any(agent.dispatchable for agent in completed.agents)
        assert any(case.status == "BLOCKED" for case in completed.decision_cases)
        assert any(action.status == "COMPLETED" for action in completed.actions)
        assert completed.verify.status == "VERIFIED"
        assert completed.verify.evidence_coverage == 100
        assert completed.ebms_status == "CONSUMED"
