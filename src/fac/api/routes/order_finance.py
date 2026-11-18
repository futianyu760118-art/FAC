"""Order finance API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fac.domain.order_finance import (
    OrderFinanceCompareInput,
    OrderFinanceCompareResult,
    OrderFinanceSnapshotInput,
    OrderFinanceSnapshotResult,
    calculate_snapshot,
    compare_order_finance,
)
from fac.infrastructure.db import get_session
from fac.infrastructure.models import CalculationRun, CalculationSnapshot
from fac.infrastructure.repositories import CoreRepository, RevisionConflict

router = APIRouter(prefix="/api/v1/fac/order-finance", tags=["FAC Order Finance"])


class OrderSnapshotRecordRequest(BaseModel):
    tenant_id: str
    evidence_ids: list[str]
    input: OrderFinanceSnapshotInput


class OrderSnapshotRecordResponse(BaseModel):
    object_id: str
    revision: int
    calculation_created: bool
    snapshot_created: bool
    result: OrderFinanceSnapshotResult


@router.post("/snapshot", response_model=OrderFinanceSnapshotResult)
def snapshot(payload: OrderFinanceSnapshotInput) -> OrderFinanceSnapshotResult:
    return calculate_snapshot(payload)


@router.post("/snapshot-and-record", response_model=OrderSnapshotRecordResponse)
def snapshot_and_record(
    payload: OrderSnapshotRecordRequest,
    session: Annotated[Session, Depends(get_session)],
) -> OrderSnapshotRecordResponse:
    if not payload.evidence_ids:
        raise HTTPException(status_code=422, detail="formal order finance snapshot requires evidence")
    result = calculate_snapshot(payload.input)
    object_id = f"{payload.input.order_id}:{payload.input.stage.value}"
    run_payload = {
        "skill_id": "order_margin_calc",
        "skill_version": "1.0",
        "input": payload.input.model_dump(mode="json"),
        "evidence_ids": payload.evidence_ids,
    }
    snapshot_payload = {
        "result_type": "OrderFinanceSnapshotResult",
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
            payload.input.revision,
            run_payload,
        )
        snapshot_created = repo.add(
            CalculationSnapshot,
            payload.tenant_id,
            object_id,
            "M09",
            payload.input.revision,
            snapshot_payload,
        )
        session.commit()
    except RevisionConflict as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return OrderSnapshotRecordResponse(
        object_id=object_id,
        revision=payload.input.revision,
        calculation_created=calculation_created,
        snapshot_created=snapshot_created,
        result=result,
    )


@router.post("/compare", response_model=OrderFinanceCompareResult)
def compare(payload: OrderFinanceCompareInput) -> OrderFinanceCompareResult:
    return compare_order_finance(payload)
