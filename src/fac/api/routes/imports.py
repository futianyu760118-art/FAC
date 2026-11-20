"""EDP import endpoints.

The fixture route remains explicit for local contract tests. Production uses the
read-only EDP Tool API route below and records every attempt for audit.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from fac.adapters.edp.adapter import (
    EdpApiAdapter,
    EdpApiError,
    EdpImportReport,
    EdpImportRequest,
)
from fac.adapters.edp_mock.adapter import EdpAdapter
from fac.adapters.edp_mock.models import EdpFixture, ImportReport
from fac.infrastructure.db import get_session
from fac.infrastructure.models import EdpImportRun
from fac.settings import get_settings

router = APIRouter()


@router.post("/api/v1/import/edp-fixture", response_model=ImportReport)
def import_edp_fixture(
    payload: EdpFixture, session: Annotated[Session, Depends(get_session)]
) -> ImportReport:
    return EdpAdapter(session).import_fixture(payload)


@router.get("/api/v1/fac/edp/status")
def edp_status(session: Annotated[Session, Depends(get_session)]) -> dict[str, object]:
    """Show EDP endpoint configuration and the latest import result."""
    settings = get_settings()
    latest = (
        session.query(EdpImportRun)
        .filter(EdpImportRun.tenant_id == settings.tenant_id)
        .order_by(EdpImportRun.id.desc())
        .first()
    )
    return {
        "configured": bool(settings.edp_base_url.strip() and settings.edp_api_key.strip()),
        "base_url": settings.edp_base_url,
        "source_system": settings.edp_source_system,
        "last_import": {
            "import_id": latest.import_id,
            "status": latest.status,
            "accepted_count": latest.accepted_count,
            "skipped_count": latest.skipped_count,
            "rejected_count": latest.rejected_count,
            "started_at": latest.started_at,
            "finished_at": latest.finished_at,
            "error": latest.error,
        }
        if latest
        else None,
    }


@router.post("/api/v1/fac/edp/import", response_model=EdpImportReport)
def import_from_edp(
    payload: EdpImportRequest,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> EdpImportReport:
    """Import governed EDP order facts and related procurement/inventory facts."""
    origin = request.headers.get("origin")
    host = request.headers.get("host")
    if origin and host and origin.split("//", 1)[-1] != host:
        raise HTTPException(status_code=403, detail="cross-origin FAC write is not allowed")
    settings = get_settings()
    tenant_id = payload.tenant_id or settings.tenant_id
    import_id = f"edp-import-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"
    run = EdpImportRun(
        tenant_id=tenant_id,
        import_id=import_id,
        source=settings.edp_source_system,
        status="RUNNING",
        requested_order=payload.order_no,
        payload={"limit": payload.limit},
    )
    session.add(run)
    session.flush()
    try:
        report = EdpApiAdapter(session, settings).import_orders(
            payload.model_copy(update={"tenant_id": tenant_id}), import_id=import_id
        )
    except EdpApiError as exc:
        run.status = "FAILED"
        run.error = str(exc)[:1024]
        run.finished_at = datetime.now(UTC)
        session.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    run.status = report.status
    run.accepted_count = report.accepted_count
    run.skipped_count = report.skipped_count
    run.rejected_count = report.rejected_count
    run.payload = report.model_dump(mode="json")
    run.finished_at = datetime.now(UTC)
    session.commit()
    return report
