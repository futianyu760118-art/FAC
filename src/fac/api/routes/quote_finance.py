"""Quote finance API endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from fac.adapters.m13.http import (
    HttpM13RegistryAdapter,
    M13RegistryConfigurationError,
    M13RegistryError,
    M13RuntimeSnapshot,
)
from fac.domain.m13_agents import FAC_AGENT_REGISTRY_V1, FinanceAgentRegistration
from fac.domain.quote_finance import QuoteFinanceInput, QuoteFinanceResult, calculate_quote_finance
from fac.infrastructure.db import get_session
from fac.infrastructure.models import CalculationRun, CalculationSnapshot
from fac.infrastructure.repositories import CoreRepository, RevisionConflict
from fac.settings import get_settings

router = APIRouter(prefix="/api/v1/fac", tags=["FAC Finance"])


class QuoteFinanceRunRequest(BaseModel):
    tenant_id: str
    revision: int = Field(ge=1)
    evidence_ids: list[str] = Field(min_length=1)
    input: QuoteFinanceInput


class QuoteFinanceRecalcRequest(QuoteFinanceRunRequest):
    base_revision: int = Field(ge=1)


class QuoteFinanceRunResponse(BaseModel):
    object_id: str
    revision: int
    calculation_created: bool
    snapshot_created: bool
    result: QuoteFinanceResult


class RecalculationRequirementView(BaseModel):
    event_id: str
    inquiry_id: str
    revision: int
    trigger_event_id: str
    trigger_event_type: str
    changed_object: dict[str, Any]
    status: str


def _record_quote(
    payload: QuoteFinanceRunRequest,
    session: Session,
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
    calculation_created = repo.add(
        CalculationRun, payload.tenant_id, object_id, "M09", payload.revision, run_payload
    )
    snapshot_created = repo.add(
        CalculationSnapshot,
        payload.tenant_id,
        object_id,
        "M09",
        payload.revision,
        snapshot_payload,
    )
    return QuoteFinanceRunResponse(
        object_id=object_id,
        revision=payload.revision,
        calculation_created=calculation_created,
        snapshot_created=snapshot_created,
        result=result,
    )


@router.post("/quote-finance/calculate", response_model=QuoteFinanceResult)
def calculate_quote(payload: QuoteFinanceInput) -> QuoteFinanceResult:
    return calculate_quote_finance(payload)


@router.post("/quote-finance/calculate-and-record", response_model=QuoteFinanceRunResponse)
def calculate_and_record_quote(
    payload: QuoteFinanceRunRequest,
    session: Annotated[Session, Depends(get_session)],
) -> QuoteFinanceRunResponse:
    try:
        response = _record_quote(payload, session)
        session.commit()
        return response
    except RevisionConflict as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/quote-finance/recalculate", response_model=QuoteFinanceRunResponse)
def recalculate_quote(
    payload: QuoteFinanceRecalcRequest,
    session: Annotated[Session, Depends(get_session)],
) -> QuoteFinanceRunResponse:
    object_id = f"{payload.input.inquiry_id}:{payload.input.quote_version}"
    repo = CoreRepository(session)
    base = repo.get(CalculationRun, payload.tenant_id, object_id, "M09", payload.base_revision)
    if base is None:
        raise HTTPException(status_code=404, detail="base calculation revision not found")
    if payload.revision <= payload.base_revision:
        raise HTTPException(status_code=422, detail="new revision must be greater than base revision")
    try:
        response = _record_quote(payload, session)
        session.commit()
        return response
    except RevisionConflict as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "/quote-finance/recalculation-requirements/{inquiry_id}",
    response_model=list[RecalculationRequirementView],
)
def list_recalculation_requirements(
    inquiry_id: str,
    tenant_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> list[RecalculationRequirementView]:
    records = CoreRepository(session).list_events(
        tenant_id=tenant_id,
        object_id=inquiry_id,
        source_system="M09",
    )
    result = []
    for record in records:
        if record.payload.get("event_type") != "QuoteRecalculationRequired":
            continue
        requirement = record.payload["payload"]
        result.append(
            RecalculationRequirementView(
                event_id=record.event_id,
                inquiry_id=inquiry_id,
                revision=record.revision,
                trigger_event_id=requirement["trigger_event_id"],
                trigger_event_type=requirement["trigger_event_type"],
                changed_object=requirement["changed_object"],
                status=requirement["status"],
            )
        )
    return result


@router.get("/m13/finance-agents", response_model=list[FinanceAgentRegistration])
def list_finance_agents() -> list[FinanceAgentRegistration]:
    """M09 professional catalog; this is not the runtime source of truth."""
    return list(FAC_AGENT_REGISTRY_V1)


@router.get("/m13/finance-agents/runtime", response_model=M13RuntimeSnapshot)
def list_live_finance_agents() -> M13RuntimeSnapshot:
    """Read runtime eligibility from M13; fail closed when registry is unavailable."""
    settings = get_settings()
    try:
        adapter = HttpM13RegistryAdapter(
            base_url=settings.m13_registry_url,
            key_id=settings.m13_registry_key_id,
            secret=settings.m13_registry_secret,
            timeout=settings.m13_registry_timeout_seconds,
        )
        return adapter.list_runtime()
    except M13RegistryConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except M13RegistryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
