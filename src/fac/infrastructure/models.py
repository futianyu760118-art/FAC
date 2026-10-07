"""Tenant and revision scoped FAC tables."""

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String, UniqueConstraint
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
