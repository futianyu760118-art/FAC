"""Local fixture import endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fac.adapters.edp_mock.adapter import EdpAdapter
from fac.adapters.edp_mock.models import EdpFixture, ImportReport
from fac.infrastructure.db import get_session

router = APIRouter()


@router.post("/api/v1/import/edp-fixture", response_model=ImportReport)
def import_edp_fixture(
    payload: EdpFixture, session: Annotated[Session, Depends(get_session)]
) -> ImportReport:
    return EdpAdapter(session).import_fixture(payload)
