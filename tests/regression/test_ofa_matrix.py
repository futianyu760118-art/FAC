from decimal import Decimal as D

import pytest

from fac.modules.ofa.engine import OFAEngine
from fac.modules.ofa.models import BOMInput, BOMLineInput, MoneyInput
from tests.modules.test_ofa_engine import Ports, context, order, price


@pytest.mark.parametrize(
    "boms,prices,expected",
    [
        (
            [
                BOMInput("p", (BOMLineInput("part", D(2), "kg", kind="SELF_MADE"),)),
                BOMInput("part", (BOMLineInput("steel", D(3), "kg"),)),
            ],
            [price("steel", "4"), price("part", "999")],
            "48.00",
        ),
        (
            [BOMInput("p", (BOMLineInput("steel", D(1), "kg"), BOMLineInput("steel", D(2), "kg")))],
            [price("steel", "4")],
            "24.00",
        ),
        (
            [
                BOMInput(
                    "p",
                    (
                        BOMLineInput(
                            "steel", D(2000), "g", conversion_factor=D("0.001"), price_uom="kg"
                        ),
                    ),
                )
            ],
            [price("steel", "4")],
            "16.00",
        ),
        (
            [
                BOMInput(
                    "p",
                    (
                        BOMLineInput(
                            "plate",
                            D(2),
                            "piece",
                            kind="OUTSOURCE",
                            processing_price=MoneyInput(D(3), "CNY"),
                        ),
                    ),
                )
            ],
            [price("plate", "4", uom="piece")],
            "28.00",
        ),
    ],
)
def test_rollup_matrix(boms, prices, expected):
    result = OFAEngine().calculate_plan_cost(order(), Ports(boms=boms, prices=prices), context())
    assert result.status == "DRAFT"
    assert result.total_cost.to_functional() == D(expected)


def test_conversion_requires_explicit_target_price_uom():
    boms = [BOMInput("p", (BOMLineInput("steel", D(1000), "g",
                                         conversion_factor=D("0.001")),))]
    with pytest.raises(ValueError, match="price_uom"):
        OFAEngine().calculate_plan_cost(order(), Ports(boms=boms, prices=[price("steel", "4")]),
                                        context())
