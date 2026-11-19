"""FAC FastAPI application factory."""

from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from fac.api.routes.audit import router as audit_router
from fac.api.routes.health import router as health_router
from fac.api.routes.imports import router as import_router
from fac.api.routes.integration import router as integration_router
from fac.api.routes.m01_guard import router as m01_guard_router
from fac.api.routes.order_finance import router as order_finance_router
from fac.api.routes.quote_finance import router as quote_finance_router
from fac.infrastructure.db import get_session
from fac.settings import get_settings


def create_app(session_factory: sessionmaker[Session] | None = None) -> FastAPI:
    """Construct the service without opening external connections."""
    app = FastAPI(title="FAC")
    app.state.settings = get_settings()
    app.include_router(health_router)
    app.include_router(import_router)
    app.include_router(quote_finance_router)
    app.include_router(order_finance_router)
    app.include_router(integration_router)
    app.include_router(m01_guard_router)
    app.include_router(audit_router)
    if session_factory is not None:

        def test_session():
            with session_factory() as session:
                yield session

        app.dependency_overrides[get_session] = test_session
    return app
