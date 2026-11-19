"""Feature-gated local FAC demo routes."""

from typing import Annotated
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from fac.api.demo_page import render_demo_page
from fac.contracts.demo import (
    DemoResetResponse,
    DemoStateResponse,
    DemoTriggerRequest,
    DemoTriggerResponse,
)
from fac.infrastructure.db import get_session
from fac.modules.demo.service import DemoService

router = APIRouter(tags=["FAC Demo"])


@router.get("/demo/fac", response_class=HTMLResponse)
def demo_page() -> str:
    return render_demo_page()


@router.post("/api/v1/demo/reset", response_model=DemoResetResponse)
def reset_demo(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> DemoResetResponse:
    origin = request.headers.get("origin")
    host = request.headers.get("host")
    if origin and urlsplit(origin).netloc != host:
        raise HTTPException(status_code=403, detail="cross-origin Demo reset is not allowed")
    return DemoService(session).reset()


@router.get("/api/v1/demo/state", response_model=DemoStateResponse)
def demo_state(session: Annotated[Session, Depends(get_session)]) -> DemoStateResponse:
    state = DemoService(session).state()
    if not state.input_refs:
        raise HTTPException(status_code=404, detail="Demo has not been initialized")
    return state


@router.post(
    "/api/v1/demo/events/quote-recalculation", response_model=DemoTriggerResponse
)
def trigger_quote_recalculation(
    request: DemoTriggerRequest,
    session: Annotated[Session, Depends(get_session)],
) -> DemoTriggerResponse:
    try:
        return DemoService(session).trigger(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/v1/demo/replay", response_model=DemoTriggerResponse)
def replay_demo_event(
    request: DemoTriggerRequest,
    session: Annotated[Session, Depends(get_session)],
) -> DemoTriggerResponse:
    try:
        return DemoService(session).replay(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
