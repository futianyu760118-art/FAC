from fac.contracts.common import ObjectRef
from fac.infrastructure.db import make_engine, make_session_factory
from fac.infrastructure.models import (
    Base,
    CalculationRun,
    CalculationSnapshot,
    EventRecord,
    Evidence,
)
from fac.infrastructure.repositories import CoreRepository, EdpRepository


def test_edp_repository_scopes_revision_and_tenant(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'repo.db'}")
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    with factory() as session:
        repo = EdpRepository(session)
        one = ObjectRef("Order", "O-1", "edp-mock", 1)
        two = ObjectRef("Order", "O-1", "edp-mock", 2)
        assert repo.add("tenant-a", one, {"amount": "100"}) is True
        assert repo.add("tenant-a", one, {"amount": "999"}) is False
        assert repo.add("tenant-a", two, {"amount": "200"}) is True
        assert repo.get("tenant-a", one).payload["amount"] == "100"
        assert repo.get("tenant-a", two).payload["amount"] == "200"
        assert repo.get("tenant-b", one) is None


def test_core_repository_scopes_records_by_tenant_and_revision(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'core.db'}")
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    with factory() as session:
        repo = CoreRepository(session)
        for model in (CalculationRun, CalculationSnapshot, Evidence, EventRecord):
            repo.add(model, "tenant-a", "record-1", "fac", 1, {"state": "first"})
            repo.add(model, "tenant-a", "record-1", "fac", 2, {"state": "second"})
            assert repo.get(model, "tenant-a", "record-1", "fac", 1).payload == {"state": "first"}
            assert repo.get(model, "tenant-a", "record-1", "fac", 2).payload == {"state": "second"}
            assert repo.get(model, "tenant-b", "record-1", "fac", 1) is None
