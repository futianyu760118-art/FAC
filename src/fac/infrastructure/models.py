"""Tenant and revision scoped FAC tables."""

from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, JSON, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class RevisionedRecord:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    object_id: Mapped[str] = mapped_column(String(256), nullable=False)
    source_system: Mapped[str] = mapped_column(String(128), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class EdpProjection(RevisionedRecord, Base):
    __tablename__ = "edp_projections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "object_type", "object_id", "source_system", "revision"),
    )
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)


class CalculationRun(RevisionedRecord, Base):
    __tablename__ = "calculation_runs"
    __table_args__ = (UniqueConstraint("tenant_id", "object_id", "source_system", "revision"),)


class CalculationSnapshot(RevisionedRecord, Base):
    __tablename__ = "calculation_snapshots"
    __table_args__ = (UniqueConstraint("tenant_id", "object_id", "source_system", "revision"),)


class CalculationResult(RevisionedRecord, Base):
    __tablename__ = "calculation_results"
    __table_args__ = (UniqueConstraint("tenant_id", "object_id", "source_system", "revision"),)


class Evidence(RevisionedRecord, Base):
    __tablename__ = "evidence"
    __table_args__ = (UniqueConstraint("tenant_id", "object_id", "source_system", "revision"),)


class EventRecord(RevisionedRecord, Base):
    __tablename__ = "event_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "event_id"),
        UniqueConstraint("tenant_id", "idempotency_key"),
    )
    event_id: Mapped[str] = mapped_column(String(256), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)


class FinanceRule(Base):
    __tablename__ = "finance_rules"
    __table_args__ = (UniqueConstraint("tenant_id", "rule_id", "version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
    approval_status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_fields: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    evidence_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class FinancePeriod(Base):
    __tablename__ = "finance_periods"
    __table_args__ = (UniqueConstraint("tenant_id", "period_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    period_id: Mapped[str] = mapped_column(String(32), nullable=False)
    functional_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class ExternalRequest(Base):
    __tablename__ = "external_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_id"),
        UniqueConstraint("tenant_id", "idempotency_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    request_id: Mapped[str] = mapped_column(String(256), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    target_system: Mapped[str] = mapped_column(String(128), nullable=False)
    request_type: Mapped[str] = mapped_column(String(128), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    last_error: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
