"""Immutable calculation input snapshots and replay-safe run versions."""

import hashlib
import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from fac.contracts.common import ObjectRef
from fac.infrastructure.models import CalculationRun, CalculationSnapshot
from fac.infrastructure.repositories import CoreRepository, EdpRepository

EdpObjectRef = ObjectRef


@dataclass(frozen=True)
class CalculationContext:
    tenant_id: str
    subject_type: str
    subject_id: str
    version: int
    calculation_id: str
    snapshot_id: str
    input_refs: tuple[EdpObjectRef, ...]
    rule_set_version: str
    checksum: str
    trigger_type: str
    reason: str
    actor: str


class CalculationService:
    def __init__(self, session: Session, tenant_id: str):
        if not tenant_id.strip():
            raise ValueError("tenant_id is required")
        self.session = session
        self.tenant_id = tenant_id

    def start(
        self,
        subject_type: str,
        subject_id: str,
        input_refs: list[EdpObjectRef],
        rule_set_version: str,
        trigger_type: str,
        reason: str,
        actor: str,
    ) -> CalculationContext:
        if not all((subject_type, subject_id, rule_set_version, trigger_type, reason, actor)):
            raise ValueError("calculation identity and audit fields are required")
        if not input_refs:
            raise ValueError("input_refs are required")
        refs = tuple(
            sorted(
                set(input_refs),
                key=lambda ref: (ref.object_type, ref.object_id, ref.source_system, ref.revision),
            )
        )
        edp = EdpRepository(self.session)
        for ref in refs:
            if edp.get(self.tenant_id, ref) is None:
                raise ValueError(f"missing EDP reference: {ref}")
        identities = [(ref.object_type, ref.object_id, ref.source_system) for ref in refs]
        if len(identities) != len(set(identities)):
            raise ValueError("conflicting revisions for an EDP object")
        frozen = {
            "subject_type": subject_type,
            "subject_id": subject_id,
            "input_refs": [self._ref_data(ref) for ref in refs],
            "rule_set_version": rule_set_version,
        }
        checksum = self._checksum(frozen)
        object_id = self._object_id(subject_type, subject_id)
        runs = self.session.scalars(
            select(CalculationRun)
            .where(
                CalculationRun.tenant_id == self.tenant_id,
                CalculationRun.object_id == object_id,
                CalculationRun.source_system == "fac",
            )
            .order_by(CalculationRun.revision)
        ).all()
        for run in runs:
            if run.payload["checksum"] == checksum:
                return self.get(subject_type, subject_id, run.revision)
        version = runs[-1].revision + 1 if runs else 1
        context = CalculationContext(
            self.tenant_id,
            subject_type,
            subject_id,
            version,
            object_id,
            object_id + ":snapshot",
            refs,
            rule_set_version,
            checksum,
            trigger_type,
            reason,
            actor,
        )
        repo = CoreRepository(self.session)
        repo.add(
            CalculationSnapshot,
            self.tenant_id,
            context.snapshot_id,
            "fac",
            version,
            {**frozen, "checksum": checksum},
        )
        repo.add(
            CalculationRun,
            self.tenant_id,
            context.calculation_id,
            "fac",
            version,
            {
                "subject_type": subject_type,
                "subject_id": subject_id,
                "snapshot_id": context.snapshot_id,
                "checksum": checksum,
                "rule_set_version": rule_set_version,
                "trigger_type": trigger_type,
                "reason": reason,
                "actor": actor,
            },
        )
        self.session.commit()
        return context

    def get(self, subject_type: str, subject_id: str, version: int) -> CalculationContext | None:
        object_id = self._object_id(subject_type, subject_id)
        repo = CoreRepository(self.session)
        run = repo.get(CalculationRun, self.tenant_id, object_id, "fac", version)
        snapshot_id = object_id + ":snapshot"
        snap = repo.get(CalculationSnapshot, self.tenant_id, snapshot_id, "fac", version)
        if run is None or snap is None:
            return None
        frozen = {
            key: snap.payload[key]
            for key in ("subject_type", "subject_id", "input_refs", "rule_set_version")
        }
        if (
            self._checksum(frozen) != snap.payload["checksum"]
            or run.payload["checksum"] != snap.payload["checksum"]
        ):
            raise ValueError("snapshot checksum mismatch")
        return CalculationContext(
            self.tenant_id,
            subject_type,
            subject_id,
            version,
            object_id,
            snapshot_id,
            tuple(ObjectRef(**ref) for ref in snap.payload["input_refs"]),
            snap.payload["rule_set_version"],
            snap.payload["checksum"],
            run.payload["trigger_type"],
            run.payload["reason"],
            run.payload["actor"],
        )

    @staticmethod
    def _ref_data(ref: EdpObjectRef) -> dict:
        return {
            "object_type": ref.object_type,
            "object_id": ref.object_id,
            "source_system": ref.source_system,
            "revision": ref.revision,
        }

    @staticmethod
    def _object_id(subject_type: str, subject_id: str) -> str:
        return f"{subject_type}:{subject_id}"

    @staticmethod
    def _checksum(frozen: dict) -> str:
        encoded = json.dumps(frozen, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
