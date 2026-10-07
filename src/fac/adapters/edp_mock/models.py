"""Validated source projections carried by a local EDP fixture."""

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SourceObject(BaseModel):
    object_id: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    revision: int = Field(ge=1)


class MoneyInput(BaseModel):
    amount: Decimal
    currency: str

    @field_validator("currency")
    @classmethod
    def currency_code(cls, value: str) -> str:
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency must be a three-letter code")
        return value.upper()


class Order(SourceObject):
    customer_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    quantity: Decimal = Field(gt=0)
    unit_price: MoneyInput
    order_date: date


class BOMLine(BaseModel):
    material_id: str = Field(min_length=1)
    quantity: Decimal = Field(gt=0)
    uom: str = Field(min_length=1)


class BOM(SourceObject):
    product_id: str = Field(min_length=1)
    lines: list[BOMLine] = Field(min_length=1)


class MaterialPrice(SourceObject):
    material_id: str = Field(min_length=1)
    unit_price: MoneyInput
    effective_at: date


class Labor(SourceObject):
    product_id: str = Field(min_length=1)
    hours_per_unit: Decimal = Field(ge=0)
    hourly_rate: MoneyInput


class Expense(SourceObject):
    product_id: str = Field(min_length=1)
    expense_per_unit: MoneyInput


class FX(SourceObject):
    base_currency: str
    quote_currency: str
    rate: Decimal = Field(gt=0)
    rate_type: str = Field(min_length=1)
    effective_at: date
    evidence_ref: str = Field(min_length=1)

    @field_validator("base_currency", "quote_currency")
    @classmethod
    def currency_code(cls, value: str) -> str:
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency must be a three-letter code")
        return value.upper()


class EdpFixture(BaseModel):
    tenant_id: str = Field(min_length=1)
    orders: list[Any] = Field(default_factory=list)
    boms: list[Any] = Field(default_factory=list)
    material_prices: list[Any] = Field(default_factory=list)
    labor: list[Any] = Field(default_factory=list)
    expenses: list[Any] = Field(default_factory=list)
    fx_rates: list[Any] = Field(default_factory=list)


class RejectedObject(BaseModel):
    object_type: str
    object_id: str | None
    reasons: list[dict[str, Any]]


class ImportReport(BaseModel):
    accepted_count: int = 0
    skipped_count: int = 0
    rejected_count: int = 0
    rejected: list[RejectedObject] = Field(default_factory=list)
