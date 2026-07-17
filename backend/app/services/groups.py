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
from backend.app.services.fx import (
    freeze_api_rate_set,
    freeze_manual_rate_set,
    get_fx_provider,
)


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


def draft_revision(
    session: Session,
    group: SnapshotGroup,
) -> SnapshotGroupRevision | None:
    return session.exec(
        select(SnapshotGroupRevision)
        .where(
            SnapshotGroupRevision.snapshot_group_id == group.id,
            SnapshotGroupRevision.status == "draft",
        )
        .order_by(SnapshotGroupRevision.revision_number.desc())
    ).first()


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


def validate_member_ids(
    session: Session,
    member_ids: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    active_owner_ids = {
        owner.id for owner in session.exec(select(Owner).where(Owner.active.is_(True)))
    }
    member_owner_ids: set[int] = set()
    for owner_id, snapshot_id in member_ids:
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

    if member_owner_ids != active_owner_ids:
        raise ApiError(
            422,
            "validation_error",
            "Group must include exactly one confirmed snapshot for every active owner.",
            [{"field": "members", "reason": "Active owner set mismatch."}],
        )
    return member_ids


def validate_members(
    session: Session,
    members: list,
) -> list[tuple[int, int]]:
    return validate_member_ids(
        session,
        [
            (
                parse_public_id("owner", member.owner_id),
                parse_public_id("snap", member.owner_snapshot_id),
            )
            for member in members
        ],
    )


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
    revision = draft_revision(session, group) or active_revision(session, group)
    if revision is None or revision.status != "draft":
        raise ApiError(409, "conflict", "Only draft group revisions can be finalized.")
    members = revision_members(session, revision.id)
    validate_member_ids(
        session,
        [
            (member.owner_id, member.owner_snapshot_id)
            for member in members
        ],
    )

    if fx_request.mode == "manual":
        rate_set = freeze_manual_rate_set(
            session,
            base_currency=revision.base_currency,
            manual_rates=[
                {"currency": rate.currency, "rate_to_base": rate.rate_to_base}
                for rate in fx_request.manual_rates
            ],
            rate_timestamp=utc_iso_now(),
        )
    elif fx_request.mode == "api":
        currencies = required_currencies_for_revision(session, revision.id)
        rate_set = freeze_api_rate_set(
            session,
            provider=get_fx_provider(),
            base_currency=revision.base_currency,
            currencies=currencies,
        )
    else:
        raise ApiError(422, "validation_error", "Unsupported FX mode.")
    previous_active = active_revision(session, group)
    if previous_active and previous_active.id != revision.id:
        previous_active.status = "superseded"
        previous_active.superseded_at = datetime.now(UTC)
        session.add(previous_active)
    revision.fx_rate_set_id = rate_set.id
    revision.status = "finalized"
    revision.finalized_at = datetime.now(UTC)
    revision.updated_at = revision.finalized_at
    group.active_revision_id = revision.id
    group.updated_at = revision.updated_at
    session.add(group)
    session.add(revision)
    session.commit()
    session.refresh(group)
    return group


def get_group(session: Session, group_public_id: str) -> SnapshotGroup:
    return _get_group(session, group_public_id)


def required_currencies_for_revision(
    session: Session,
    revision_id: int | None,
) -> list[str]:
    currencies = set()
    for member in revision_members(session, revision_id):
        snapshot = session.get(OwnerSnapshot, member.owner_snapshot_id)
        if snapshot is None:
            continue
        from backend.app.services.snapshots import snapshot_items

        for item in snapshot_items(session, snapshot.id):
            if item.currency != settings.official_base_currency:
                currencies.add(item.currency)
    return sorted(currencies)


def reopen_group(
    session: Session,
    group_public_id: str,
    note: str | None,
) -> SnapshotGroup:
    group = _get_group(session, group_public_id)
    finalized = active_revision(session, group)
    if finalized is None or finalized.status != "finalized":
        raise ApiError(409, "conflict", "Only finalized groups can be reopened.")
    if draft_revision(session, group) is not None:
        raise ApiError(409, "conflict", "Group already has a draft revision.")

    next_revision_number = (
        session.exec(
            select(SnapshotGroupRevision.revision_number)
            .where(SnapshotGroupRevision.snapshot_group_id == group.id)
            .order_by(SnapshotGroupRevision.revision_number.desc())
        ).first()
        or 0
    ) + 1
    draft = SnapshotGroupRevision(
        snapshot_group_id=group.id,
        revision_number=next_revision_number,
        status="draft",
        base_currency=finalized.base_currency,
        note=note,
    )
    session.add(draft)
    session.commit()
    session.refresh(draft)

    for member in revision_members(session, finalized.id):
        session.add(
            SnapshotGroupMember(
                snapshot_group_revision_id=draft.id,
                owner_id=member.owner_id,
                owner_snapshot_id=member.owner_snapshot_id,
            )
        )
    session.commit()
    session.refresh(group)
    return group


def cancel_draft(session: Session, group_public_id: str) -> SnapshotGroup:
    group = _get_group(session, group_public_id)
    draft = draft_revision(session, group)
    if draft is None:
        raise ApiError(409, "conflict", "Group has no draft revision.")
    draft.status = "cancelled"
    draft.updated_at = datetime.now(UTC)
    session.add(draft)
    session.commit()
    session.refresh(group)
    return group
