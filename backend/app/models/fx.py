from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class FxRateSet(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    base_currency: str
    rate_source: str
    rate_timestamp: str
    created_at: datetime = Field(default_factory=utc_now)
    note: str | None = None


class FxRate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    fx_rate_set_id: int = Field(foreign_key="fxrateset.id", index=True)
    currency: str
    rate_to_base: str
