from sqlmodel import Session, create_engine, select

from backend.app.db.base import SQLModel
from backend.app.models.fx import FxRate, FxRateSet
from backend.app.services.fx import freeze_manual_rate_set


def test_manual_fallback_freezes_supplied_rates(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        rate_set = freeze_manual_rate_set(
            session,
            base_currency="CNY",
            manual_rates=[{"currency": "USD", "rate_to_base": "7.25000000"}],
            rate_timestamp="2026-03-31T16:00:00Z",
        )

    with Session(engine) as session:
        saved_set = session.exec(select(FxRateSet)).one()
        saved_rate = session.exec(select(FxRate)).one()

    assert saved_set.id == rate_set.id
    assert saved_set.base_currency == "CNY"
    assert saved_set.rate_source == "manual"
    assert saved_rate.currency == "USD"
    assert saved_rate.rate_to_base == "7.25000000"
