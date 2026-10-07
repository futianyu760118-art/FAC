"""Decimal-based money values with explicit currency precision and FX provenance."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from fac.contracts.common import FXRate
from fac.domain.errors import FXRateMissing, InvalidMoney


@dataclass(frozen=True)
class CurrencyMetadata:
    code: str
    decimal_places: int


CURRENCY_METADATA: dict[str, CurrencyMetadata] = {
    code: CurrencyMetadata(code=code, decimal_places=places)
    for code, places in {"CNY": 2, "USD": 2, "EUR": 2, "GBP": 2, "JPY": 0}.items()
}


def _quantize(value: Decimal, currency: str) -> Decimal:
    quantum = Decimal(1).scaleb(-CURRENCY_METADATA[currency].decimal_places)
    try:
        return value.quantize(quantum, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise InvalidMoney("amount cannot be represented at the currency precision") from exc


@dataclass(frozen=True)
class Money:
    original_amount: Decimal
    original_currency: str
    functional_currency: str
    fx_rate: Decimal
    original_currency_metadata: CurrencyMetadata
    functional_currency_metadata: CurrencyMetadata
    _functional_amount: Decimal

    @classmethod
    def from_original(
        cls,
        amount: Decimal,
        currency: str,
        functional_currency: str,
        fx: FXRate | None,
    ) -> "Money":
        if not isinstance(amount, Decimal) or not amount.is_finite() or amount < 0:
            raise InvalidMoney("amount must be a finite, non-negative Decimal")
        if not isinstance(currency, str) or not isinstance(functional_currency, str):
            raise InvalidMoney("currency codes must be strings")
        original_code = currency.upper()
        functional_code = functional_currency.upper()
        if original_code not in CURRENCY_METADATA or functional_code not in CURRENCY_METADATA:
            raise InvalidMoney("unsupported currency code")

        original_amount = _quantize(amount, original_code)
        if original_code == functional_code:
            if fx is not None and (fx.base_currency != original_code or fx.quote_currency != functional_code):
                raise FXRateMissing("FX rate currencies do not match the money currencies")
            rate = Decimal(1)
        else:
            if (
                fx is None
                or fx.base_currency != original_code
                or fx.quote_currency != functional_code
            ):
                raise FXRateMissing(
                    f"a sourced {original_code}-to-{functional_code} FX rate is required"
                )
            rate = fx.rate

        functional_amount = _quantize(original_amount * rate, functional_code)
        return cls(
            original_amount=original_amount,
            original_currency=original_code,
            functional_currency=functional_code,
            fx_rate=rate,
            original_currency_metadata=CURRENCY_METADATA[original_code],
            functional_currency_metadata=CURRENCY_METADATA[functional_code],
            _functional_amount=functional_amount,
        )

    def to_functional(self) -> Decimal:
        return self._functional_amount
