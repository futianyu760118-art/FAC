from pathlib import Path

from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from alembic import command
from fac.infrastructure.db import make_engine, make_session_factory
from fac.main import create_app


def _upgrade() -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "head")


def test_formal_database_can_upgrade_twice_without_demo_seed(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'formal.db'}"
    monkeypatch.setenv("FAC_DATABASE_URL", database_url)

    _upgrade()
    _upgrade()

    engine = make_engine(database_url)
    table_names = set(inspect(engine).get_table_names())
    assert {"finance_rules", "finance_periods", "external_requests"} <= table_names
    response = TestClient(create_app(make_session_factory(engine))).get(
        "/api/v1/fac/orders?tenant_id=tenant-a"
    )
    assert response.status_code == 200
    assert response.json() == []
    assert not any(item.get("order_id") == "ORD-1001" for item in response.json())


def test_container_defaults_are_formal_and_keep_current_migrations():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "FAC_DATABASE_URL=sqlite:////app/data/fac.db" in dockerfile
    assert "FAC_DEMO_ENABLED=false" in dockerfile
    assert "COPY alembic ./alembic" in dockerfile
    assert "-delete" not in dockerfile
