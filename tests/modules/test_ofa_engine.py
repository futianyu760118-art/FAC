from datetime import date
from decimal import Decimal as D

from fac.contracts.common import FXRate, ObjectRef
from fac.contracts.ofa import PlanCostResponse
from fac.modules.calculation.service import CalculationContext
from fac.modules.ofa.engine import OFAEngine
from fac.modules.ofa.models import (
    BOMInput,
    BOMLineInput,
    ExpenseInput,
    LaborInput,
    MaterialPriceInput,
    MoneyInput,
    OrderInput,
)


class Ports:
    def __init__(self, boms=(), prices=(), labor=(), expense=(), fx=()):
        self.boms = {item.product_id: item for item in boms}
        self.prices = prices
        self.labor = {item.product_id: item for item in labor}
        self.expense = {item.product_id: item for item in expense}
        self.fx = fx

    def get_bom(self, product_id, context):
        return self.boms.get(product_id)

    def get_material_prices(self, material_id, context):
        return [item for item in self.prices if item.material_id == material_id]

    def get_labor(self, product_id, context):
        return self.labor.get(product_id)

    def get_expense(self, product_id, context):
        return self.expense.get(product_id)

    def get_exchange_rate(self, base_currency, quote_currency, as_of, context):
        return next(
            (
                rate
                for rate in self.fx
                if rate.base_currency == base_currency
                and rate.quote_currency == quote_currency
                and rate.effective_at <= as_of
            ),
            None,
        )


def context():
    return CalculationContext(
        "t1", "Order", "o1", 1, "calc-1", "snap-1", (), "v1", "a" * 64, "manual", "test", "alice"
    )


def order(quantity="2", when=date(2026, 10, 7)):
    return OrderInput("o1", "p", D(quantity), when, "CNY", ObjectRef("Order", "o1", "mock", 1))


def price(material, amount, when=date(2026, 1, 1), uom="kg", currency="CNY", override=False):
    return MaterialPriceInput(
        material,
        MoneyInput(D(amount), currency),
        uom,
        when,
        ObjectRef("MaterialPrice", material + str(when), "mock", 1),
        override,
    )


def test_simple_bom_cost_components_and_total():
    ports = Ports(
        boms=[BOMInput("p", (BOMLineInput("steel", D(3), "kg"),))],
        prices=[price("steel", "4")],
        labor=[LaborInput("p", D(2), MoneyInput(D(5), "CNY"))],
        expense=[ExpenseInput("p", MoneyInput(D(1), "CNY"))],
    )
    result = OFAEngine().calculate_plan_cost(order(), ports, context())
    assert result.status == "DRAFT"
    assert result.material_cost.to_functional() == D("24.00")
    assert result.labor_cost.to_functional() == D("20.00")
    assert result.expense_cost.to_functional() == D("2.00")
    assert result.total_cost.to_functional() == D("46.00")
    assert result.cost_type == "PLAN"
    assert result.calculation_id == "calc-1"


def test_missing_price_is_incomplete_without_fake_total():
    ports = Ports(boms=[BOMInput("p", (BOMLineInput("unknown", D(1), "kg"),))])
    result = OFAEngine().calculate_plan_cost(order(), ports, context())
    assert result.status == "CALCULATION_INCOMPLETE"
    assert result.total_cost is None
    assert result.material_cost is None
    assert result.errors[0].code == "MaterialPriceMissing"


def test_historical_price_and_explicit_override():
    bom = BOMInput("p", (BOMLineInput("steel", D(1), "kg"),))
    ports = Ports(
        boms=[bom],
        prices=[
            price("steel", "3", date(2026, 1, 1)),
            price("steel", "7", date(2026, 11, 1)),
            price("steel", "4", date(2026, 9, 1)),
        ],
    )
    result = OFAEngine().calculate_plan_cost(order(), ports, context())
    assert result.material_cost.to_functional() == D("8.00")
    ports.prices.append(price("steel", "5", date(2026, 8, 1), override=True))
    assert OFAEngine().calculate_plan_cost(
        order(), ports, context()
    ).material_cost.to_functional() == D("10.00")


def test_missing_fx_is_incomplete_and_sourced_fx_converts():
    ports = Ports(
        boms=[BOMInput("p", (BOMLineInput("steel", D(1), "kg"),))],
        prices=[price("steel", "2", currency="USD")],
    )
    incomplete = OFAEngine().calculate_plan_cost(order(), ports, context())
    assert incomplete.status == "CALCULATION_INCOMPLETE"
    assert incomplete.total_cost is None
    assert incomplete.errors[0].code == "FXRateMissing"
    ports.fx = [FXRate("USD", "CNY", D(7), "spot", date(2026, 10, 1), "mock", 1, "evidence-fx")]
    complete = OFAEngine().calculate_plan_cost(order(), ports, context())
    assert complete.total_cost.to_functional() == D("28.00")
    assert complete.material_lines[0].money.original_currency == "USD"
    assert complete.material_lines[0].money.fx_rate == D(7)
    assert complete.fx_usages[0].rate.effective_at == date(2026, 10, 1)
    assert complete.fx_usages[0].rate.rate_type == "spot"
    assert complete.fx_usages[0].rate.evidence_ref == "evidence-fx"
    assert (
        PlanCostResponse.from_result(complete).model_dump(mode="json")["fx_usages"][0][
            "evidence_ref"
        ]
        == "evidence-fx"
    )


def test_response_contract_keeps_plan_distinction_and_decimal_values():
    ports = Ports(
        boms=[BOMInput("p", (BOMLineInput("steel", D(1), "kg"),))], prices=[price("steel", "2")]
    )
    result = OFAEngine().calculate_plan_cost(order(), ports, context())
    response = PlanCostResponse.from_result(result)
    payload = response.model_dump(mode="json")
    assert payload["cost_type"] == "PLAN"
    assert payload["total_cost"]["functional_amount"] == "4.00"
    assert payload["snapshot_id"] == "snap-1"
    assert "actual_cost" not in payload
