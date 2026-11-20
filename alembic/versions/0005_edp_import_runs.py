"""Add real EDP import audit records.

Revision ID: 0005_edp_import_runs
Revises: 0004_fac_product_baseline
"""

import sqlalchemy as sa

from alembic import op

revision = "0005_edp_import_runs"
down_revision = "0004_fac_product_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "edp_import_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("import_id", sa.String(128), nullable=False),
        sa.Column("source", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("requested_order", sa.String(256), nullable=True),
        sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("error", sa.String(1024), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "import_id"),
    )
    op.create_index("ix_edp_import_runs_tenant_id", "edp_import_runs", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_edp_import_runs_tenant_id", table_name="edp_import_runs")
    op.drop_table("edp_import_runs")
