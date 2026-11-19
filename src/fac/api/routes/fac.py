"""Formal FAC product routes independent from the development Demo routes."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from fac.api.fac_page import render_fac_page
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
