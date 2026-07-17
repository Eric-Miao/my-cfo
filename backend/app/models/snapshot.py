from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class OwnerSnapshot(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="owner.id", index=True)
    reporting_at: str
    status: str
    source: str
    label: str | None = None
    replaces_snapshot_id: int | None = Field(
        default=None,
        foreign_key="ownersnapshot.id",
    )
    superseded_by_snapshot_id: int | None = Field(
        default=None,
        foreign_key="ownersnapshot.id",
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    confirmed_at: datetime | None = None
    superseded_at: datetime | None = None
    revision_note: str | None = None


class SnapshotItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_snapshot_id: int = Field(foreign_key="ownersnapshot.id", index=True)
    template_id: int = Field(foreign_key="balancesheetitemtemplate.id", index=True)
    item_type: str
    system_category_id: int = Field(foreign_key="systemcategory.id", index=True)
    system_category_code_snapshot: str
    system_category_name_snapshot: str
    account_name_snapshot: str
    institution_name_snapshot: str | None = None
    currency: str
    amount_original: str | None = None
    note: str | None = None
    display_order: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SnapshotItemTag(SQLModel, table=True):
    snapshot_item_id: int = Field(foreign_key="snapshotitem.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)
    tag_name_snapshot: str
