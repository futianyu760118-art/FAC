"""Per-object validation and import of local EDP fixture data."""

import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from fac.adapters.edp_mock.models import (
    BOM,
    FX,
    EdpFixture,
    Expense,
    ImportReport,
    Labor,
    MaterialPrice,
    Order,
    RejectedObject,
)
from fac.contracts.common import ObjectRef
from fac.infrastructure.repositories import EdpRepository, RevisionConflict


class EdpAdapter:
    def __init__(self, session: Session):
        self.session = session

    def import_fixture(self, payload: EdpFixture) -> ImportReport:
        report = ImportReport()
        repo = EdpRepository(self.session)
        groups = (
            ("orders", Order, "Order"),
            ("boms", BOM, "BOM"),
            ("material_prices", MaterialPrice, "MaterialPrice"),
            ("labor", Labor, "Labor"),
            ("expenses", Expense, "Expense"),
            ("fx_rates", FX, "FX"),
        )
        try:
            for field, schema, kind in groups:
                for raw in getattr(payload, field):
                    try:
                        item = schema.model_validate(raw)
                    except ValidationError as exc:
                        raw_id = raw.get("object_id") if isinstance(raw, dict) else None
                        if raw_id is None or isinstance(raw_id, str):
                            rejected_id = raw_id
                        else:
                            rejected_id = json.dumps(raw_id, ensure_ascii=False, sort_keys=True)
                        report.rejected.append(
                            RejectedObject(
                                object_type=kind,
                                object_id=rejected_id,
                                reasons=[
                                    {
                                        "field": ".".join(map(str, error["loc"])),
                                        "code": error["type"],
                                        "message": error["msg"],
                                    }
                                    for error in exc.errors()
                                ],
                            )
                        )
                        report.rejected_count += 1
                        continue
                    ref = ObjectRef(kind, item.object_id, item.source_system, item.revision)
                    try:
                        inserted = repo.add(payload.tenant_id, ref, item.model_dump(mode="json"))
                    except RevisionConflict as exc:
                        report.rejected.append(
                            RejectedObject(
                                object_type=kind,
                                object_id=item.object_id,
                                reasons=[
                                    {
                                        "field": "revision",
                                        "code": "revision_conflict",
                                        "message": str(exc),
                                    }
                                ],
                            )
                        )
                        report.rejected_count += 1
                        continue
                    if inserted:
                        report.accepted_count += 1
                    else:
                        report.skipped_count += 1
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return report
