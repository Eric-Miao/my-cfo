from http import HTTPStatus

from fastapi import APIRouter

from backend.app.api.deps import SessionDep
from backend.app.models.snapshot import OwnerSnapshot
from backend.app.schemas.group import (
    SnapshotGroupCreate,
    SnapshotGroupFinalizeRequest,
    SnapshotGroupMemberRead,
    SnapshotGroupRead,
    SnapshotGroupReopenRequest,
    SnapshotGroupRevisionRead,
)
from backend.app.services import groups

router = APIRouter(prefix="/snapshot-groups", tags=["snapshot-groups"])


def _read_group(session: SessionDep, group) -> SnapshotGroupRead:
    def read_revision(revision):
        if revision is None:
            return None
        member_reads = []
        for member in groups.revision_members(session, revision.id):
            snapshot = session.get(OwnerSnapshot, member.owner_snapshot_id)
            if snapshot is None:
                continue
            member_reads.append(SnapshotGroupMemberRead.from_model(member, snapshot))
        return SnapshotGroupRevisionRead.from_model(revision, member_reads)

    return SnapshotGroupRead.from_model(
        group,
        read_revision(groups.active_revision(session, group)),
        read_revision(groups.draft_revision(session, group)),
    )


@router.post("", status_code=HTTPStatus.CREATED)
def create_snapshot_group(
    payload: SnapshotGroupCreate,
    session: SessionDep,
) -> SnapshotGroupRead:
    return _read_group(session, groups.create_group(session, payload))


@router.get("/{group_id}")
def get_snapshot_group(group_id: str, session: SessionDep) -> SnapshotGroupRead:
    return _read_group(session, groups.get_group(session, group_id))


@router.post("/{group_id}/finalize")
def finalize_snapshot_group(
    group_id: str,
    payload: SnapshotGroupFinalizeRequest,
    session: SessionDep,
) -> SnapshotGroupRead:
    return _read_group(
        session,
        groups.finalize_group(session, group_id, payload.fx_rates),
    )


@router.post("/{group_id}/reopen")
def reopen_snapshot_group(
    group_id: str,
    payload: SnapshotGroupReopenRequest,
    session: SessionDep,
) -> SnapshotGroupRead:
    return _read_group(session, groups.reopen_group(session, group_id, payload.note))


@router.post("/{group_id}/cancel-draft")
def cancel_snapshot_group_draft(
    group_id: str,
    session: SessionDep,
) -> SnapshotGroupRead:
    return _read_group(session, groups.cancel_draft(session, group_id))
