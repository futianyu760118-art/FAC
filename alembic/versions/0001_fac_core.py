"""Initial FAC core and EDP projection tables.

Revision ID: 0001_fac_core
Revises:
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_fac_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name in (
        "edp_projections",
        "calculation_runs",
        "calculation_snapshots",
        "evidence",
        "event_records",
    ):
        columns = [
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("tenant_id", sa.String(128), nullable=False),
            sa.Column("object_id", sa.String(256), nullable=False),
            sa.Column("source_system", sa.String(128), nullable=False),
            sa.Column("revision", sa.Integer(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        ]
        if name == "edp_projections":
            columns.append(sa.Column("object_type", sa.String(64), nullable=False))
            unique = ("tenant_id", "object_type", "object_id", "source_system", "revision")
        else:
            unique = ("tenant_id", "object_id", "source_system", "revision")
        op.create_table(name, *columns, sa.UniqueConstraint(*unique))
        op.create_index(f"ix_{name}_tenant_id", name, ["tenant_id"])


def downgrade() -> None:
    for name in reversed(
        (
            "edp_projections",
            "calculation_runs",
            "calculation_snapshots",
            "evidence",
            "event_records",
        )
    ):
        op.drop_index(f"ix_{name}_tenant_id", table_name=name)
        op.drop_table(name)
