"""Feature-gated local FAC demo routes."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["FAC Demo"])


@router.get("/demo/fac", response_class=HTMLResponse)
def demo_page() -> str:
    return "<html><body><h1>FAC Demo</h1></body></html>"
