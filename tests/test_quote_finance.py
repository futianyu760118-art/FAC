from decimal import Decimal

from fastapi.testclient import TestClient

from fac.domain.quote_finance import QuoteFinanceInput, RiskLevel, calculate_quote_finance
from fac.main import create_app


def sample_payload() -> QuoteFinanceInput:
    return QuoteFinanceInput(
        inquiry_id="INQ-2026-0088",
        quote_version="V1",
        customer_id="CUS-001",
        product_id="WL6000",
        configuration_id="CFG-WL6000-V2",
        specification_id="SPEC-WL6000-V4",
        bom_id="BOM-WL6000-R12",
        quantity=Decimal("8000"),
        unit_price_original=Decimal("15.90"),
        currency="USD",
        fx_rate_to_cny=Decimal("7.20"),
        material_cost_cny=Decimal("468000"),
        labor_cost_cny=Decimal("61000"),
        processing_cost_cny=Decimal("42000"),
        packaging_cost_cny=Decimal("28000"),
        logistics_cost_cny=Decimal("36000"),
        quality_reserve_cny=Decimal("15000"),
        aftersales_reserve_cny=Decimal("12000"),
        fx_reserve_cny=Decimal("9000"),
        payment_days=87,
    )


def test_quote_finance_is_deterministic():
    result = calculate_quote_finance(sample_payload())
    assert result.total_cost_cny == Decimal("671000.00")
    assert result.revenue_cny == Decimal("915840.00")
    assert result.gross_profit_cny == Decimal("244840.00")
    assert result.risk_level == RiskLevel.LOW
    assert result.calculation_method == "DETERMINISTIC"


def test_quote_finance_api_and_m13_registry():
    client = TestClient(create_app())
    response = client.post("/api/v1/fac/quote-finance/calculate", json=sample_payload().model_dump(mode="json"))
    assert response.status_code == 200
    assert response.json()["total_cost_cny"] == "671000.00"

    agents = client.get("/api/v1/fac/m13/finance-agents")
    assert agents.status_code == 200
    assert len(agents.json()) == 10
    assert agents.json()[0]["agent_id"] == "AG-FAC-001"
