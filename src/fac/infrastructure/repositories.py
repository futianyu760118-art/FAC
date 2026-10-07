"""Queries always include tenant and source revision."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fac.contracts.common import ObjectRef
from fac.infrastructure.models import (
    CalculationRun,
    CalculationSnapshot,
    EdpProjection,
    EventRecord,
    Evidence,
)


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
        if self.get(tenant_id, ref) is not None:
            return False
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


CoreModel = type[CalculationRun] | type[CalculationSnapshot] | type[Evidence] | type[EventRecord]


class CoreRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(
        self, model: CoreModel, tenant_id: str, object_id: str, source_system: str, revision: int
    ):
        return self.session.scalar(
            select(model).where(
                model.tenant_id == tenant_id,
                model.object_id == object_id,
                model.source_system == source_system,
                model.revision == revision,
            )
        )

    def add(
        self,
        model: CoreModel,
        tenant_id: str,
        object_id: str,
        source_system: str,
        revision: int,
        payload: dict,
    ):
        if self.get(model, tenant_id, object_id, source_system, revision) is not None:
            return False
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
