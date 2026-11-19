"""OFA input boundary: callers provide frozen EDP projections."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Protocol

from sqlalchemy.orm import Session

from fac.contracts.common import FXRate, ObjectRef
from fac.infrastructure.repositories import EdpRepository
from fac.modules.calculation.service import CalculationContext
from fac.modules.ofa.models import (
    BOMInput,
    BOMLineInput,
    ExpenseInput,
    LaborInput,
    MaterialPriceInput,
    MoneyInput,
    OrderInput,
)


class OFAPorts(Protocol):
    def get_order(self, ref: ObjectRef, context: CalculationContext) -> OrderInput: ...

    def get_bom(self, product_id: str, context: CalculationContext) -> BOMInput | None: ...

    def get_material_prices(
        self, material_id: str, context: CalculationContext
    ) -> Sequence[MaterialPriceInput]: ...

    def get_labor(self, product_id: str, context: CalculationContext) -> LaborInput | None: ...

    def get_expense(self, product_id: str, context: CalculationContext) -> ExpenseInput | None: ...

    def get_exchange_rate(
        self, base_currency: str, quote_currency: str, as_of: date, context: CalculationContext
    ) -> FXRate | None: ...


class EdpOFAPorts:
    """Read only the tenant's EDP revisions named by the snapshot."""

    def __init__(self, session: Session, tenant_id: str):
        self.repository = EdpRepository(session)
        self.tenant_id = tenant_id

    def _projections(self, kind: str, context: CalculationContext):
        if context.tenant_id != self.tenant_id:
            raise ValueError("context tenant mismatch")
        for ref in context.input_refs:
            if ref.object_type == kind:
                row = self.repository.get(self.tenant_id, ref)
                if row is None:
                    raise ValueError(f"frozen EDP reference disappeared: {ref}")
                yield ref, row.payload

    def get_order(self, ref: ObjectRef, context: CalculationContext) -> OrderInput:
        if ref not in context.input_refs or ref.object_type != "Order":
            raise ValueError("order ref is not frozen in snapshot")
        for candidate, payload in self._projections("Order", context):
            if candidate == ref:
                return OrderInput(
                    ref.object_id,
                    payload["product_id"],
                    Decimal(payload["quantity"]),
                    date.fromisoformat(payload["order_date"]),
                    payload.get("functional_currency", "CNY"),
                    ref,
                )
        raise ValueError("frozen order ref is unavailable")

    def get_bom(self, product_id: str, context: CalculationContext) -> BOMInput | None:
        for _, payload in self._projections("BOM", context):
            if payload["product_id"] == product_id:
                lines = tuple(
                    BOMLineInput(
                        line.get("component_id", line.get("material_id")),
                        Decimal(line["quantity"]),
                        line["uom"],
                        line.get("kind", "MATERIAL"),
                        Decimal(line.get("conversion_factor", "1")),
                        self._money(line["processing_price"])
                        if line.get("processing_price")
                        else None,
                        line.get("price_uom"),
                    )
                    for line in payload["lines"]
                )
                return BOMInput(product_id, lines)
        return None

    def get_material_prices(
        self, material_id: str, context: CalculationContext
    ) -> Sequence[MaterialPriceInput]:
        return [
            MaterialPriceInput(
                material_id,
                self._money(payload["unit_price"]),
                payload.get("uom", ""),
                date.fromisoformat(payload["effective_at"]),
                ref,
                payload.get("override", False),
                payload.get("fallback", False),
            )
            for ref, payload in self._projections("MaterialPrice", context)
            if payload["material_id"] == material_id
        ]

    def get_labor(self, product_id: str, context: CalculationContext) -> LaborInput | None:
        for _, payload in self._projections("Labor", context):
            if payload["product_id"] == product_id:
                return LaborInput(
                    product_id,
                    Decimal(payload["hours_per_unit"]),
                    self._money(payload["hourly_rate"]),
                )
        return None

    def get_expense(self, product_id: str, context: CalculationContext) -> ExpenseInput | None:
        for _, payload in self._projections("Expense", context):
            if payload["product_id"] == product_id:
                return ExpenseInput(product_id, self._money(payload["expense_per_unit"]))
        return None

    def get_exchange_rate(
        self, base_currency: str, quote_currency: str, as_of: date, context: CalculationContext
    ) -> FXRate | None:
        candidates = [
            (ref, payload)
            for ref, payload in self._projections("FX", context)
            if payload["base_currency"].upper() == base_currency
            and payload["quote_currency"].upper() == quote_currency
            and date.fromisoformat(payload["effective_at"]) <= as_of
        ]
        if not candidates:
            return None
        ref, payload = max(candidates, key=lambda pair: (pair[1]["effective_at"], pair[0].revision))
        return FXRate(
            base_currency,
            quote_currency,
            Decimal(payload["rate"]),
            payload["rate_type"],
            date.fromisoformat(payload["effective_at"]),
            ref.source_system,
            ref.revision,
            payload["evidence_ref"],
        )

    @staticmethod
    def _money(payload: dict) -> MoneyInput:
        return MoneyInput(Decimal(payload["amount"]), payload["currency"])
