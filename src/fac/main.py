"""FAC FastAPI application factory."""

from fastapi import FastAPI

from fac.api.routes.health import router as health_router
from fac.settings import get_settings


def create_app() -> FastAPI:
    """Construct the service without opening external connections."""
    app = FastAPI(title="FAC")
    app.state.settings = get_settings()
    app.include_router(health_router)
    return app
