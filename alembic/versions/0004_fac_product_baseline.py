"""Add formal FAC governance and external-request tables.

Revision ID: 0004_fac_product_baseline
Revises: 0003_plan_cost_result
"""

import sqlalchemy as sa

from alembic import op

revision = "0004_fac_product_baseline"
down_revision = "0003_plan_cost_result"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "finance_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("rule_id", sa.String(128), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("rule_name", sa.String(256), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("owner", sa.String(128), nullable=False),
        sa.Column("approval_status", sa.String(32), nullable=False),
        sa.Column("source_fields", sa.JSON(), nullable=False),
        sa.Column("evidence_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "rule_id", "version"),
    )
    op.create_index("ix_finance_rules_tenant_id", "finance_rules", ["tenant_id"])
    op.create_table(
        "finance_periods",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("period_id", sa.String(32), nullable=False),
        sa.Column("functional_currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "period_id"),
    )
    op.create_index("ix_finance_periods_tenant_id", "finance_periods", ["tenant_id"])
    op.create_table(
        "external_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(128), nullable=False),
        sa.Column("request_id", sa.String(256), nullable=False),
        sa.Column("correlation_id", sa.String(256), nullable=False),
        sa.Column("target_system", sa.String(128), nullable=False),
        sa.Column("request_type", sa.String(128), nullable=False),
        sa.Column("idempotency_key", sa.String(256), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("last_error", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "request_id"),
        sa.UniqueConstraint("tenant_id", "idempotency_key"),
    )
    op.create_index("ix_external_requests_tenant_id", "external_requests", ["tenant_id"])
    op.create_index("ix_external_requests_correlation_id", "external_requests", ["correlation_id"])


def downgrade() -> None:
    op.drop_index("ix_external_requests_correlation_id", table_name="external_requests")
    op.drop_index("ix_external_requests_tenant_id", table_name="external_requests")
    op.drop_table("external_requests")
    op.drop_index("ix_finance_periods_tenant_id", table_name="finance_periods")
    op.drop_table("finance_periods")
    op.drop_index("ix_finance_rules_tenant_id", table_name="finance_rules")
    op.drop_table("finance_rules")
