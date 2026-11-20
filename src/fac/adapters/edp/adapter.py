"""Read-only adapter from the EDP Tool API into FAC projections.

FAC never connects to the SPC/ERP database. EDP owns source ingestion and
exposes the governed, evidence-aware Tool API; this adapter only reads that
contract and stores immutable, revision-scoped FAC projections.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from fac.adapters.edp_mock.adapter import EdpAdapter
from fac.adapters.edp_mock.models import EdpFixture
from fac.infrastructure.repositories import EdpRepository, RevisionConflict
from fac.settings import Settings


class EdpApiError(RuntimeError):
    """The configured EDP endpoint could not fulfil a read request."""


class EdpImportRequest(BaseModel):
    tenant_id: str | None = None
    order_no: str | None = Field(default=None, min_length=1, max_length=256)
    limit: int = Field(default=50, ge=1, le=100)


class EdpImportReport(BaseModel):
    import_id: str
    source: str
    status: str
    requested_order: str | None = None
    accepted_count: int = 0
    skipped_count: int = 0
    rejected_count: int = 0
    orders: int = 0
    boms: int = 0
    purchase_orders: int = 0
    inventory: int = 0
    available_data: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    rejected: list[dict] = Field(default_factory=list)
    message: str | None = None


@dataclass(slots=True)
class _EdpApiClient:
    base_url: str
    api_key: str
    timeout: float
    source_system: str

    def get(self, path: str, params: dict[str, object] | None = None) -> dict:
        query = urllib.parse.urlencode({key: value for key, value in (params or {}).items() if value is not None})
        url = f"{self.base_url.rstrip('/')}{path}"
        if query:
            url = f"{url}?{query}"
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "X-API-Key": self.api_key},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:300]
            raise EdpApiError(f"EDP {exc.code} {path}: {body}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise EdpApiError(f"EDP 请求失败 {path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise EdpApiError(f"EDP 响应格式错误 {path}")
        return payload


@dataclass(slots=True)
class EdpApiAdapter:
    session: Session
    settings: Settings
    client: _EdpApiClient | None = None

    def __post_init__(self) -> None:
        if self.client is None:
            self.client = _EdpApiClient(
                self.settings.edp_base_url,
                self.settings.edp_api_key,
                self.settings.edp_timeout_seconds,
                self.settings.edp_source_system,
            )

    def import_orders(self, request: EdpImportRequest, *, import_id: str | None = None) -> EdpImportReport:
        if not self.settings.edp_base_url.strip():
            raise EdpApiError("FAC_EDP_BASE_URL 未配置，无法从 EDP 导入实际数据")
        assert self.client is not None
        order_items = (
            [self.client.get(f"/api/v1/tools/orders/{urllib.parse.quote(request.order_no, safe='')}")]
            if request.order_no
            else self.client.get("/api/v1/tools/orders", {"limit": request.limit}).get("items", [])
        )
        if not isinstance(order_items, list):
            raise EdpApiError("EDP 订单列表响应缺少 items")

        fixture = EdpFixture(tenant_id=request.tenant_id or self.settings.tenant_id)
        counts = {"orders": 0, "boms": 0, "purchase_orders": 0, "inventory": 0}
        seen_products: set[str] = set()
        seen_materials: set[str] = set()
        rejected: list[dict] = []

        for summary in order_items:
            try:
                detail = summary if "lines" in summary else self.client.get(
                    f"/api/v1/tools/orders/{urllib.parse.quote(str(summary['order_no']), safe='')}"
                )
                order = self._order(detail)
                fixture.orders.append(order)
                counts["orders"] += 1
                for line in detail.get("lines") or []:
                    product = line.get("product_code")
                    material = line.get("material_code")
                    if product:
                        seen_products.add(str(product))
                    if material:
                        seen_materials.add(str(material))
            except (KeyError, TypeError, ValueError, EdpApiError) as exc:
                rejected.append({"object_type": "Order", "object_id": summary.get("order_no"), "reasons": [str(exc)]})

        for product in sorted(seen_products):
            try:
                bom = self.client.get("/api/v1/tools/bom", {"product_code": product})
                lines = [
                    {
                        "material_id": item.get("material_code") or "UNKNOWN",
                        "quantity": item.get("quantity_per"),
                        "uom": "EA",
                    }
                    for item in bom.get("items", [])
                    if item.get("material_code") and item.get("quantity_per") is not None
                ]
                if lines:
                    fixture.boms.append(
                        {
                            "object_id": f"BOM:{product}:{bom.get('bom_version') or 'ACTIVE'}",
                            "source_system": self.settings.edp_source_system,
                            "revision": self._hint_revision(bom.get("evidence_hint")),
                            "product_id": product,
                            "lines": lines,
                        }
                    )
                    counts["boms"] += 1
                    seen_materials.update(str(line["material_id"]) for line in lines)
            except (EdpApiError, KeyError, TypeError, ValueError) as exc:
                rejected.append({"object_type": "BOM", "object_id": product, "reasons": [str(exc)]})

        # Purchase and inventory facts are stored as generic EDP projections so
        # the EBMS workbench can show their real presence without inventing cost.
        related = self._related_projections(fixture.tenant_id, seen_materials)
        counts["purchase_orders"] = related.pop("purchase_orders")
        counts["inventory"] = related.pop("inventory")

        report = EdpAdapter(self.session).import_fixture(fixture)
        for kind, items in related.items():
            for item in items:
                ref = item.pop("_ref")
                try:
                    if EdpRepository(self.session).add(fixture.tenant_id, ref, item):
                        report.accepted_count += 1
                    else:
                        report.skipped_count += 1
                except RevisionConflict as exc:
                    report.rejected_count += 1
                    rejected.append({"object_type": kind, "object_id": ref.object_id, "reasons": [str(exc)]})
        self.session.commit()

        missing = ["material_prices", "labor", "expenses", "fx_rates"]
        available = ["orders", "boms"]
        if counts["purchase_orders"]:
            available.append("purchase_orders")
        if counts["inventory"]:
            available.append("inventory")
        return EdpImportReport(
            import_id=import_id or f"edp-import-{uuid4().hex[:16]}",
            source=self.settings.edp_source_system,
            status="SUCCEEDED" if not rejected else "PARTIAL",
            requested_order=request.order_no,
            accepted_count=report.accepted_count,
            skipped_count=report.skipped_count,
            rejected_count=report.rejected_count + len(rejected),
            orders=counts["orders"],
            boms=counts["boms"],
            purchase_orders=counts["purchase_orders"],
            inventory=counts["inventory"],
            available_data=available,
            missing_data=missing,
            rejected=[*report.rejected, *rejected],
            message="已导入 EDP 实际对象；FAC 计划成本仍缺少 EDP 财经价格/人工/费用/汇率事实。",
        )

    def _order(self, detail: dict) -> dict:
        lines = detail.get("lines") or []
        first = next((line for line in lines if line.get("product_code") or line.get("material_code")), None)
        if not first:
            raise ValueError("订单缺少可用于核算的 product_code/material_code")
        quantity = first.get("quantity") or 1
        unit_price = first.get("unit_price")
        amount = detail.get("amount")
        currency = detail.get("currency") or (unit_price or {}).get("currency") or "CNY"
        if not isinstance(unit_price, dict) or unit_price.get("amount") is None:
            unit_price = {"amount": amount or 0, "currency": currency}
        customer = detail.get("customer") or {}
        return {
            "object_id": detail["order_no"],
            "source_system": self.settings.edp_source_system,
            "revision": self._hint_revision(detail.get("evidence_hint")),
            "customer_id": customer.get("code") or "EDP-UNKNOWN",
            "product_id": first.get("product_code") or first.get("material_code"),
            "quantity": quantity,
            "unit_price": {"amount": unit_price.get("amount", 0), "currency": currency},
            "order_date": self._date(detail.get("order_date")),
            "amount": amount,
            "currency": currency,
            "delivery_date": self._date(detail.get("delivery_date")),
            "lines": lines,
            "evidence_hint": detail.get("evidence_hint"),
        }

    def _related_projections(self, tenant_id: str, materials: set[str]) -> dict[str, object]:
        assert self.client is not None
        purchase_orders: list[dict] = []
        inventory: list[dict] = []
        for material in sorted(materials):
            try:
                purchase = self.client.get("/api/v1/tools/purchase-orders", {"material_code": material, "limit": 100})
                for item in purchase.get("items", []):
                    row = dict(item)
                    ref_id = str(row.pop("object_id", row.get("po_no")))
                    row["material_code"] = material
                    row["_ref"] = self._ref("PurchaseOrder", ref_id, self._hint_revision(row.get("evidence_hint")))
                    purchase_orders.append(row)
            except EdpApiError:
                pass
            try:
                stock = self.client.get("/api/v1/tools/inventory", {"material_code": material})
                row = dict(stock)
                ref_id = f"{material}:inventory"
                row["_ref"] = self._ref("Inventory", ref_id, self._hint_revision(row.get("evidence_hint")))
                inventory.append(row)
            except EdpApiError:
                pass
        return {"purchase_orders": len(purchase_orders), "inventory": len(inventory), "PurchaseOrder": purchase_orders, "Inventory": inventory}

    def _ref(self, kind: str, object_id: str, revision: int):
        from fac.contracts.common import ObjectRef

        return ObjectRef(kind, object_id, self.settings.edp_source_system, max(1, revision))

    def _hint_revision(self, hint: object) -> int:
        if not isinstance(hint, dict):
            return 1
        assert self.client is not None
        object_id = hint.get("object_id")
        if not object_id:
            return 1
        try:
            payload = self.client.get(f"/api/v1/objects/{object_id}")
            return int(payload.get("revision") or 1)
        except (EdpApiError, TypeError, ValueError):
            return 1

    @staticmethod
    def _date(value: object) -> str:
        if value is None:
            return datetime.now(UTC).date().isoformat()
        return str(value)[:10]
