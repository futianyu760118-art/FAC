"""Read-only adapter from the existing EBMS order-analysis API into FAC.

The fallback deliberately uses only EBMS GET endpoints. It never calls EBMS
sync or mutation endpoints, so choosing the fallback cannot change source data.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from sqlalchemy.orm import Session

from fac.adapters.edp.adapter import EdpImportReport, EdpImportRequest
from fac.adapters.edp_mock.adapter import EdpAdapter
from fac.adapters.edp_mock.models import EdpFixture
from fac.infrastructure.repositories import EdpRepository, RevisionConflict
from fac.settings import Settings


class EbmsApiError(RuntimeError):
    """The configured EBMS endpoint could not fulfil a read request."""


@dataclass(slots=True)
class _EbmsApiClient:
    base_url: str
    api_key: str
    timeout: float

    def get(self, path: str, params: dict[str, object] | None = None) -> dict:
        query = urllib.parse.urlencode(
            {key: value for key, value in (params or {}).items() if value is not None}
        )
        url = f"{self.base_url.rstrip('/')}{path}"
        if query:
            url = f"{url}?{query}"
        headers = {"Accept": "application/json"}
        if self.api_key.strip():
            headers["Authorization"] = f"Bearer {self.api_key.strip()}"
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:300]
            raise EbmsApiError(f"EBMS {exc.code} {path}: {body}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise EbmsApiError(f"EBMS 请求失败 {path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise EbmsApiError(f"EBMS 响应格式错误 {path}")
        return payload


@dataclass(slots=True)
class EbmsApiAdapter:
    session: Session
    settings: Settings
    client: _EbmsApiClient | None = None

    def __post_init__(self) -> None:
        if self.client is None:
            self.client = _EbmsApiClient(
                self.settings.ebms_base_url,
                self.settings.ebms_api_key,
                self.settings.ebms_timeout_seconds,
            )

    def import_orders(
        self, request: EdpImportRequest, *, import_id: str | None = None
    ) -> EdpImportReport:
        if not self.settings.ebms_base_url.strip():
            raise EbmsApiError("FAC_EBMS_BASE_URL 未配置，无法从 EBMS 导入实际数据")
        assert self.client is not None
        params: dict[str, object] = {
            "page": 1,
            "limit": min(request.limit, self.settings.ebms_order_limit),
        }
        if request.order_no:
            params["keyword"] = request.order_no
        payload = self.client.get("/api/order-analysis", params)
        rows = self._items(payload)
        if request.order_no:
            rows = [row for row in rows if str(row.get("order_no", "")) == request.order_no]
        if not rows:
            raise EbmsApiError(
                f"EBMS 未返回订单数据{f'（{request.order_no}）' if request.order_no else ''}"
            )

        fixture = EdpFixture(tenant_id=request.tenant_id or self.settings.tenant_id)
        raw_rows: list[dict] = []
        counts = {"orders": 0, "boms": 0}
        rejected: list[dict] = []
        available = {"orders"}
        has_plan = False
        has_actual = False
        has_material_prices = False
        has_labor = False
        has_expenses = False

        for row in rows:
            order_no = str(row.get("order_no") or row.get("id") or "").strip()
            if not order_no:
                rejected.append({"object_type": "Order", "object_id": None, "reasons": ["缺少 order_no"]})
                continue
            raw_rows.append(row)
            has_plan = has_plan or row.get("plan_total_cost") is not None
            has_actual = has_actual or row.get("actual_total_cost") is not None
            try:
                detail = self._detail(row)
                order, products = self._order(row, detail)
                fixture.orders.append(order)
                counts["orders"] += 1
                for product in products:
                    bom = self._bom(product, row)
                    if bom:
                        fixture.boms.append(bom)
                        counts["boms"] += 1
                        has_material_prices = has_material_prices or any(
                            line.get("unit_price") not in (None, 0, "0") for line in product.get("tree", [])
                        )
                        has_labor = has_labor or any(
                            line.get("labor_amount") not in (None, 0, "0") for line in product.get("tree", [])
                        )
                        has_expenses = has_expenses or any(
                            line.get("expense_amount") not in (None, 0, "0") for line in product.get("tree", [])
                        )
            except (KeyError, TypeError, ValueError, InvalidOperation, EbmsApiError) as exc:
                rejected.append({"object_type": "Order", "object_id": order_no, "reasons": [str(exc)]})

        if counts["orders"] == 0:
            raise EbmsApiError("EBMS 返回的订单均无法转换为 FAC 订单事实")
        report = EdpAdapter(self.session).import_fixture(fixture)
        raw_report = self._store_raw_rows(fixture.tenant_id, raw_rows, rejected)
        report.accepted_count += raw_report["accepted"]
        report.skipped_count += raw_report["skipped"]
        report.rejected_count += raw_report["rejected"]
        self.session.commit()

        for name, present in (
            ("boms", counts["boms"] > 0),
            ("plan_costs", has_plan),
            ("actual_costs", has_actual),
            ("material_prices", has_material_prices),
            ("labor", has_labor),
            ("expenses", has_expenses),
        ):
            if present:
                available.add(name)
        missing = [
            name
            for name in ("boms", "material_prices", "labor", "expenses", "fx_rates")
            if name not in available
        ]
        return EdpImportReport(
            import_id=import_id or f"ebms-import-{uuid4().hex[:16]}",
            source=self.settings.ebms_source_system,
            status="SUCCEEDED" if not rejected else "PARTIAL",
            requested_order=request.order_no,
            accepted_count=report.accepted_count,
            skipped_count=report.skipped_count,
            rejected_count=report.rejected_count,
            orders=counts["orders"],
            boms=counts["boms"],
            available_data=sorted(available),
            missing_data=missing,
            rejected=[*report.rejected, *rejected],
            message="已从 EBMS 订单核算接口导入实际订单、计划/实际成本与可用 BOM 事实。",
        )

    def _detail(self, row: dict) -> dict:
        assert self.client is not None
        record_id = row.get("id")
        if record_id is None:
            return {"products": []}
        try:
            return self.client.get(f"/api/order-analysis/{urllib.parse.quote(str(record_id), safe='')}/line-items")
        except EbmsApiError:
            try:
                return self.client.get(f"/api/order-analysis/{urllib.parse.quote(str(record_id), safe='')}/details")
            except EbmsApiError:
                return {"products": []}

    def _order(self, row: dict, detail: dict) -> tuple[dict, list[dict]]:
        products = self._items(detail, key="products")
        product_code = str(row.get("product_code") or (products[0].get("product_code") if products else "") or "").strip()
        if not product_code:
            raise ValueError("订单缺少可用于核算的 product_code")
        quantity = self._number(row.get("quantity"), default=0)
        if quantity <= 0 and products:
            quantity = self._number(products[0].get("quantity"), default=0)
        if quantity <= 0:
            raise ValueError("订单缺少有效 quantity")
        amount = self._number(row.get("order_amount"), default=0)
        unit_price = amount / quantity if quantity else amount
        currency = str(row.get("currency") or "CNY").upper()
        customer = str(row.get("customer_name") or "EBMS-UNKNOWN")
        return (
            {
                "object_id": str(row.get("order_no") or row.get("id")),
                "source_system": self.settings.ebms_source_system,
                "revision": 1,
                "customer_id": customer,
                "product_id": product_code,
                "quantity": quantity,
                "unit_price": {"amount": unit_price, "currency": currency},
                "order_date": self._date(row.get("promised_date") or row.get("created_at")),
                "amount": amount,
                "currency": currency,
                "delivery_date": self._date(row.get("promised_date")),
                "lines": products,
                "evidence_hint": {"source": "ebms", "order_id": row.get("id")},
            },
            products,
        )

    def _bom(self, product: dict, row: dict) -> dict | None:
        code = str(product.get("bom_no") or product.get("product_code") or "").strip()
        lines: list[dict] = []
        for item in self._flatten_tree(product.get("tree") or product.get("rows") or [product]):
            material = str(item.get("material_code") or "").strip()
            quantity = self._number(item.get("bom_qty") or item.get("total_qty"), default=0)
            if not material or quantity <= 0:
                continue
            kind = "SELF_MADE" if str(item.get("material_attr")) in {"自制", "委外加工"} else "MATERIAL"
            lines.append(
                {
                    "material_id": material,
                    "quantity": quantity,
                    "uom": str(item.get("unit") or "EA"),
                    "kind": kind,
                }
            )
        if not code or not lines:
            return None
        return {
            "object_id": f"BOM:{code}",
            "source_system": self.settings.ebms_source_system,
            "revision": 1,
            "product_id": str(product.get("product_code") or row.get("product_code") or code),
            "lines": lines,
        }

    def _store_raw_rows(self, tenant_id: str, rows: list[dict], rejected: list[dict]) -> dict[str, int]:
        repo = EdpRepository(self.session)
        result = {"accepted": 0, "skipped": 0, "rejected": 0}
        for row in rows:
            object_id = str(row.get("order_no") or row.get("id") or "")
            if not object_id:
                continue
            ref = self._raw_ref(object_id, row)
            try:
                if repo.add(tenant_id, ref, row):
                    result["accepted"] += 1
                else:
                    result["skipped"] += 1
            except RevisionConflict as exc:
                rejected.append({"object_type": "EBMSOrderAnalysis", "object_id": object_id, "reasons": [str(exc)]})
                result["rejected"] += 1
        return result

    def _raw_ref(self, object_id: str, row: dict):
        from fac.contracts.common import ObjectRef

        digest = hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()
        revision = int(digest[:8], 16) or 1
        return ObjectRef("EBMSOrderAnalysis", object_id, self.settings.ebms_source_system, revision)

    @staticmethod
    def _items(payload: dict, *, key: str = "data") -> list[dict]:
        value = payload.get(key)
        if value is None and key == "data":
            value = payload.get("items")
        if value is None and isinstance(payload.get("data"), dict):
            value = payload["data"].get(key) or payload["data"].get("items")
        if value is None:
            return []
        if not isinstance(value, list):
            raise EbmsApiError(f"EBMS 响应字段 {key} 格式错误")
        return [item for item in value if isinstance(item, dict)]

    @classmethod
    def _flatten_tree(cls, nodes: list[dict]) -> list[dict]:
        result: list[dict] = []
        for node in nodes:
            result.append(node)
            children = node.get("children")
            if isinstance(children, list):
                result.extend(cls._flatten_tree([child for child in children if isinstance(child, dict)]))
        return result

    @staticmethod
    def _number(value: object, *, default: float = 0) -> float:
        if value is None or value == "":
            return default
        try:
            return float(Decimal(str(value)))
        except (InvalidOperation, ValueError, TypeError):
            return default

    @staticmethod
    def _date(value: object) -> str:
        return str(value or datetime.now(UTC).date().isoformat())[:10]
