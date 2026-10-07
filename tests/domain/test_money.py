from datetime import date
from decimal import Decimal

import pytest

from fac.contracts.common import FXRate
from fac.domain.errors import FXRateMissing, InvalidMoney
from fac.domain.money import CURRENCY_METADATA, Money


def fx(base: str, quote: str, rate: str) -> FXRate:
    return FXRate(
        base_currency=base,
        quote_currency=quote,
        rate=Decimal(rate),
        rate_type="closing",
        effective_at=date(2026, 10, 7),
        source="EDP",
        revision=1,
        evidence_ref="ev-fx-1",
    )


def test_same_currency_stores_identity_rate_and_currency_metadata() -> None:
    money = Money.from_original(Decimal("12.34"), "CNY", "CNY", None)

    assert money.fx_rate == Decimal(1)
    assert money.original_currency == money.functional_currency == "CNY"
    assert money.original_amount == money.to_functional() == Decimal("12.34")
    assert money.original_currency_metadata == CURRENCY_METADATA["CNY"]
    assert money.functional_currency_metadata == CURRENCY_METADATA["CNY"]


@pytest.mark.parametrize(
    ("currency", "amount", "rate", "expected"),
    [
        ("USD", "10.25", "7.123456", "73.02"),
        ("EUR", "10.00", "7.5", "75.00"),
        ("GBP", "10.00", "9.1", "91.00"),
        ("JPY", "10", "0.0485", "0.49"),
    ],
)
def test_foreign_currency_conversion_uses_decimal_currency_precision(
    currency: str, amount: str, rate: str, expected: str
) -> None:
    money = Money.from_original(Decimal(amount), currency, "CNY", fx(currency, "CNY", rate))

    assert money.to_functional() == Decimal(expected)
    assert money.fx_rate == Decimal(rate)
    assert isinstance(money.to_functional(), Decimal)


def test_jpy_original_and_functional_amounts_use_zero_decimal_quantization() -> None:
    money = Money.from_original(Decimal("10.5"), "JPY", "JPY", None)

    assert money.original_amount == Decimal(11)
    assert money.to_functional() == Decimal(11)


def test_non_functional_currency_requires_matching_fx_rate() -> None:
    with pytest.raises(FXRateMissing) as exc:
        Money.from_original(Decimal(1), "USD", "CNY", None)

    assert exc.value.code == "FX_RATE_MISSING"


def test_fx_rate_must_match_original_to_functional_currency_direction() -> None:
    with pytest.raises(FXRateMissing):
        Money.from_original(Decimal(1), "USD", "CNY", fx("CNY", "USD", "0.14"))


@pytest.mark.parametrize(
    ("amount", "currency"),
    [
        (Decimal(1), "XXX"),
        (Decimal("-0.01"), "CNY"),
        (Decimal("NaN"), "CNY"),
        (Decimal("Infinity"), "CNY"),
        (1.25, "CNY"),
        ("1.25", "CNY"),
    ],
)
def test_invalid_money_inputs_raise_stable_domain_error(amount: object, currency: str) -> None:
    with pytest.raises(InvalidMoney) as exc:
        Money.from_original(amount, currency, "CNY", None)  # type: ignore[arg-type]

    assert exc.value.code == "INVALID_MONEY"
