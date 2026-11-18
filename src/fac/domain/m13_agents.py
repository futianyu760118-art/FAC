"""M13 registry contracts for FAC finance agents."""

from enum import StrEnum

from pydantic import BaseModel, Field


class AgentStatus(StrEnum):
    DRAFT = "DRAFT"
    TESTING = "TESTING"
    PUBLISHED = "PUBLISHED"
    DISABLED = "DISABLED"


class AutonomyLevel(StrEnum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"


class FinanceAgentRegistration(BaseModel):
    agent_id: str
    name_zh: str
    owning_system: str = "M09"
    registry_system: str = "M13"
    professional_domain: str
    owner_role: str
    skill_ids: list[str] = Field(default_factory=list)
    autonomy_level: AutonomyLevel
    status: AgentStatus
    guard_policy: str = "M01"
    evidence_policy: str = "M02"


FAC_AGENT_REGISTRY_V1: tuple[FinanceAgentRegistration, ...] = (
    FinanceAgentRegistration(agent_id="AG-FAC-001", name_zh="财务总监智能体", professional_domain="综合财经", owner_role="财务总监", skill_ids=["finance_review_pack", "finance_opportunity"], autonomy_level=AutonomyLevel.A1, status=AgentStatus.PUBLISHED),
    FinanceAgentRegistration(agent_id="AG-FAC-002", name_zh="收入智能体", professional_domain="收入", owner_role="财务", skill_ids=["revenue_variance"], autonomy_level=AutonomyLevel.A1, status=AgentStatus.TESTING),
    FinanceAgentRegistration(agent_id="AG-FAC-003", name_zh="成本智能体", professional_domain="成本", owner_role="成本会计", skill_ids=["quote_cost_calc", "quote_actual_variance"], autonomy_level=AutonomyLevel.A2, status=AgentStatus.PUBLISHED),
    FinanceAgentRegistration(agent_id="AG-FAC-004", name_zh="毛利智能体", professional_domain="毛利", owner_role="财务", skill_ids=["order_margin_calc", "order_economic_assessment"], autonomy_level=AutonomyLevel.A2, status=AgentStatus.PUBLISHED),
    FinanceAgentRegistration(agent_id="AG-FAC-005", name_zh="应收智能体", professional_domain="应收", owner_role="主办会计", skill_ids=["ar_aging", "dso_calc"], autonomy_level=AutonomyLevel.A2, status=AgentStatus.TESTING),
    FinanceAgentRegistration(agent_id="AG-FAC-006", name_zh="资金智能体", professional_domain="资金", owner_role="财务总监", skill_ids=["cash_7_30_90"], autonomy_level=AutonomyLevel.A2, status=AgentStatus.TESTING),
    FinanceAgentRegistration(agent_id="AG-FAC-007", name_zh="预算智能体", professional_domain="预算", owner_role="财务总监", skill_ids=["budget_actual_variance"], autonomy_level=AutonomyLevel.A1, status=AgentStatus.TESTING),
    FinanceAgentRegistration(agent_id="AG-FAC-008", name_zh="ROI智能体", professional_domain="投入产出", owner_role="财务总监", skill_ids=["project_roi"], autonomy_level=AutonomyLevel.A1, status=AgentStatus.TESTING),
    FinanceAgentRegistration(agent_id="AG-FAC-009", name_zh="财务风险与机会智能体", professional_domain="风险机会", owner_role="财务总监", skill_ids=["finance_opportunity"], autonomy_level=AutonomyLevel.A1, status=AgentStatus.TESTING),
    FinanceAgentRegistration(agent_id="AG-FAC-010", name_zh="财经复盘智能体", professional_domain="复盘", owner_role="财务总监", skill_ids=["finance_review_pack"], autonomy_level=AutonomyLevel.A2, status=AgentStatus.TESTING),
)
