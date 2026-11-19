"""Plan cost rollup over frozen OFA inputs."""

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from fac.contracts.common import FXRate, ObjectRef
from fac.domain.errors import FXRateMissing
from fac.domain.money import CURRENCY_METADATA, Money
from fac.infrastructure.models import CalculationResult
from fac.infrastructure.repositories import CoreRepository
from fac.modules.calculation.service import CalculationContext, CalculationService
from fac.modules.ofa.models import CostError, CostLine, FxUsage, OrderInput, PlanCostResult
from fac.modules.ofa.ports import OFAPorts
from fac.modules.ofa.rules import get_rules


class OFAEngine:
    def __init__(self, session: Session | None = None):
        self.session = session

    def get_result(self, context: CalculationContext) -> PlanCostResult | None:
        if self.session is None:
            return None
        result_id = f"{context.calculation_id}:plan:v{context.version}"
        row = CoreRepository(self.session).get(
            CalculationResult, context.tenant_id, result_id, "fac", context.version
        )
        if row is None:
            return None
        payload = row.payload
        if payload["checksum"] != context.checksum or payload["snapshot_id"] != context.snapshot_id:
            raise ValueError("result snapshot checksum or identity mismatch")

        def money(data):
            if data is None:
                return None
            return Money(
                Decimal(data["original_amount"]),
                data["original_currency"],
                data["functional_currency"],
                Decimal(data["fx_rate"]),
                CURRENCY_METADATA[data["original_currency"]],
                CURRENCY_METADATA[data["functional_currency"]],
                Decimal(data["functional_amount"]),
            )

        from fac.modules.ofa.models import CostLine

        return PlanCostResult(
            result_id,
            context.version,
            context.calculation_id,
            context.snapshot_id,
            payload["rule_set_version"],
            payload["status"],
            money(payload["material_cost"]),
            money(payload["labor_cost"]),
            money(payload["expense_cost"]),
            money(payload["processing_cost"]),
            money(payload["total_cost"]),
            tuple(
                CostLine(
                    item["component_id"],
                    Decimal(item["quantity"]),
                    item["uom"],
                    money(item["money"]),
                    ObjectRef(**item["price_ref"]) if item["price_ref"] else None,
                )
                for item in payload["material_lines"]
            ),
            tuple(CostError(**item) for item in payload["errors"]),
            (),
            payload["previous_result_id"],
            fx_usages=tuple(
                FxUsage(
                    item["cost_component"],
                    item["object_id"],
                    Decimal(item["original_amount"]),
                    FXRate(
                        item["base_currency"],
                        item["quote_currency"],
                        Decimal(item["rate"]),
                        item["rate_type"],
                        date.fromisoformat(item["effective_at"]),
                        item["source"],
                        item["revision"],
                        item["evidence_ref"],
                    ),
                )
                for item in payload.get("fx_usages", [])
            ),
        )

    def calculate_plan_cost(
        self, order: OrderInput, ports: OFAPorts, context: CalculationContext
    ) -> PlanCostResult:
        existing = self.get_result(context)
        if existing is not None:
            return existing
        rules = get_rules(context.rule_set_version)
        if order.order_id != context.subject_id or context.subject_type != "Order":
            raise ValueError("order does not match calculation context")
        if not isinstance(order.quantity, Decimal) or order.quantity <= 0:
            raise ValueError("order quantity must be a positive Decimal")
        if context.input_refs and order.ref not in context.input_refs:
            raise ValueError("order ref is not frozen in snapshot")
        currency = order.functional_currency
        totals = {name: Decimal(0) for name in ("material", "labor", "expense", "processing")}
        material_lines: list[CostLine] = []
        fx_usages: list[FxUsage] = []
        errors: list[CostError] = []

        def add_amount(
            kind: str,
            amount: Decimal,
            unit_currency: str,
            component_id: str,
            quantity: Decimal,
            uom: str,
            price_ref=None,
        ):
            try:
                fx = (
                    None
                    if unit_currency.upper() == currency.upper()
                    else ports.get_exchange_rate(
                        unit_currency.upper(), currency.upper(), order.order_date, context
                    )
                )
                money = Money.from_original(amount, unit_currency, currency, fx)
            except FXRateMissing:
                errors.append(CostError("FXRateMissing", f"{unit_currency}->{currency}"))
                return
            totals[kind] += money.to_functional()
            if fx is not None:
                fx_usages.append(FxUsage(kind, component_id, money.original_amount, fx))
            if kind == "material":
                material_lines.append(CostLine(component_id, quantity, uom, money, price_ref))

        def rollup(product_id: str, units: Decimal, stack: tuple[str, ...]):
            if product_id in stack:
                raise ValueError("cyclic BOM")
            bom = ports.get_bom(product_id, context)
            if bom is None:
                errors.append(CostError("BOMMissing", product_id))
                return
            labor = ports.get_labor(product_id, context)
            if labor is not None:
                add_amount(
                    "labor",
                    units * labor.hours_per_unit * labor.hourly_rate.amount,
                    labor.hourly_rate.currency,
                    product_id,
                    units,
                    "unit",
                )
            expense = ports.get_expense(product_id, context)
            if expense is not None:
                add_amount(
                    "expense",
                    units * expense.expense_per_unit.amount,
                    expense.expense_per_unit.currency,
                    product_id,
                    units,
                    "unit",
                )
            merged = defaultdict(lambda: Decimal(0))
            for line in bom.lines:
                if line.kind != "SELF_MADE" and line.conversion_factor != 1 and not line.price_uom:
                    raise ValueError("price_uom is required for UOM conversion")
                key = (
                    line.component_id,
                    line.uom,
                    line.kind,
                    line.conversion_factor,
                    line.processing_price,
                    line.price_uom,
                )
                merged[key] += line.quantity
            for (
                component_id,
                uom,
                kind,
                factor,
                processing_price,
                price_uom,
            ), per_unit in merged.items():
                quantity = units * rules.quantity_in_price_uom(per_unit, factor)
                if kind == "SELF_MADE":
                    rollup(component_id, quantity, (*stack, product_id))
                    continue
                if kind not in ("MATERIAL", "OUTSOURCE"):
                    raise ValueError(f"unsupported BOM kind: {kind}")
                candidates = [
                    item
                    for item in ports.get_material_prices(component_id, context)
                    if item.effective_at <= order.order_date
                    and (item.uom == price_uom if price_uom else item.uom in ("", uom))
                ]
                overrides = [item for item in candidates if item.override]
                normal = [item for item in candidates if not item.override and not item.fallback]
                fallback = [item for item in candidates if item.fallback]
                pool = (
                    overrides
                    if rules.allow_explicit_override and overrides
                    else normal or (fallback if rules.allow_explicit_fallback else [])
                )
                if not pool:
                    errors.append(CostError("MaterialPriceMissing", component_id))
                else:
                    selected = max(pool, key=lambda item: (item.effective_at, item.ref.revision))
                    add_amount(
                        "material",
                        quantity * selected.unit_price.amount,
                        selected.unit_price.currency,
                        component_id,
                        quantity,
                        selected.uom,
                        selected.ref,
                    )
                if kind == "OUTSOURCE":
                    if processing_price is None:
                        errors.append(CostError("OutsourceProcessingPriceMissing", component_id))
                    else:
                        add_amount(
                            "processing",
                            quantity * processing_price.amount,
                            processing_price.currency,
                            component_id,
                            quantity,
                            uom,
                        )

        rollup(order.product_id, order.quantity, ())
        complete = not errors

        def component(name: str) -> Money | None:
            return Money.from_original(totals[name], currency, currency, None) if complete else None

        total = (
            Money.from_original(sum(totals.values()), currency, currency, None)
            if complete
            else None
        )
        result = PlanCostResult(
            result_id=f"{context.calculation_id}:plan:v{context.version}",
            version=context.version,
            calculation_id=context.calculation_id,
            snapshot_id=context.snapshot_id,
            rule_set_version=context.rule_set_version,
            status="DRAFT" if complete else "CALCULATION_INCOMPLETE",
            material_cost=component("material"),
            labor_cost=component("labor"),
            expense_cost=component("expense"),
            processing_cost=component("processing"),
            total_cost=total,
            material_lines=tuple(material_lines),
            errors=tuple(errors),
            previous_result_id=(
                f"{context.calculation_id}:plan:v{context.version - 1}"
                if context.version > 1
                else None
            ),
            fx_usages=tuple(fx_usages),
        )
        if self.session is not None:
            self._persist(result, context)
        return result

    def _persist(self, result: PlanCostResult, context: CalculationContext) -> None:
        def money(value):
            if value is None:
                return None
            return {
                "original_amount": str(value.original_amount),
                "original_currency": value.original_currency,
                "functional_amount": str(value.to_functional()),
                "functional_currency": value.functional_currency,
                "fx_rate": str(value.fx_rate),
            }

        payload = {
            "rule_set_version": result.rule_set_version,
            "snapshot_id": result.snapshot_id,
            "checksum": context.checksum,
            "status": result.status,
            "cost_type": result.cost_type,
            "material_cost": money(result.material_cost),
            "labor_cost": money(result.labor_cost),
            "expense_cost": money(result.expense_cost),
            "processing_cost": money(result.processing_cost),
            "total_cost": money(result.total_cost),
            "material_lines": [
                {
                    "component_id": line.component_id,
                    "quantity": str(line.quantity),
                    "uom": line.uom,
                    "money": money(line.money),
                    "price_ref": (
                        CalculationService._ref_data(line.price_ref) if line.price_ref else None
                    ),
                }
                for line in result.material_lines
            ],
            "errors": [
                {"code": error.code, "object_id": error.object_id} for error in result.errors
            ],
            "previous_result_id": result.previous_result_id,
            "evidence_refs": [],
            "fx_usages": [
                {
                    "cost_component": item.cost_component,
                    "object_id": item.object_id,
                    "original_amount": str(item.original_amount),
                    "base_currency": item.rate.base_currency,
                    "quote_currency": item.rate.quote_currency,
                    "rate": str(item.rate.rate),
                    "rate_type": item.rate.rate_type,
                    "effective_at": item.rate.effective_at.isoformat(),
                    "source": item.rate.source,
                    "revision": item.rate.revision,
                    "evidence_ref": item.rate.evidence_ref,
                }
                for item in result.fx_usages
            ],
        }
        CoreRepository(self.session).add(
            CalculationResult, context.tenant_id, result.result_id, "fac", result.version, payload
        )
        self.session.commit()
