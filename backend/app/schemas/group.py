from pydantic import BaseModel

from backend.app.models.group import (
    SnapshotGroup,
    SnapshotGroupMember,
    SnapshotGroupRevision,
)
from backend.app.models.snapshot import OwnerSnapshot
from backend.app.schemas.ids import public_id


class SnapshotGroupMemberInput(BaseModel):
    owner_id: str
    owner_snapshot_id: str


class SnapshotGroupCreate(BaseModel):
    label: str | None = None
    members: list[SnapshotGroupMemberInput]


class SnapshotGroupFinalizeRequest(BaseModel):
    fx_rates: "FxFinalizeRequest"


class SnapshotGroupMemberRead(BaseModel):
    owner_id: str
    owner_snapshot_id: str
    owner_snapshot_reporting_at: str

    @classmethod
    def from_model(
        cls,
        member: SnapshotGroupMember,
        snapshot: OwnerSnapshot,
    ) -> "SnapshotGroupMemberRead":
        return cls(
            owner_id=public_id("owner", member.owner_id),
            owner_snapshot_id=public_id("snap", member.owner_snapshot_id),
            owner_snapshot_reporting_at=snapshot.reporting_at,
        )


class SnapshotGroupRevisionRead(BaseModel):
    id: str
    snapshot_group_id: str
    revision_number: int
    status: str
    base_currency: str
    fx_rate_set_id: str | None
    members: list[SnapshotGroupMemberRead]
    note: str | None

    @classmethod
    def from_model(
        cls,
        revision: SnapshotGroupRevision,
        members: list[SnapshotGroupMemberRead],
    ) -> "SnapshotGroupRevisionRead":
        return cls(
            id=public_id("rev", revision.id),
            snapshot_group_id=public_id("group", revision.snapshot_group_id),
            revision_number=revision.revision_number,
            status=revision.status,
            base_currency=revision.base_currency,
            fx_rate_set_id=(
                public_id("fxset", revision.fx_rate_set_id)
                if revision.fx_rate_set_id
                else None
            ),
            members=members,
            note=revision.note,
        )


class SnapshotGroupRead(BaseModel):
    id: str
    reporting_at: str
    label: str | None
    active_revision: SnapshotGroupRevisionRead | None

    @classmethod
    def from_model(
        cls,
        group: SnapshotGroup,
        active_revision: SnapshotGroupRevisionRead | None,
    ) -> "SnapshotGroupRead":
        return cls(
            id=public_id("group", group.id),
            reporting_at=group.reporting_at,
            label=group.label,
            active_revision=active_revision,
        )


from backend.app.schemas.fx import FxFinalizeRequest  # noqa: E402

SnapshotGroupFinalizeRequest.model_rebuild()
