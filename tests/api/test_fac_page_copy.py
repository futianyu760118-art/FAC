from fastapi.testclient import TestClient

from fac.main import create_app


def test_formal_fac_page_uses_product_copy_and_formal_api_hooks(monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "false")

    response = TestClient(create_app()).get("/fac")

    assert response.status_code == 200
    for text in (
        "M09 · 财经工作台",
        "订单财经分析",
        "规则与期间",
        "结果与证据",
        "待外部处理",
        "计算订单",
        "/api/v1/fac/orders",
        "/api/v1/fac/external-requests",
        "/api/v1/fac/results/",
    ):
        assert text in response.text


def test_formal_fac_page_does_not_expose_demo_copy(monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "false")

    response = TestClient(create_app()).get("/fac")

    assert response.status_code == 200
    for text in (
        "运行联调演示",
        "FAC-DEMO-2025-01",
        "demo-tenant",
        "本地联调沙箱",
        "中文演示数据",
        "/api/v1/demo/",
    ):
        assert text not in response.text


def test_formal_fac_page_does_not_offer_fake_external_action(monkeypatch):
    monkeypatch.setenv("FAC_DEMO_ENABLED", "false")

    response = TestClient(create_app()).get("/fac")

    assert response.status_code == 200
    assert "创建示例动作" not in response.text
    assert "POMS 动作已创建" not in response.text
    assert "查看待外部处理" in response.text
    assert "/api/v1/fac/external-requests" in response.text
