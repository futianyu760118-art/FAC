"""Versioned OFA policies. Unknown versions cannot silently use today's rules."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class CostRules:
    version: str
    rounding: str = ROUND_HALF_UP
    allow_explicit_override: bool = True
    allow_explicit_fallback: bool = True

    def quantity_in_price_uom(self, quantity: Decimal, factor: Decimal) -> Decimal:
        if not isinstance(quantity, Decimal) or not quantity.is_finite() or quantity <= 0:
            raise ValueError("BOM quantity must be a positive Decimal")
        if not isinstance(factor, Decimal) or not factor.is_finite() or factor <= 0:
            raise ValueError("UOM conversion factor must be a positive Decimal")
        return quantity * factor


RULE_REGISTRY = {"v1": CostRules("v1"), "v2": CostRules("v2")}


def get_rules(version: str) -> CostRules:
    try:
        return RULE_REGISTRY[version]
    except KeyError as exc:
        raise ValueError(f"unknown OFA rule version: {version}") from exc
