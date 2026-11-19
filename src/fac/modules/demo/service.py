"""Seed and run the local FAC finance demo through real domain services."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from fac.contracts.common import ObjectRef
from fac.contracts.demo import (
    DemoActionState,
    DemoAgentState,
    DemoDecisionCaseState,
    DemoIntegrationState,
    DemoResetResponse,
    DemoStageState,
    DemoStateResponse,
    DemoTriggerRequest,
    DemoTriggerResponse,
    DemoVerifyState,
)
from fac.contracts.fac import FacCalculationRequest
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
from fac.modules.fac.service import FacService
from fac.modules.ofa.engine import OFAEngine

DEMO_TENANT_ID = "demo-tenant"
DEMO_SOURCE_SYSTEM = "demo-edp"
DEMO_ORDER_ID = "ORD-1001"
DEMO_OCCURRED_AT = datetime(2026, 11, 19, tzinfo=UTC)
DEMO_CORRELATION_ID = "FAC-DEMO-2025-01"


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
        existing_event = CoreRepository(self.session).get_event_by_id(
            DEMO_TENANT_ID, request.event_id
        )
        result = FacService(self.session, DEMO_TENANT_ID).calculate_order(
            FacCalculationRequest(
                tenant_id=DEMO_TENANT_ID,
                order_id=request.order_id,
                period_id="2026-11",
                rule_id="OFA_PLAN_COST",
                rule_version="v1",
                input_refs=tuple(refs),
                actor=request.actor,
                idempotency_key=request.idempotency_key,
                event_id=request.event_id,
                trigger_type=request.trigger_type,
                reason=request.reason,
            )
        )
        context = CalculationService(self.session, DEMO_TENANT_ID).get(
            "Order", DEMO_ORDER_ID, result.version
        )
        if context is None:
            raise RuntimeError("formal FAC calculation context was not persisted")
        return DemoTriggerResponse(
            replayed=existing_event is not None,
            event_id=request.event_id,
            calculation=CalculationResponse.from_context(context),
            result=result,
        )

    def replay(self, request: DemoTriggerRequest) -> DemoTriggerResponse:
        event = CoreRepository(self.session).get_event_by_id(DEMO_TENANT_ID, request.event_id)
        if event is None:
            raise LookupError(f"Demo event not found: {request.event_id}")
        if event.idempotency_key != request.idempotency_key:
            raise ValueError("Demo replay identity does not match the stored event")
        result = FacService(self.session, DEMO_TENANT_ID).replay(
            FacCalculationRequest(
                tenant_id=DEMO_TENANT_ID,
                order_id=request.order_id,
                period_id="2026-11",
                rule_id="OFA_PLAN_COST",
                rule_version="v1",
                input_refs=tuple(self._refs_for_price(request.price_revision)),
                actor=request.actor,
                idempotency_key=request.idempotency_key,
                event_id=request.event_id,
                trigger_type=request.trigger_type,
                reason=request.reason,
            )
        )
        context = CalculationService(self.session, DEMO_TENANT_ID).get(
            "Order", DEMO_ORDER_ID, result.version
        )
        if context is None:
            raise RuntimeError("formal FAC replay context was not persisted")
        return DemoTriggerResponse(
            replayed=True,
            event_id=request.event_id,
            calculation=CalculationResponse.from_context(context),
            result=result,
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
            (
                PlanCostResponse.from_result(result)
                if (result := OFAEngine(self.session).get_result(context)) is not None
                else None
            )
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
        persisted_refs = tuple(
            ObjectRef(row.object_type, row.object_id, row.source_system, row.revision)
            for row in self.session.scalars(
                select(EdpProjection)
                .where(
                    EdpProjection.tenant_id == DEMO_TENANT_ID,
                    EdpProjection.source_system == DEMO_SOURCE_SYSTEM,
                )
                .order_by(EdpProjection.id)
            ).all()
        )
        latest_refs = contexts[-1].input_refs if contexts else persisted_refs
        return DemoStateResponse(
            tenant_id=DEMO_TENANT_ID,
            input_refs=latest_refs,
            events=events,
            calculations=tuple(CalculationResponse.from_context(context) for context in contexts),
            results=results,
            integration=self.integration_state(),
        )

    def integration_state(self) -> DemoIntegrationState:
        """Build the complete AEOS integration projection from local Demo facts."""
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
            context
            for context in (
                calculation_service.get("Order", DEMO_ORDER_ID, run.revision) for run in runs
            )
            if context is not None
        )
        results = tuple(
            OFAEngine(self.session).get_result(context) for context in contexts
        )
        has_v1 = bool(results and results[0] is not None)
        has_v2 = len(results) > 1 and results[1] is not None
        latest_result = results[-1] if results else None
        result_id = latest_result.result_id if latest_result is not None else None
        result_evidence = tuple(
            evidence.evidence_id
            for evidence in latest_result.evidence_refs
        ) if latest_result is not None else ()

        stages = (
            self._stage(
                "M02 EDP",
                "事实标准化与审计",
                "COMPLETED" if has_v1 else "WAITING",
                ("Object", "Event", "Evidence"),
                ("CalculationRun",) if has_v1 else (),
            ),
            self._stage(
                "M09 FAC",
                "财经计算与判断",
                "COMPLETED" if has_v1 else "WAITING",
                ("CalculationSnapshot", "Rule"),
                ("FinanceResult V2",) if has_v2 else ("FinanceResult V1",) if has_v1 else (),
            ),
            self._stage(
                "M13 Agent",
                "智能体建议与技能注册",
                "COMPLETED" if has_v2 else "READY" if has_v1 else "WAITING",
                ("Agent Registry", "Capability"),
                ("Suggestion",) if has_v2 else (),
            ),
            self._stage(
                "M01 Guard",
                "策略、权限与决策案例",
                "COMPLETED" if has_v2 else "WAITING",
                ("Suggestion", "DecisionCase"),
                ("Policy Decision",) if has_v2 else (),
            ),
            self._stage(
                "M10 POMS",
                "动作下发与执行反馈",
                "COMPLETED" if has_v2 else "WAITING",
                ("DecisionCase", "Action"),
                ("Execution Feedback",) if has_v2 else (),
            ),
            self._stage(
                "FAC Verify",
                "财经结果与证据验证",
                "COMPLETED" if has_v2 else "WAITING",
                ("FinanceResult", "Evidence"),
                ("Value Ledger",) if has_v2 else (),
            ),
            self._stage(
                "EBMS",
                "结果消费与回证",
                "COMPLETED" if has_v2 else "WAITING",
                ("FinanceResult", "Evidence"),
                ("Consumed Result",) if has_v2 else (),
            ),
        )
        agents = (
            DemoAgentState(
                agent_id="agent-cfo-001",
                name="CFO 智能体",
                capabilities=("财经汇总", "财经解释"),
                action_level="A0",
                dispatchable=has_v1,
                status="READY" if has_v1 else "WAITING",
                source="M13 Registry 沙箱",
            ),
            DemoAgentState(
                agent_id="agent-cost-001",
                name="成本智能体",
                capabilities=("计划成本计算", "成本异常识别"),
                action_level="A1",
                dispatchable=has_v1,
                status="READY" if has_v1 else "WAITING",
                source="M13 Registry 沙箱",
            ),
            DemoAgentState(
                agent_id="agent-margin-001",
                name="毛利智能体",
                capabilities=("订单毛利计算", "毛利风险识别"),
                action_level="A1",
                dispatchable=has_v1,
                status="READY" if has_v1 else "WAITING",
                source="M13 Registry 沙箱",
            ),
            DemoAgentState(
                agent_id="agent-ar-001",
                name="应收智能体",
                capabilities=("应收账龄计算", "回款预测"),
                action_level="A1",
                dispatchable=has_v1,
                status="READY" if has_v1 else "WAITING",
                source="M13 Registry 沙箱",
            ),
            DemoAgentState(
                agent_id="agent-payment-001",
                name="付款智能体",
                capabilities=("付款执行", "高风险动作"),
                action_level="A2",
                dispatchable=False,
                status="GUARDED",
                source="M13 Registry 沙箱",
            ),
        )
        decision_cases = (
            DemoDecisionCaseState(
                case_id="DC-OFA-250124-01",
                title="订单 B 毛利率低于底线",
                risk_level="MEDIUM",
                decision="ALLOW" if has_v2 else "PENDING",
                status="APPROVED" if has_v2 else "WAITING",
                maker="毛利智能体",
                checker="订单财经组",
                approver="财经负责人",
                accountable_owner="订单财经组",
                result_id=result_id,
            ),
            DemoDecisionCaseState(
                case_id="DC-PAY-250124-01",
                title="供应商付款建议 #PAY-250124",
                risk_level="HIGH",
                decision="DENY",
                status="BLOCKED" if has_v2 else "WAITING",
                maker="付款智能体",
                checker="资金管理组",
                approver="财务总监",
                accountable_owner="资金管理组",
                result_id=result_id,
            ),
        )
        actions = (
            DemoActionState(
                action_id="POMS-OFA-250124",
                title="复核订单 B 成本构成",
                status="COMPLETED" if has_v2 else "WAITING",
                owner="订单财经组",
                due_date="2026-11-21",
                decision_case_id="DC-OFA-250124-01",
                feedback="执行反馈已回流 FAC" if has_v2 else "等待 Guard 决策",
                evidence_ref="evidence:action:poms-ofa" if has_v2 else None,
            ),
            DemoActionState(
                action_id="POMS-PAY-250124",
                title="确认供应商付款建议",
                status="BLOCKED" if has_v2 else "WAITING",
                owner="资金管理组",
                due_date="2026-11-22",
                decision_case_id="DC-PAY-250124-01",
                feedback="高风险动作已被 Guard 阻断" if has_v2 else "等待 Guard 决策",
                evidence_ref=None,
            ),
        )
        verify = DemoVerifyState(
            status="VERIFIED" if has_v2 else "WAITING",
            status_label="已验证" if has_v2 else "待验证",
            evidence_coverage=100 if has_v2 else 0,
            result_id=result_id,
            roi_value="+12.8%（演示值）" if has_v2 else "待计算",
            value_ledger_id="VL-FAC-250124-01",
            evidence_refs=result_evidence + (("evidence:action:poms-ofa",) if has_v2 else ()),
        )
        return DemoIntegrationState(
            correlation_id=DEMO_CORRELATION_ID,
            idempotency_enabled=True,
            mode="LOCAL_SANDBOX",
            stages=stages,
            agents=agents,
            decision_cases=decision_cases,
            actions=actions,
            verify=verify,
            ebms_status="CONSUMED" if has_v2 else "WAITING",
            event_ledger=self._integration_event_ledger(has_v1, has_v2),
        )

    @staticmethod
    def _stage(
        module: str,
        name: str,
        status: str,
        input_refs: tuple[str, ...],
        output_refs: tuple[str, ...],
    ) -> DemoStageState:
        labels = {
            "WAITING": "待运行",
            "READY": "可调度",
            "COMPLETED": "已完成",
        }
        return DemoStageState(
            module=module,
            name=name,
            status=status,
            status_label=labels.get(status, status),
            mode="沙箱投影" if module not in {"M02 EDP", "M09 FAC"} else "本地真实",
            input_refs=input_refs,
            output_refs=output_refs,
        )

    @staticmethod
    def _integration_event_ledger(has_v1: bool, has_v2: bool) -> tuple[dict[str, Any], ...]:
        return (
            {
                "event_id": "demo-event-v1",
                "event_type": "QuoteRecalculationRequired",
                "source": "CRM",
                "target": "M09 FAC",
                "status": "PROCESSED" if has_v1 else "WAITING",
                "correlation_id": DEMO_CORRELATION_ID,
                "idempotency_key": "demo-key-v1",
            },
            {
                "event_id": "plm-bom-0118",
                "event_type": "BOMReleased",
                "source": "PLM",
                "target": "M02 EDP",
                "status": "ACKED" if has_v1 else "WAITING",
                "correlation_id": "PLM-2025-0118",
                "idempotency_key": "plm-key-0118",
            },
            {
                "event_id": "demo-margin-risk-v2",
                "event_type": "MarginRiskDetected",
                "source": "M09 FAC",
                "target": "M01 Guard",
                "status": "REVIEW" if has_v2 else "WAITING",
                "correlation_id": "RISK-250124-02",
                "idempotency_key": "risk-key-250124-02",
            },
        )

    @staticmethod
    def _seeded_refs() -> list[ObjectRef]:
        return [
            ObjectRef("Order", DEMO_ORDER_ID, DEMO_SOURCE_SYSTEM, 1),
            ObjectRef("BOM", "BOM-1001", DEMO_SOURCE_SYSTEM, 1),
            ObjectRef("MaterialPrice", "PRICE-1001", DEMO_SOURCE_SYSTEM, 1),
            ObjectRef("MaterialPrice", "PRICE-1001", DEMO_SOURCE_SYSTEM, 2),
            ObjectRef("Labor", "LABOR-1001", DEMO_SOURCE_SYSTEM, 1),
            ObjectRef("Expense", "EXPENSE-1001", DEMO_SOURCE_SYSTEM, 1),
        ]

    @staticmethod
    def _seed(repository: EdpRepository) -> list[ObjectRef]:
        refs = DemoService._seeded_refs()
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
            "actor_id": payload.get("actor_id"),
            "object_ref": {
                "object_type": object_ref.get("object_type", "Order"),
                "object_id": event.object_id,
                "source_system": event.source_system,
                "revision": event.revision,
            },
            "payload": payload.get("payload", payload),
        }
