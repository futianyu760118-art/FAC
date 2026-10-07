from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from alembic import command
from fac.contracts.common import ObjectRef
from fac.contracts.events import EventEnvelope
from fac.infrastructure.db import make_engine, make_session_factory
from fac.infrastructure.models import (
    Base,
    CalculationRun,
    CalculationSnapshot,
    EventRecord,
    Evidence,
)
from fac.infrastructure.repositories import CoreRepository, EdpRepository


def test_edp_repository_scopes_revision_and_tenant(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'repo.db'}")
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    with factory() as session:
        repo = EdpRepository(session)
        one = ObjectRef("Order", "O-1", "edp-mock", 1)
        two = ObjectRef("Order", "O-1", "edp-mock", 2)
        assert repo.add("tenant-a", one, {"amount": "100"}) is True
        with pytest.raises(ValueError, match="revision conflict"):
            repo.add("tenant-a", one, {"amount": "999"})
        assert repo.add("tenant-a", two, {"amount": "200"}) is True
        assert repo.get("tenant-a", one).payload["amount"] == "100"
        assert repo.get("tenant-a", two).payload["amount"] == "200"
        assert repo.get("tenant-b", one) is None


def test_core_repository_scopes_records_by_tenant_and_revision(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'core.db'}")
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    with factory() as session:
        repo = CoreRepository(session)
        for model in (CalculationRun, CalculationSnapshot, Evidence):
            repo.add(model, "tenant-a", "record-1", "fac", 1, {"state": "first"})
            repo.add(model, "tenant-a", "record-1", "fac", 2, {"state": "second"})
            assert repo.get(model, "tenant-a", "record-1", "fac", 1).payload == {"state": "first"}
            assert repo.get(model, "tenant-a", "record-1", "fac", 2).payload == {"state": "second"}
            assert repo.get(model, "tenant-b", "record-1", "fac", 1) is None


def _event(event_id="event-1", key="key-1", value=1):
    return EventEnvelope(
        event_id=event_id,
        event_type="OrderImported",
        version=1,
        object_ref=ObjectRef("Order", "ORD-1", "edp-mock", 1),
        source_system="fac",
        occurred_at=datetime(2026, 10, 7, tzinfo=UTC),
        actor_id="actor-1",
        correlation_id="corr-1",
        causation_id="cause-1",
        trace_id="trace-1",
        payload_version=1,
        payload={"value": value},
        evidence_refs=[],
        idempotency_key=key,
    )


def test_event_repository_enforces_tenant_scoped_event_replay_identity(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'events.db'}")
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    with factory() as session:
        repo = CoreRepository(session)
        assert repo.add_event("tenant-a", _event()) is True
        assert repo.add_event("tenant-a", _event()) is False
        with pytest.raises(ValueError, match="event identity conflict"):
            repo.add_event("tenant-a", _event(event_id="event-2", key="key-1"))
        with pytest.raises(ValueError, match="event identity conflict"):
            repo.add_event("tenant-a", _event(event_id="event-1", key="key-2"))
        with pytest.raises(ValueError, match="event identity conflict"):
            repo.add_event("tenant-a", _event(value=999))
        assert repo.add_event("tenant-b", _event()) is True
        assert repo.add_event("tenant-a", _event(event_id="event-2", key="key-2")) is True
        assert repo.get_event_by_id("tenant-a", "event-1").idempotency_key == "key-1"
        assert repo.get_event_by_id("tenant-b", "event-1") is not None
        assert repo.get_event_by_id("tenant-c", "event-1") is None


def test_generic_core_add_cannot_bypass_event_identity(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'bypass.db'}")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session, pytest.raises(ValueError, match="add_event"):
        CoreRepository(session).add(EventRecord, "tenant-a", "ORD-1", "fac", 1, {})


def test_event_database_uniqueness_covers_both_replay_identifiers(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'event_constraints.db'}")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session:
        CoreRepository(session).add_event("tenant-a", _event())
        for event_id, key in (("event-1", "different-key"), ("different-event", "key-1")):
            with pytest.raises(IntegrityError), session.begin_nested():
                session.add(
                    EventRecord(
                        tenant_id="tenant-a",
                        object_id="ORD-2",
                        source_system="edp-mock",
                        revision=2,
                        event_id=event_id,
                        idempotency_key=key,
                        payload={},
                    )
                )
                session.flush()


def test_event_migration_preserves_legacy_row_and_adds_replay_identity(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'legacy.db'}"
    monkeypatch.setenv("FAC_DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.upgrade(config, "0001_fac_core")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text("""
            INSERT INTO event_records
                (tenant_id, object_id, source_system, revision, payload, created_at, updated_at)
            VALUES
                ('tenant-a', 'ORD-1', 'fac', 1, '{"state": "legacy"}',
                 '2026-10-07 00:00:00', '2026-10-07 00:00:00')
        """)
        )
    command.upgrade(config, "head")
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT event_id, idempotency_key, payload FROM event_records WHERE tenant_id='tenant-a'"
            )
        ).one()
    assert row.event_id == "legacy-event-1"
    assert row.idempotency_key == "legacy-key-1"
    assert '"state": "legacy"' in row.payload
    with engine.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(
            text("""
            INSERT INTO event_records
                (tenant_id, object_id, source_system, revision, payload, created_at,
                 updated_at, event_id, idempotency_key)
            VALUES
                ('tenant-a', 'ORD-2', 'fac', 2, '{}', '2026-10-07 00:00:00',
                 '2026-10-07 00:00:00', 'legacy-event-1', 'new-key')
        """)
        )


def test_event_migration_avoids_generated_id_and_key_collisions(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'collision.db'}"
    monkeypatch.setenv("FAC_DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.upgrade(config, "0001_fac_core")
    engine = make_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text("""
            INSERT INTO event_records
                (id, tenant_id, object_id, source_system, revision, payload,
                 created_at, updated_at)
            VALUES
                (1, 'tenant-a', 'ORD-1', 'fac', 1, '{"state": "missing"}',
                 '2026-10-07 00:00:00', '2026-10-07 00:00:00'),
                (2, 'tenant-a', 'ORD-2', 'fac', 1,
                 '{"event_id": "legacy-event-1", "idempotency_key": "legacy-key-1"}',
                 '2026-10-07 00:00:00', '2026-10-07 00:00:00')
        """)
        )
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT id, event_id, idempotency_key FROM event_records ORDER BY id")
        ).all()
    assert [(row.id, row.event_id, row.idempotency_key) for row in rows] == [
        (1, "legacy-event-1-1", "legacy-key-1-1"),
        (2, "legacy-event-1", "legacy-key-1"),
    ]
