from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from fac.infrastructure.db import make_engine, make_session_factory
from fac.infrastructure.models import Base, ExternalRequest, FinancePeriod, FinanceRule


def _session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'formal.db'}")
    Base.metadata.create_all(engine)
    return make_session_factory(engine)()


def test_finance_governance_records_are_tenant_scoped_and_queryable(tmp_path):
    with _session(tmp_path) as session:
        session.add_all(
            [
                FinanceRule(
                    tenant_id="tenant-a",
                    rule_id="OFA_PLAN_COST",
                    version="v1",
                    rule_name="订单计划成本",
                    status="ACTIVE",
                    effective_from=date(2026, 1, 1),
                    owner="fac-finance",
                    approval_status="APPROVED",
                    source_fields=["Order", "BOM", "MaterialPrice"],
                    evidence_required=True,
                ),
                FinancePeriod(
                    tenant_id="tenant-a",
                    period_id="2026-11",
                    functional_currency="CNY",
                    status="OPEN",
                ),
                ExternalRequest(
                    tenant_id="tenant-a",
                    request_id="req-001",
                    correlation_id="corr-001",
                    target_system="M10 POMS",
                    request_type="Action",
                    idempotency_key="action-001",
                    status="WAITING_EXTERNAL",
                    payload={"action": "review"},
                ),
            ]
        )
        session.commit()

        assert session.scalar(
            select(FinanceRule).where(FinanceRule.tenant_id == "tenant-a")
        ).rule_id == "OFA_PLAN_COST"
        assert session.scalar(
            select(FinancePeriod).where(FinancePeriod.tenant_id == "tenant-a")
        ).status == "OPEN"
        assert session.scalar(
            select(ExternalRequest).where(ExternalRequest.tenant_id == "tenant-a")
        ).status == "WAITING_EXTERNAL"
        assert session.scalars(
            select(FinanceRule).where(FinanceRule.tenant_id == "tenant-b")
        ).all() == []


def test_finance_rule_version_and_external_request_key_are_unique_per_tenant(tmp_path):
    with _session(tmp_path) as session:
        session.add(
            FinanceRule(
                tenant_id="tenant-a",
                rule_id="OFA_PLAN_COST",
                version="v1",
                rule_name="订单计划成本",
                status="ACTIVE",
                effective_from=date(2026, 1, 1),
                owner="fac-finance",
                approval_status="APPROVED",
                source_fields=[],
                evidence_required=True,
            )
        )
        session.commit()

        session.add(
            FinanceRule(
                tenant_id="tenant-a",
                rule_id="OFA_PLAN_COST",
                version="v1",
                rule_name="重复规则",
                status="DRAFT",
                effective_from=date(2026, 1, 1),
                owner="fac-finance",
                approval_status="PENDING",
                source_fields=[],
                evidence_required=True,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
