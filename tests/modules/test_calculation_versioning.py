import pytest

from fac.contracts.common import ObjectRef
from fac.infrastructure.db import make_engine, make_session_factory
from fac.infrastructure.models import Base, CalculationRun, CalculationSnapshot
from fac.infrastructure.repositories import CoreRepository, EdpRepository
from fac.modules.calculation.service import CalculationService


def test_edp_backed_result_versions_are_immutable_and_replayable(tmp_path):
    from decimal import Decimal as D

    from fac.infrastructure.models import CalculationResult
    from fac.modules.ofa.engine import OFAEngine
    from fac.modules.ofa.ports import EdpOFAPorts

    engine = make_engine(f"sqlite:///{tmp_path / 'results.db'}")
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    order_ref = ObjectRef("Order", "o1", "mock", 1)
    bom_ref = ObjectRef("BOM", "b1", "mock", 1)
    p1 = ObjectRef("MaterialPrice", "p1", "mock", 1)
    p2 = ObjectRef("MaterialPrice", "p1", "mock", 2)
    with factory() as session:
        edp = EdpRepository(session)
        edp.add(
            "t1",
            order_ref,
            {
                "object_id": "o1",
                "product_id": "product",
                "quantity": "2",
                "order_date": "2026-10-07",
            },
        )
        edp.add(
            "t1",
            bom_ref,
            {
                "product_id": "product",
                "lines": [{"material_id": "steel", "quantity": "3", "uom": "kg"}],
            },
        )
        for ref, value in ((p1, "4"), (p2, "5")):
            edp.add(
                "t1",
                ref,
                {
                    "material_id": "steel",
                    "unit_price": {"amount": value, "currency": "CNY"},
                    "uom": "kg",
                    "effective_at": "2026-01-01",
                },
            )
        session.commit()

        service = CalculationService(session, "t1")
        ports = EdpOFAPorts(session, "t1")
        first = service.start(
            "Order", "o1", [order_ref, bom_ref, p1], "v1", "manual", "initial", "alice"
        )
        order_input = ports.get_order(order_ref, first)
        first_result = OFAEngine(session).calculate_plan_cost(order_input, ports, first)
        assert first_result.total_cost.to_functional() == D("24.00")
        replay = OFAEngine(session).calculate_plan_cost(order_input, ports, first)
        assert replay == first_result

        second = service.start(
            "Order", "o1", [order_ref, bom_ref, p2], "v1", "manual", "price update", "alice"
        )
        second_result = OFAEngine(session).calculate_plan_cost(
            ports.get_order(order_ref, second), ports, second
        )
        assert second_result.total_cost.to_functional() == D("30.00")
        assert second_result.previous_result_id == first_result.result_id
        assert second_result.version == 2
        assert (
            CoreRepository(session)
            .get(CalculationResult, "t1", first_result.result_id, "fac", 1)
            .payload["total_cost"]["functional_amount"]
            == "24.00"
        )
        assert (
            CoreRepository(session)
            .get(CalculationResult, "t1", second_result.result_id, "fac", 2)
            .payload["total_cost"]["functional_amount"]
            == "30.00"
        )
    with factory() as session:
        from dataclasses import replace

        assert EdpOFAPorts(session, "t1").get_material_prices("steel", first)[
            0
        ].unit_price.amount == D(4)
        assert OFAEngine(session).get_result(first).total_cost.to_functional() == D("24.00")
        assert OFAEngine(session).get_result(second).total_cost.to_functional() == D("30.00")
        assert OFAEngine(session).get_result(replace(first, tenant_id="other")) is None
        with pytest.raises(ValueError, match="snapshot checksum"):
            OFAEngine(session).get_result(replace(first, checksum="0" * 64))


