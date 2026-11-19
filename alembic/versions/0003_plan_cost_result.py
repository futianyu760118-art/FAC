"""Store immutable versioned plan-cost results.

Revision ID: 0003_plan_cost_result
Revises: 0002_event_replay_identity
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_plan_cost_result"
down_revision = "0002_event_replay_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "calculation_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("object_id", sa.String(256), nullable=False),
        sa.Column("source_system", sa.String(128), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "object_id", "source_system", "revision"),
    )
    op.create_index("ix_calculation_results_tenant_id", "calculation_results", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_calculation_results_tenant_id", table_name="calculation_results")
    op.drop_table("calculation_results")
