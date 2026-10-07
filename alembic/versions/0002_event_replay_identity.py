"""Persist tenant-scoped event replay identity.

Revision ID: 0002_event_replay_identity
Revises: 0001_fac_core
"""

import json

import sqlalchemy as sa

from alembic import op

revision = "0002_event_replay_identity"
down_revision = "0001_fac_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_records_v2",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("object_id", sa.String(256), nullable=False),
        sa.Column("source_system", sa.String(128), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_id", sa.String(256), nullable=False),
        sa.Column("idempotency_key", sa.String(256), nullable=False),
        sa.UniqueConstraint("tenant_id", "event_id"),
        sa.UniqueConstraint("tenant_id", "idempotency_key"),
    )
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT * FROM event_records")).mappings()
    for row in rows:
        payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
        event_id = payload.get("event_id") if isinstance(payload, dict) else None
        key = payload.get("idempotency_key") if isinstance(payload, dict) else None
        connection.execute(
            sa.text("""
            INSERT INTO event_records_v2
                (id, tenant_id, object_id, source_system, revision, payload,
                 created_at, updated_at, event_id, idempotency_key)
            VALUES
                (:id, :tenant_id, :object_id, :source_system, :revision, :payload,
                 :created_at, :updated_at, :event_id, :idempotency_key)
        """),
            {
                "id": row["id"],
                "tenant_id": row["tenant_id"],
                "object_id": row["object_id"],
                "source_system": row["source_system"],
                "revision": row["revision"],
                "payload": row["payload"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "event_id": event_id
                if isinstance(event_id, str) and event_id
                else f"legacy-event-{row['id']}",
                "idempotency_key": key
                if isinstance(key, str) and key
                else f"legacy-key-{row['id']}",
            },
        )
    op.drop_index("ix_event_records_tenant_id", table_name="event_records")
    op.drop_table("event_records")
    op.rename_table("event_records_v2", "event_records")
    op.create_index("ix_event_records_tenant_id", "event_records", ["tenant_id"])


def downgrade() -> None:
    raise NotImplementedError("event identity cannot be safely removed")