def test_replay_and_revision_changes_preserve_snapshots(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'versions.db'}")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session:
        edp = EdpRepository(session)
        refs = [
            ObjectRef(kind, name, "mock", 1)
            for kind, name in (
                ("Order", "o1"),
                ("BOM", "b1"),
                ("MaterialPrice", "p1"),
                ("FX", "f1"),
            )
        ]
        for ref in refs:
            edp.add("t1", ref, {"revision": 1})
        service = CalculationService(session, "t1")

        first = service.start("Order", "o1", refs, "v1", "manual", "initial", "alice")
        replay = service.start(
            "Order", "o1", list(reversed(refs)), "v1", "manual", "initial", "alice"
        )
        assert replay == first
        assert isinstance(first.input_refs, tuple)
        assert len(first.checksum) == 64

        versions = []
        for index in (1, 2, 3):
            changed = list(refs)
            old = changed[index]
            changed[index] = ObjectRef(old.object_type, old.object_id, old.source_system, 2)
            edp.add("t1", changed[index], {"revision": 2})
            versions.append(
                service.start("Order", "o1", changed, "v1", "manual", "change", "alice")
            )
        versions.append(service.start("Order", "o1", refs, "v2", "manual", "rule", "alice"))
        assert [item.version for item in (first, *versions)] == [1, 2, 3, 4, 5]
        assert len({item.checksum for item in (first, *versions)}) == 5

        repo = CoreRepository(session)
        original_run = repo.get(CalculationRun, "t1", first.calculation_id, "fac", 1)
        original_snapshot = repo.get(CalculationSnapshot, "t1", first.snapshot_id, "fac", 1)
        assert original_run.payload["snapshot_id"] == first.snapshot_id
        assert original_snapshot.payload["checksum"] == first.checksum
        assert original_snapshot.payload["rule_set_version"] == "v1"
        assert len(original_snapshot.payload["input_refs"]) == 4
        assert service.get("Order", "o1", 1) == first
        assert service.get("Order", "o1", 5) == versions[-1]
        assert CalculationService(session, "other").get("Order", "o1", 1) is None
        original_snapshot.payload = {**original_snapshot.payload, "rule_set_version": "tampered"}
        session.flush()
        with pytest.raises(ValueError, match="snapshot checksum"):
            service.get("Order", "o1", 1)


def test_start_rejects_unfrozen_or_cross_tenant_edp_ref(tmp_path):
    import pytest

    engine = make_engine(f"sqlite:///{tmp_path / 'missing.db'}")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session:
        ref = ObjectRef("Order", "o1", "mock", 1)
        EdpRepository(session).add("other", ref, {"quantity": "1"})
        with pytest.raises(ValueError, match="missing EDP reference"):
            CalculationService(session, "t1").start(
                "Order", "o1", [ref], "v1", "manual", "initial", "alice"
            )


def test_import_preserves_ofa_bom_and_price_policy_fields(tmp_path):
    from fac.adapters.edp_mock.adapter import EdpAdapter
    from fac.adapters.edp_mock.models import EdpFixture
    from fac.modules.ofa.ports import EdpOFAPorts

    engine = make_engine(f"sqlite:///{tmp_path / 'import.db'}")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session:
        fixture = EdpFixture(
            tenant_id="t1",
            boms=[
                {
                    "object_id": "b1",
                    "source_system": "mock",
                    "revision": 1,
                    "product_id": "p",
                    "lines": [
                        {
                            "material_id": "m",
                            "quantity": "1000",
                            "uom": "g",
                            "price_uom": "kg",
                            "conversion_factor": "0.001",
                            "kind": "OUTSOURCE",
                            "processing_price": {"amount": "2", "currency": "CNY"},
                        }
                    ],
                }
            ],
            material_prices=[
                {
                    "object_id": "pr1",
                    "source_system": "mock",
                    "revision": 1,
                    "material_id": "m",
                    "unit_price": {"amount": "3", "currency": "CNY"},
                    "uom": "kg",
                    "effective_at": "2026-01-01",
                    "override": True,
                }
            ],
        )
        assert EdpAdapter(session).import_fixture(fixture).accepted_count == 2
        refs = [ObjectRef("BOM", "b1", "mock", 1), ObjectRef("MaterialPrice", "pr1", "mock", 1)]
        ctx = CalculationService(session, "t1").start(
            "Order", "o1", refs, "v1", "manual", "test", "alice"
        )
        ports = EdpOFAPorts(session, "t1")
        line = ports.get_bom("p", ctx).lines[0]
        assert line.kind == "OUTSOURCE"
        assert str(line.conversion_factor) == "0.001"
        assert line.price_uom == "kg"
        assert str(line.processing_price.amount) == "2"
        assert ports.get_material_prices("m", ctx)[0].override is True


