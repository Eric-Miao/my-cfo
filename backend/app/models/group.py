from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class SnapshotGroup(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    reporting_at: str
    label: str | None = None
    active_revision_id: int | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SnapshotGroupRevision(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    snapshot_group_id: int = Field(foreign_key="snapshotgroup.id", index=True)
    revision_number: int
    status: str
    base_currency: str
    fx_rate_set_id: int | None = Field(default=None, foreign_key="fxrateset.id")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    finalized_at: datetime | None = None
    superseded_at: datetime | None = None
    note: str | None = None


class SnapshotGroupMember(SQLModel, table=True):
    snapshot_group_revision_id: int = Field(
        foreign_key="snapshotgrouprevision.id",
        primary_key=True,
    )
    owner_id: int = Field(foreign_key="owner.id", primary_key=True)
    owner_snapshot_id: int = Field(foreign_key="ownersnapshot.id", index=True)
