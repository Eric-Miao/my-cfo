from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class Owner(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    display_order: int = 0
    active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
