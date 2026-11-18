"""Quote finance API endpoints."""

from fastapi import APIRouter

from fac.domain.m13_agents import FAC_AGENT_REGISTRY_V1, FinanceAgentRegistration
from fac.domain.quote_finance import QuoteFinanceInput, QuoteFinanceResult, calculate_quote_finance

router = APIRouter(prefix="/api/v1/fac", tags=["FAC Finance"])


@router.post("/quote-finance/calculate", response_model=QuoteFinanceResult)
def calculate_quote(payload: QuoteFinanceInput) -> QuoteFinanceResult:
    return calculate_quote_finance(payload)


@router.get("/m13/finance-agents", response_model=list[FinanceAgentRegistration])
def list_finance_agents() -> list[FinanceAgentRegistration]:
    return list(FAC_AGENT_REGISTRY_V1)
