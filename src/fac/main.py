"""FAC FastAPI application factory."""

from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from fac.api.routes.health import router as health_router
from fac.api.routes.imports import router as import_router
from fac.infrastructure.db import get_session
from fac.settings import get_settings


def create_app(session_factory: sessionmaker[Session] | None = None) -> FastAPI:
    """Construct the service without opening external connections."""
    app = FastAPI(title="FAC")
    app.state.settings = get_settings()
    app.include_router(health_router)
    app.include_router(import_router)
    if session_factory is not None:

        def test_session():
            with session_factory() as session:
                yield session

        app.dependency_overrides[get_session] = test_session
    return app
