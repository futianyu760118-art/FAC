from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from fac.contracts.common import ObjectRef
from fac.contracts.fac import (
    ExternalRequestResponse,
    FacCalculationRequest,
    FinancePeriodResponse,
    FinanceRuleResponse,
)


def test_formal_calculation_request_requires_edp_refs_and_idempotency_key():
    request = FacCalculationRequest(
        tenant_id="tenant-a",
        order_id="ORD-1001",
        period_id="2026-11",
        rule_id="OFA_PLAN_COST",
        rule_version="v1",
        input_refs=(ObjectRef("Order", "ORD-1001", "m02-edp", 1),),
        actor="user-001",
        idempotency_key="calc-ord-1001-v1",
    )

    assert request.input_refs[0].source_system == "m02-edp"
    assert request.rule_version == "v1"


def test_formal_calculation_request_rejects_empty_input_refs():
    with pytest.raises(ValidationError):
        FacCalculationRequest(
            tenant_id="tenant-a",
            order_id="ORD-1001",
            period_id="2026-11",
            rule_id="OFA_PLAN_COST",
            rule_version="v1",
            input_refs=(),
            actor="user-001",
            idempotency_key="calc-ord-1001-v1",
        )


def test_rule_period_and_external_request_contracts_preserve_governance_fields():
    rule = FinanceRuleResponse(
        tenant_id="tenant-a",
        rule_id="OFA_PLAN_COST",
        version="v1",
        rule_name="订单计划成本",
        status="ACTIVE",
        effective_from=date(2026, 1, 1),
        owner="fac-finance",
        approval_status="APPROVED",
        evidence_required=True,
    )
    period = FinancePeriodResponse(
        tenant_id="tenant-a",
        period_id="2026-11",
        functional_currency="CNY",
        status="OPEN",
    )
    request = ExternalRequestResponse(
        tenant_id="tenant-a",
        request_id="req-001",
        correlation_id="corr-001",
        target_system="M10 POMS",
        request_type="Action",
        idempotency_key="action-001",
        status="WAITING_EXTERNAL",
        attempts=0,
        created_at=datetime.now(timezone.utc),
    )

    assert rule.evidence_required is True
    assert period.status == "OPEN"
    assert request.status == "WAITING_EXTERNAL"
