from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Session, create_engine, select

from backend.app.db.base import SQLModel
from backend.app.models.fx import FxRate, FxRateSet
from backend.app.services.fx import freeze_api_rate_set, freeze_manual_rate_set


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


class FakeFxProvider:
    def quote(
        self,
        base_currency: str,
        currencies: list[str],
        rate_timestamp: datetime,
    ) -> dict[str, Decimal]:
        assert base_currency == "CNY"
        assert currencies == ["USD"]
        assert rate_timestamp.tzinfo is not None
        return {"USD": Decimal("7.25000000")}


def test_api_provider_freezes_decimal_rates(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        rate_set = freeze_api_rate_set(
            session,
            provider=FakeFxProvider(),
            base_currency="CNY",
            currencies=["USD"],
            rate_timestamp=datetime(2026, 3, 31, 16, tzinfo=UTC),
        )

    with Session(engine) as session:
        saved_set = session.exec(select(FxRateSet)).one()
        saved_rate = session.exec(select(FxRate)).one()

    assert saved_set.id == rate_set.id
    assert saved_set.rate_source == "api"
    assert saved_rate.currency == "USD"
    assert saved_rate.rate_to_base == "7.25000000"
