from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class SystemCategory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    item_type: str
    code: str = Field(index=True)
    name: str
    calculation_role: str
    active: bool = True
    display_order: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