def test_plan_result_migration_creates_queryable_table(tmp_path, monkeypatch):
    from pathlib import Path

    from alembic.config import Config
    from sqlalchemy import inspect

    from alembic import command

    url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setenv("FAC_DATABASE_URL", url)
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.upgrade(config, "head")
    assert "calculation_results" in inspect(make_engine(url)).get_table_names()


def test_bom_price_fx_and_rule_revisions_each_create_result_version(tmp_path):
    from decimal import Decimal as D

    from fac.modules.ofa.engine import OFAEngine
    from fac.modules.ofa.ports import EdpOFAPorts

    engine = make_engine(f"sqlite:///{tmp_path / 'all_changes.db'}")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session:
        edp = EdpRepository(session)
        order = ObjectRef("Order", "o", "mock", 1)
        bom1 = ObjectRef("BOM", "b", "mock", 1)
        bom2 = ObjectRef("BOM", "b", "mock", 2)
        cny = ObjectRef("MaterialPrice", "p-cny", "mock", 1)
        usd = ObjectRef("MaterialPrice", "p-usd", "mock", 1)
        fx1 = ObjectRef("FX", "usd-cny", "mock", 1)
        fx2 = ObjectRef("FX", "usd-cny", "mock", 2)
        edp.add("t", order, {"product_id": "p", "quantity": "1", "order_date": "2026-10-07"})
        for ref, quantity in ((bom1, "2"), (bom2, "3")):
            edp.add("t", ref, {"product_id": "p", "lines": [
                {"material_id": "m", "quantity": quantity, "uom": "kg"}]})
        for ref, currency in ((cny, "CNY"), (usd, "USD")):
            edp.add("t", ref, {"material_id": "m", "unit_price":
                               {"amount": "4", "currency": currency},
                               "uom": "kg", "effective_at": "2026-01-01"})
        for ref, rate in ((fx1, "7"), (fx2, "8")):
            edp.add("t", ref, {"base_currency": "USD", "quote_currency": "CNY",
                               "rate": rate, "rate_type": "spot", "effective_at": "2026-01-01",
                               "evidence_ref": f"fx-{ref.revision}"})
        service = CalculationService(session, "t")
        ports = EdpOFAPorts(session, "t")
        inputs = [([order, bom1, cny], "v1"), ([order, bom2, cny], "v1"),
                  ([order, bom2, usd, fx1], "v1"), ([order, bom2, usd, fx2], "v1"),
                  ([order, bom2, usd, fx2], "v2")]
        contexts = []
        results = []
        for refs, rule in inputs:
            ctx = service.start("Order", "o", refs, rule, "manual", "revision", "alice")
            contexts.append(ctx)
            results.append(OFAEngine(session).calculate_plan_cost(
                ports.get_order(order, ctx), ports, ctx
            ))
        assert [ctx.version for ctx in contexts] == [1, 2, 3, 4, 5]
        assert [result.total_cost.to_functional() for result in results] == [
            D("8.00"), D("12.00"), D("84.00"), D("96.00"), D("96.00")]
        assert results[3].fx_usages[0].rate.evidence_ref == "fx-2"
        assert OFAEngine(session).get_result(contexts[0]).total_cost.to_functional() == D("8.00")
        assert OFAEngine(session).get_result(contexts[2]).fx_usages[0].rate.revision == 1
