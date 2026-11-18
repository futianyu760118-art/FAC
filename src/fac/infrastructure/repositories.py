"""Queries always include tenant and source revision."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fac.contracts.common import ObjectRef
from fac.contracts.events import EventEnvelope
from fac.domain.events import _canonical
from fac.infrastructure.models import (
    CalculationRun,
    CalculationSnapshot,
    EdpProjection,
    EventRecord,
    Evidence,
)


class RevisionConflict(ValueError):
    """An existing source revision contains different data."""


class EdpRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, tenant_id: str, ref: ObjectRef) -> EdpProjection | None:
        return self.session.scalar(
            select(EdpProjection).where(
                EdpProjection.tenant_id == tenant_id,
                EdpProjection.object_type == ref.object_type,
                EdpProjection.object_id == ref.object_id,
                EdpProjection.source_system == ref.source_system,
                EdpProjection.revision == ref.revision,
            )
        )

    def add(self, tenant_id: str, ref: ObjectRef, payload: dict) -> bool:
        existing = self.get(tenant_id, ref)
        if existing is not None:
            if existing.payload == payload:
                return False
            raise RevisionConflict(
                f"revision conflict for {ref.object_type}/{ref.object_id}"
                f" from {ref.source_system} revision {ref.revision}"
            )
        self.session.add(
            EdpProjection(
                tenant_id=tenant_id,
                object_type=ref.object_type,
                object_id=ref.object_id,
                source_system=ref.source_system,
                revision=ref.revision,
                payload=payload,
            )
        )
        self.session.flush()
        return True


CoreModel = type[CalculationRun] | type[CalculationSnapshot] | type[Evidence]


class CoreRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(
        self, model: CoreModel, tenant_id: str, object_id: str, source_system: str, revision: int
    ):
        if model is EventRecord:
            raise ValueError("use get_event_by_id for EventRecord")
        return self.session.scalar(
            select(model).where(
                model.tenant_id == tenant_id,
                model.object_id == object_id,
                model.source_system == source_system,
                model.revision == revision,
            )
        )

    def list_revisions(
        self,
        model: CoreModel,
        tenant_id: str,
        object_id: str,
        source_system: str,
    ) -> list:
        if model is EventRecord:
            raise ValueError("use event query methods for EventRecord")
        return list(
            self.session.scalars(
                select(model)
                .where(
                    model.tenant_id == tenant_id,
                    model.object_id == object_id,
                    model.source_system == source_system,
                )
                .order_by(model.revision.asc())
            )
        )

    def latest(
        self,
        model: CoreModel,
        tenant_id: str,
        object_id: str,
        source_system: str,
    ):
        if model is EventRecord:
            raise ValueError("use event query methods for EventRecord")
        return self.session.scalar(
            select(model)
            .where(
                model.tenant_id == tenant_id,
                model.object_id == object_id,
                model.source_system == source_system,
            )
            .order_by(model.revision.desc())
            .limit(1)
        )

    def add(
        self,
        model: CoreModel,
        tenant_id: str,
        object_id: str,
        source_system: str,
        revision: int,
        payload: dict,
    ) -> bool:
        if model is EventRecord:
            raise ValueError("use add_event for EventRecord")
        existing = self.get(model, tenant_id, object_id, source_system, revision)
        if existing is not None:
            if existing.payload == payload:
                return False
            raise RevisionConflict(
                f"revision conflict for {model.__name__}/{object_id}"
                f" from {source_system} revision {revision}"
            )
        self.session.add(
            model(
                tenant_id=tenant_id,
                object_id=object_id,
                source_system=source_system,
                revision=revision,
                payload=payload,
            )
        )
        self.session.flush()
        return True

    def get_event_by_id(self, tenant_id: str, event_id: str) -> EventRecord | None:
        return self.session.scalar(
            select(EventRecord).where(
                EventRecord.tenant_id == tenant_id, EventRecord.event_id == event_id
            )
        )

    def add_event(self, tenant_id: str, envelope: EventEnvelope) -> bool:
        if not isinstance(envelope, EventEnvelope):
            raise TypeError("envelope must be an EventEnvelope")
        by_id = self.get_event_by_id(tenant_id, envelope.event_id)
        by_key = self.session.scalar(
            select(EventRecord).where(
                EventRecord.tenant_id == tenant_id,
                EventRecord.idempotency_key == envelope.idempotency_key,
            )
        )
        canonical = _canonical(envelope)
        if by_id is not None or by_key is not None:
            if by_id is by_key and by_id is not None and by_id.payload == canonical:
                return False
            raise ValueError("event identity conflict")
        ref = envelope.object_ref
        self.session.add(
            EventRecord(
                tenant_id=tenant_id,
                object_id=ref.object_id,
                source_system=ref.source_system,
                revision=ref.revision,
                event_id=envelope.event_id,
                idempotency_key=envelope.idempotency_key,
                payload=canonical,
            )
        )
        self.session.flush()
        return True
