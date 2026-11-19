"""Formal FAC product routes independent from the development Demo routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from fac.api.fac_page import render_fac_page
from fac.contracts.fac import FacCalculationRequest
from fac.infrastructure.db import get_session
from fac.infrastructure.models import (
    CalculationResult,
    CalculationRun,
    EdpProjection,
    EventRecord,
    Evidence,
    ExternalRequest,
    FinancePeriod,
    FinanceRule,
)
from fac.modules.fac.service import FacService
from fac.settings import get_settings

router = APIRouter(tags=["FAC"])


@router.get("/fac", response_class=HTMLResponse)
def fac_page() -> str:
    """Render the formal M09 FAC workbench entry point."""
    return render_fac_page()


@router.get("/api/v1/fac/overview")
def fac_overview() -> dict[str, object]:
    """Return formal runtime readiness without requiring Demo initialization."""
    settings = get_settings()
    return {
        "service": "fac",
        "status": "ready",
        "environment": settings.environment,
        "demo_enabled": settings.demo_enabled,
    }


@router.get("/api/v1/fac/integration")
def fac_workbench_projection(
    session: Annotated[Session, Depends(get_session)],
    tenant_id: str | None = Query(default=None),
) -> dict[str, object]:
    """Return a formal workbench projection without claiming external completion."""
    tenant = _tenant(tenant_id)
    orders = session.scalars(
        select(EdpProjection).where(
            EdpProjection.tenant_id == tenant,
            EdpProjection.object_type == "Order",
        )
    ).all()
    events = session.scalars(
        select(EventRecord)
        .where(EventRecord.tenant_id == tenant)
        .order_by(EventRecord.id)
    ).all()
    external_requests = session.scalars(
        select(ExternalRequest)
        .where(ExternalRequest.tenant_id == tenant)
        .order_by(ExternalRequest.id)
    ).all()
    results = session.scalars(
        select(CalculationResult)
        .where(CalculationResult.tenant_id == tenant)
        .order_by(CalculationResult.id)
    ).all()
    latest_result = results[-1] if results else None
    result_evidence_refs = tuple(latest_result.payload.get("evidence_refs", ())) if latest_result else ()
    result_evidence = {
        row.object_id
        for row in session.scalars(
            select(Evidence).where(
                Evidence.tenant_id == tenant,
                Evidence.object_id.in_(result_evidence_refs),
            )
        ).all()
    }
    evidence_verified = bool(result_evidence_refs) and set(result_evidence_refs) <= result_evidence
    order_status = "READY" if orders else "WAITING_EXTERNAL"
    fac_status = "WAITING_EVIDENCE" if latest_result else ("WAITING" if orders else "WAITING_EXTERNAL")
    return {
        "mode": "FORMAL",
        "correlation_id": orders[0].object_id if orders else "待接入订单",
        "idempotency_enabled": True,
        "verify": {
            "status": "VERIFIED" if evidence_verified else "WAITING_EVIDENCE",
            "evidence_coverage": 100 if evidence_verified else 0,
            "value_ledger_id": latest_result.object_id if evidence_verified else "待生成",
            "roi_value": "待验证" if not evidence_verified else "待接入 EBMS",
        },
        "ebms_status": "WAITING_EXTERNAL",
        "stages": [
            {
                "module": "M02 EDP",
                "name": "订单对象",
                "mode": "FORMAL",
                "input_refs": [row.object_id for row in orders],
                "output_refs": [],
                "status": order_status,
            },
            {
                "module": "M09 FAC",
                "name": "订单财经计算",
                "mode": "FORMAL",
                "input_refs": [row.object_id for row in orders],
                "output_refs": [latest_result.object_id] if latest_result else [],
                "status": fac_status,
            },
            {
                "module": "M13 Agent",
                "name": "智能体建议",
                "mode": "INTERFACE_READY",
                "input_refs": [],
                "output_refs": [],
                "status": "WAITING_EXTERNAL",
            },
            {
                "module": "M01 Guard",
                "name": "策略决策",
                "mode": "INTERFACE_READY",
                "input_refs": [],
                "output_refs": [],
                "status": "WAITING",
            },
            {
                "module": "M10 POMS",
                "name": "动作下发",
                "mode": "INTERFACE_READY",
                "input_refs": [],
                "output_refs": [],
                "status": "WAITING_EXTERNAL",
            },
            {
                "module": "FAC Verify",
                "name": "证据验证",
                "mode": "FORMAL",
                "input_refs": [],
                "output_refs": [],
                "status": "WAITING_EVIDENCE",
            },
        ],
        "event_ledger": [
            {
                "event_id": row.event_id,
                "event_type": row.payload.get("event_type", "FinanceCalculationRequested"),
                "source": row.source_system,
                "target": "M09 FAC",
                "correlation_id": row.object_id,
                "idempotency_key": row.idempotency_key,
                "status": "ACKED",
            }
            for row in events
        ],
        "agents": [],
        "decision_cases": [],
        "actions": [],
        "external_requests": [
            {"target_system": row.target_system, "status": row.status}
            for row in external_requests
        ],
    }


def _tenant(value: str | None) -> str:
    tenant_id = value or get_settings().tenant_id
    if not tenant_id.strip():
        raise HTTPException(status_code=400, detail="tenant_id is required")
    return tenant_id


def _same_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    host = request.headers.get("host")
    if origin and host and origin.split("//", 1)[-1] != host:
        raise HTTPException(status_code=403, detail="cross-origin FAC write is not allowed")


@router.get("/api/v1/fac/orders")
def list_orders(
    session: Annotated[Session, Depends(get_session)],
    tenant_id: str | None = Query(default=None),
) -> list[dict[str, object]]:
    tenant = _tenant(tenant_id)
    rows = session.scalars(
        select(EdpProjection)
        .where(EdpProjection.tenant_id == tenant, EdpProjection.object_type == "Order")
        .order_by(EdpProjection.id)
    ).all()
    projections = session.scalars(
        select(EdpProjection).where(EdpProjection.tenant_id == tenant).order_by(EdpProjection.id)
    ).all()

    def input_refs(order: EdpProjection) -> list[dict[str, object]]:
        product_id = order.payload.get("product_id")
        boms = [
            row
            for row in projections
            if row.object_type == "BOM" and row.payload.get("product_id") == product_id
        ]
        material_ids = {
            line.get("material_id")
            for bom in boms
            for line in bom.payload.get("lines", [])
            if line.get("material_id")
        }
        selected = [order, *boms]
        selected.extend(
            row
            for row in projections
            if row.object_type == "MaterialPrice"
            and row.payload.get("material_id") in material_ids
        )
        selected.extend(
            row
            for row in projections
            if row.object_type in {"Labor", "Expense"}
            and row.payload.get("product_id") == product_id
        )
        selected.extend(row for row in projections if row.object_type == "FX")
        return [
            {
                "object_type": row.object_type,
                "object_id": row.object_id,
                "source_system": row.source_system,
                "revision": row.revision,
            }
            for row in selected
        ]

    return [
        {
            "tenant_id": row.tenant_id,
            "order_id": row.object_id,
            "source_system": row.source_system,
            "revision": row.revision,
            "payload": row.payload,
            "input_refs": input_refs(row),
        }
        for row in rows
    ]


@router.get("/api/v1/fac/rules")
def list_rules(
    session: Annotated[Session, Depends(get_session)],
    tenant_id: str | None = Query(default=None),
) -> list[dict[str, object]]:
    tenant = _tenant(tenant_id)
    return [
        {
            "tenant_id": row.tenant_id,
            "rule_id": row.rule_id,
            "version": row.version,
            "rule_name": row.rule_name,
            "status": row.status,
            "effective_from": row.effective_from,
            "effective_to": row.effective_to,
            "owner": row.owner,
            "approval_status": row.approval_status,
            "source_fields": row.source_fields,
            "evidence_required": row.evidence_required,
        }
        for row in session.scalars(
            select(FinanceRule)
            .where(FinanceRule.tenant_id == tenant)
            .order_by(FinanceRule.rule_id, FinanceRule.version)
        ).all()
    ]


@router.get("/api/v1/fac/periods")
def list_periods(
    session: Annotated[Session, Depends(get_session)],
    tenant_id: str | None = Query(default=None),
) -> list[dict[str, object]]:
    tenant = _tenant(tenant_id)
    return [
        {
            "tenant_id": row.tenant_id,
            "period_id": row.period_id,
            "functional_currency": row.functional_currency,
            "status": row.status,
            "closed_at": row.closed_at,
        }
        for row in session.scalars(
            select(FinancePeriod)
            .where(FinancePeriod.tenant_id == tenant)
            .order_by(FinancePeriod.period_id)
        ).all()
    ]


@router.get("/api/v1/fac/events")
def list_events(
    session: Annotated[Session, Depends(get_session)],
    tenant_id: str | None = Query(default=None),
) -> list[dict[str, object]]:
    tenant = _tenant(tenant_id)
    return [
        {
            "tenant_id": row.tenant_id,
            "event_id": row.event_id,
            "idempotency_key": row.idempotency_key,
            "object_id": row.object_id,
            "source_system": row.source_system,
            "revision": row.revision,
            "payload": row.payload,
        }
        for row in session.scalars(
            select(EventRecord).where(EventRecord.tenant_id == tenant).order_by(EventRecord.id)
        ).all()
    ]


@router.get("/api/v1/fac/external-requests")
def list_external_requests(
    session: Annotated[Session, Depends(get_session)],
    tenant_id: str | None = Query(default=None),
) -> list[dict[str, object]]:
    tenant = _tenant(tenant_id)
    return [
        {
            "tenant_id": row.tenant_id,
            "request_id": row.request_id,
            "correlation_id": row.correlation_id,
            "target_system": row.target_system,
            "request_type": row.request_type,
            "idempotency_key": row.idempotency_key,
            "status": row.status,
            "attempts": row.attempts,
            "last_error": row.last_error,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in session.scalars(
            select(ExternalRequest)
            .where(ExternalRequest.tenant_id == tenant)
            .order_by(ExternalRequest.id)
        ).all()
    ]


@router.post("/api/v1/fac/orders/{order_id}/calculations")
def calculate_order(
    order_id: str,
    request: FacCalculationRequest,
    http_request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, object]:
    _same_origin(http_request)
    if request.order_id != order_id:
        raise HTTPException(status_code=400, detail="order_id does not match request")
    try:
        result = FacService(session, request.tenant_id).calculate_order(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "CALCULATED", "result": result}


@router.get("/api/v1/fac/calculations/{calculation_id}")
def get_calculation(
    calculation_id: str,
    session: Annotated[Session, Depends(get_session)],
    tenant_id: str | None = Query(default=None),
) -> dict[str, object]:
    row = session.scalar(
        select(CalculationRun).where(
            CalculationRun.tenant_id == _tenant(tenant_id),
            CalculationRun.object_id == calculation_id,
            CalculationRun.source_system == "fac",
        )
    )
    if row is None:
        raise HTTPException(status_code=404, detail="calculation not found")
    return {"id": row.object_id, "version": row.revision, "payload": row.payload}


@router.get("/api/v1/fac/results/{result_id}/evidence")
def get_result_evidence(
    result_id: str,
    session: Annotated[Session, Depends(get_session)],
    tenant_id: str | None = Query(default=None),
) -> dict[str, object]:
    tenant = _tenant(tenant_id)
    row = session.scalar(
        select(CalculationResult).where(
            CalculationResult.tenant_id == tenant,
            CalculationResult.object_id == result_id,
            CalculationResult.source_system == "fac",
        )
    )
    if row is None:
        raise HTTPException(status_code=404, detail="finance result not found")
    evidence_refs = tuple(row.payload.get("evidence_refs", ()))
    evidence_rows = session.scalars(
        select(Evidence).where(
            Evidence.tenant_id == tenant,
            Evidence.object_id.in_(evidence_refs),
        )
    ).all()
    evidence_ids = {item.object_id for item in evidence_rows}
    evidence_verified = bool(evidence_refs) and set(evidence_refs) <= evidence_ids
    return {
        "result_id": result_id,
        "evidence_refs": evidence_refs,
        "evidence_coverage": 100 if evidence_verified else 0,
        "status": "VERIFIED" if evidence_verified else "WAITING_EVIDENCE",
    }
