import pytest
from fastapi.testclient import TestClient

from fac.adapters.ebms.adapter import EbmsApiError
from fac.adapters.edp.adapter import EdpApiError, EdpImportReport, EdpImportRequest
from fac.adapters.priority import PriorityImportAdapter, SourceImportError
from fac.api.routes import imports as import_routes
from fac.infrastructure.db import make_engine, make_session_factory
from fac.infrastructure.models import Base, EdpProjection
from fac.main import create_app
from fac.settings import Settings


def _session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'import.db'}")
    Base.metadata.create_all(engine)
    return make_session_factory(engine)


def _report(source: str) -> EdpImportReport:
    return EdpImportReport(
        import_id="import-1",
        source=source,
        status="SUCCEEDED",
        orders=1,
        available_data=["orders"],
    )


class _Adapter:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = 0

    def import_orders(self, request, *, import_id=None):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


def test_edp_success_does_not_call_ebms():
    edp = _Adapter(result=_report("edp"))
    ebms = _Adapter(result=_report("ebms"))

    report = PriorityImportAdapter(edp=edp, ebms=ebms).import_orders(
        EdpImportRequest(limit=10), import_id="import-1"
    )

    assert report.source == "edp"
    assert report.source_chain == ["edp"]
    assert report.fallback_reason is None
    assert edp.calls == 1
    assert ebms.calls == 0


def test_edp_unavailable_falls_back_to_ebms_and_records_reason():
    edp = _Adapter(error=EdpApiError("EDP timeout"))
    ebms = _Adapter(result=_report("ebms"))

    report = PriorityImportAdapter(edp=edp, ebms=ebms).import_orders(
        EdpImportRequest(limit=10), import_id="import-1"
    )

    assert report.source == "ebms"
    assert report.source_chain == ["edp", "ebms"]
    assert report.fallback_reason == "EDP timeout"
    assert edp.calls == 1
    assert ebms.calls == 1


def test_both_sources_unavailable_is_explicit_failure():
    edp = _Adapter(error=EdpApiError("EDP 未配置"))
    ebms = _Adapter(error=EbmsApiError("EBMS 未配置"))

    with pytest.raises(SourceImportError) as exc_info:
        PriorityImportAdapter(edp=edp, ebms=ebms).import_orders(
            EdpImportRequest(limit=10), import_id="import-1"
        )

    assert "EDP 未配置" in str(exc_info.value)
    assert "EBMS 未配置" in str(exc_info.value)


class _FakeEbmsClient:
    def get(self, path, params=None):
        if path == "/api/order-analysis":
            return {
                "data": [
                    {
                        "id": 7,
                        "order_no": "EBMS-001",
                        "customer_name": "EBMS客户",
                        "product_code": "P-EBMS",
                        "quantity": 4,
                        "order_amount": 800,
                        "plan_total_cost": 500,
                        "actual_total_cost": 520,
                        "promised_date": "2026-11-10",
                    }
                ]
            }
        if path == "/api/order-analysis/7/line-items":
            return {
                "products": [
                    {
                        "product_code": "P-EBMS",
                        "bom_no": "BOM-EBMS",
                        "quantity": 4,
                        "tree": [
                            {
                                "material_code": "M-EBMS",
                                "bom_qty": 2,
                                "unit": "EA",
                                "material_attr": "外购",
                                "unit_price": 10,
                            }
                        ],
                    }
                ]
            }
        raise AssertionError((path, params))


def test_ebms_fallback_maps_order_bom_and_preserves_cost_facts(tmp_path):
    from fac.adapters.ebms.adapter import EbmsApiAdapter

    factory = _session(tmp_path)
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'import.db'}",
        tenant_id="tenant-a",
        ebms_base_url="http://ebms.test",
    )
    with factory() as session:
        report = EbmsApiAdapter(session, settings, client=_FakeEbmsClient()).import_orders(
            EdpImportRequest(tenant_id="tenant-a", limit=10)
        )

        assert report.source == "ebms"
        assert report.orders == 1
        assert report.boms == 1
        assert "plan_costs" in report.available_data
        assert "actual_costs" in report.available_data
        assert session.query(EdpProjection).filter_by(object_type="Order").count() == 1
        assert session.query(EdpProjection).filter_by(object_type="BOM").count() == 1
        assert session.query(EdpProjection).filter_by(object_type="EBMSOrderAnalysis").count() == 1
    response = TestClient(create_app(session_factory=factory)).get(
        "/api/v1/fac/orders?tenant_id=tenant-a"
    )
    assert response.status_code == 200
    assert response.json()[0]["payload"]["ebms_analysis"]["actual_total_cost"] == 520


def test_import_route_reports_ebms_fallback_source(tmp_path, monkeypatch):
    factory = _session(tmp_path)
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'import.db'}",
        tenant_id="default-tenant",
        ebms_base_url="http://ebms.test",
    )

    class _UnavailableEdp:
        def __init__(self, session, settings):
            pass

        def import_orders(self, request, *, import_id=None):
            raise EdpApiError("EDP 请求超时")

    class _AvailableEbms:
        def __init__(self, session, settings):
            pass

        def import_orders(self, request, *, import_id=None):
            return EdpImportReport(
                import_id=import_id or "import-1",
                source="ebms",
                status="SUCCEEDED",
                orders=2,
                source_chain=["edp", "ebms"],
                fallback_reason="EDP 请求超时",
            )

    monkeypatch.setattr(import_routes, "get_settings", lambda: settings)
    monkeypatch.setattr(import_routes, "EdpApiAdapter", _UnavailableEdp)
    monkeypatch.setattr(import_routes, "EbmsApiAdapter", _AvailableEbms)

    response = TestClient(create_app(session_factory=factory)).post(
        "/api/v1/fac/edp/import", json={"limit": 10}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "ebms"
    assert body["source_chain"] == ["edp", "ebms"]
    status = TestClient(create_app(session_factory=factory)).get("/api/v1/fac/edp/status")
    assert status.json()["last_import"]["source"] == "ebms"
