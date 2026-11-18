"""Quote finance API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from fac.domain.m13_agents import FAC_AGENT_REGISTRY_V1, FinanceAgentRegistration
from fac.domain.quote_finance import QuoteFinanceInput, QuoteFinanceResult, calculate_quote_finance
from fac.infrastructure.db import get_session
from fac.infrastructure.models import CalculationRun, CalculationSnapshot
from fac.infrastructure.repositories import CoreRepository, RevisionConflict

router = APIRouter(prefix="/api/v1/fac", tags=["FAC Finance"])


class QuoteFinanceRunRequest(BaseModel):
    tenant_id: str
    revision: int = Field(ge=1)
    evidence_ids: list[str] = Field(min_length=1)
    input: QuoteFinanceInput


class QuoteFinanceRunResponse(BaseModel):
    object_id: str
    revision: int
    calculation_created: bool
    snapshot_created: bool
    result: QuoteFinanceResult


@router.post("/quote-finance/calculate", response_model=QuoteFinanceResult)
def calculate_quote(payload: QuoteFinanceInput) -> QuoteFinanceResult:
    return calculate_quote_finance(payload)


@router.post("/quote-finance/calculate-and-record", response_model=QuoteFinanceRunResponse)
def calculate_and_record_quote(
    payload: QuoteFinanceRunRequest,
    session: Annotated[Session, Depends(get_session)],
) -> QuoteFinanceRunResponse:
    result = calculate_quote_finance(payload.input)
    object_id = f"{payload.input.inquiry_id}:{payload.input.quote_version}"
    run_payload = {
        "skill_id": "quote_cost_calc",
        "skill_version": "1.0",
        "input": payload.input.model_dump(mode="json"),
        "evidence_ids": payload.evidence_ids,
    }
    snapshot_payload = {
        "result_type": "QuoteFinanceResult",
        "result": result.model_dump(mode="json"),
        "evidence_ids": payload.evidence_ids,
    }

    repo = CoreRepository(session)
    try:
        calculation_created = repo.add(
            CalculationRun,
            payload.tenant_id,
            object_id,
            "M09",
            payload.revision,
            run_payload,
        )
        snapshot_created = repo.add(
            CalculationSnapshot,
            payload.tenant_id,
            object_id,
            "M09",
            payload.revision,
            snapshot_payload,
        )
        session.commit()
    except RevisionConflict as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return QuoteFinanceRunResponse(
        object_id=object_id,
        revision=payload.revision,
        calculation_created=calculation_created,
        snapshot_created=snapshot_created,
        result=result,
    )


@router.get("/m13/finance-agents", response_model=list[FinanceAgentRegistration])
def list_finance_agents() -> list[FinanceAgentRegistration]:
    return list(FAC_AGENT_REGISTRY_V1)
