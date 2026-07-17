from datetime import UTC, datetime

from sqlmodel import Session, select

from backend.app.api.errors import ApiError
from backend.app.core.config import settings
from backend.app.models.group import (
    SnapshotGroup,
    SnapshotGroupMember,
    SnapshotGroupRevision,
)
from backend.app.models.owner import Owner
from backend.app.models.snapshot import OwnerSnapshot
from backend.app.schemas.fx import FxFinalizeRequest
from backend.app.schemas.group import SnapshotGroupCreate
from backend.app.schemas.ids import parse_public_id
from backend.app.services.fx import freeze_manual_rate_set


def utc_iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _get_group(session: Session, group_public_id: str) -> SnapshotGroup:
    group = session.get(SnapshotGroup, parse_public_id("group", group_public_id))
    if group is None:
        raise ApiError(404, "not_found", "Snapshot group was not found.")
    return group


def active_revision(
    session: Session,
    group: SnapshotGroup,
) -> SnapshotGroupRevision | None:
    if group.active_revision_id is None:
        return None
    return session.get(SnapshotGroupRevision, group.active_revision_id)


def revision_members(
    session: Session,
    revision_id: int | None,
) -> list[SnapshotGroupMember]:
    return list(
        session.exec(
            select(SnapshotGroupMember)
            .where(SnapshotGroupMember.snapshot_group_revision_id == revision_id)
            .order_by(SnapshotGroupMember.owner_id)
        )
    )


def validate_members(
    session: Session,
    members: list,
) -> list[tuple[int, int]]:
    active_owner_ids = {
        owner.id for owner in session.exec(select(Owner).where(Owner.active.is_(True)))
    }
    member_owner_ids: set[int] = set()
    validated: list[tuple[int, int]] = []

    for member in members:
        owner_id = parse_public_id("owner", member.owner_id)
        snapshot_id = parse_public_id("snap", member.owner_snapshot_id)
        snapshot = session.get(OwnerSnapshot, snapshot_id)
        if snapshot is None or snapshot.owner_id != owner_id:
            raise ApiError(
                422,
                "validation_error",
                "Group member snapshot must belong to the selected owner.",
                [{"field": "members", "reason": "Owner snapshot mismatch."}],
            )
        if snapshot.status != "confirmed":
            raise ApiError(
                422,
                "validation_error",
                "Group members must use confirmed owner snapshots.",
                [{"field": "members", "reason": "Snapshot is not confirmed."}],
            )
        member_owner_ids.add(owner_id)
        validated.append((owner_id, snapshot_id))

    if member_owner_ids != active_owner_ids:
        raise ApiError(
            422,
            "validation_error",
            "Group must include exactly one confirmed snapshot for every active owner.",
            [{"field": "members", "reason": "Active owner set mismatch."}],
        )
    return validated


def create_group(session: Session, payload: SnapshotGroupCreate) -> SnapshotGroup:
    validated_members = validate_members(session, payload.members)
    group = SnapshotGroup(reporting_at=utc_iso_now(), label=payload.label)
    session.add(group)
    session.commit()
    session.refresh(group)

    revision = SnapshotGroupRevision(
        snapshot_group_id=group.id,
        revision_number=1,
        status="draft",
        base_currency=settings.official_base_currency,
    )
    session.add(revision)
    session.commit()
    session.refresh(revision)

    for owner_id, snapshot_id in validated_members:
        session.add(
            SnapshotGroupMember(
                snapshot_group_revision_id=revision.id,
                owner_id=owner_id,
                owner_snapshot_id=snapshot_id,
            )
        )
    group.active_revision_id = revision.id
    group.updated_at = datetime.now(UTC)
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def finalize_group(
    session: Session,
    group_public_id: str,
    fx_request: FxFinalizeRequest,
) -> SnapshotGroup:
    group = _get_group(session, group_public_id)
    revision = active_revision(session, group)
    if revision is None or revision.status != "draft":
        raise ApiError(409, "conflict", "Only draft group revisions can be finalized.")
    members = revision_members(session, revision.id)
    validate_members(
        session,
        [
            type(
                "MemberInput",
                (),
                {
                    "owner_id": f"owner_{member.owner_id}",
                    "owner_snapshot_id": f"snap_{member.owner_snapshot_id}",
                },
            )
            for member in members
        ],
    )

    if fx_request.mode != "manual":
        raise ApiError(422, "validation_error", "Only manual FX is implemented.")
    rate_set = freeze_manual_rate_set(
        session,
        base_currency=revision.base_currency,
        manual_rates=[
            {"currency": rate.currency, "rate_to_base": rate.rate_to_base}
            for rate in fx_request.manual_rates
        ],
        rate_timestamp=utc_iso_now(),
    )
    revision.fx_rate_set_id = rate_set.id
    revision.status = "finalized"
    revision.finalized_at = datetime.now(UTC)
    revision.updated_at = revision.finalized_at
    session.add(revision)
    session.commit()
    session.refresh(group)
    return group


def get_group(session: Session, group_public_id: str) -> SnapshotGroup:
    return _get_group(session, group_public_id)
