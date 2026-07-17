from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class BalanceSheetItemTemplate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="owner.id", index=True)
    item_type: str
    system_category_id: int = Field(foreign_key="systemcategory.id", index=True)
    account_name: str
    institution_name: str | None = None
    currency: str
    display_order: int = 0
    active: bool = True
    note: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class BalanceSheetItemTemplateTag(SQLModel, table=True):
    template_id: int = Field(
        foreign_key="balancesheetitemtemplate.id",
        primary_key=True,
    )
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)
