"""Per-object validation and import of local EDP fixture data."""

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
from fac.infrastructure.repositories import EdpRepository


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
                        report.rejected.append(
                            RejectedObject(
                                object_type=kind,
                                object_id=raw.get("object_id") if isinstance(raw, dict) else None,
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
                    if repo.add(payload.tenant_id, ref, item.model_dump(mode="json")):
                        report.accepted_count += 1
                    else:
                        report.skipped_count += 1
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return report
