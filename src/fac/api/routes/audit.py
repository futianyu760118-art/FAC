"""Traceable FAC calculation and evidence views."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fac.infrastructure.db import get_session
from fac.infrastructure.models import CalculationRun, CalculationSnapshot, Evidence
from fac.infrastructure.repositories import CoreRepository

router = APIRouter(prefix="/api/v1/fac/audit", tags=["FAC Audit"])


class RevisionView(BaseModel):
    revision: int
    payload: dict[str, Any]


class FinanceTraceResponse(BaseModel):
    object_id: str
    source_system: str
    calculations: list[RevisionView]
    snapshots: list[RevisionView]
    evidence: list[RevisionView]
    evidence_ids: list[str]


@router.get("/trace/{object_id}", response_model=FinanceTraceResponse)
def trace(
    object_id: str,
    tenant_id: str,
    session: Annotated[Session, Depends(get_session)],
    source_system: str = "M09",
) -> FinanceTraceResponse:
    repo = CoreRepository(session)
    calculations = repo.list_revisions(
        CalculationRun, tenant_id, object_id, source_system
    )
    snapshots = repo.list_revisions(
        CalculationSnapshot, tenant_id, object_id, source_system
    )
    evidence = repo.list_revisions(Evidence, tenant_id, object_id, source_system)
    evidence_ids = sorted(
        {
            evidence_id
            for record in [*calculations, *snapshots]
            for evidence_id in record.payload.get("evidence_ids", [])
        }
    )
    return FinanceTraceResponse(
        object_id=object_id,
        source_system=source_system,
        calculations=[
            RevisionView(revision=item.revision, payload=item.payload)
            for item in calculations
        ],
        snapshots=[
            RevisionView(revision=item.revision, payload=item.payload)
            for item in snapshots
        ],
        evidence=[
            RevisionView(revision=item.revision, payload=item.payload)
            for item in evidence
        ],
        evidence_ids=evidence_ids,
    )
