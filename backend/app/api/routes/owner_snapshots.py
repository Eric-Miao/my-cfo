from http import HTTPStatus

from fastapi import APIRouter

from backend.app.api.deps import SessionDep
from backend.app.schemas.snapshot import (
    OwnerSnapshotCreate,
    OwnerSnapshotRead,
    SnapshotItemPatch,
)
from backend.app.services import snapshots

router = APIRouter(prefix="/owner-snapshots", tags=["owner-snapshots"])


def _read_snapshot(session: SessionDep, snapshot) -> OwnerSnapshotRead:
    return OwnerSnapshotRead.from_model(
        snapshot,
        snapshots.snapshot_items(session, snapshot.id),
    )


@router.post("", status_code=HTTPStatus.CREATED)
def create_owner_snapshot(
    payload: OwnerSnapshotCreate,
    session: SessionDep,
) -> OwnerSnapshotRead:
    return _read_snapshot(session, snapshots.create_owner_snapshot(session, payload))


@router.patch("/{snapshot_id}/items/{item_id}")
def update_snapshot_item(
    snapshot_id: str,
    item_id: str,
    payload: SnapshotItemPatch,
    session: SessionDep,
) -> OwnerSnapshotRead:
    return _read_snapshot(
        session,
        snapshots.update_snapshot_item(session, snapshot_id, item_id, payload),
    )


@router.post("/{snapshot_id}/confirm")
def confirm_owner_snapshot(snapshot_id: str, session: SessionDep) -> OwnerSnapshotRead:
    return _read_snapshot(session, snapshots.confirm_snapshot(session, snapshot_id))


@router.post("/{snapshot_id}/cancel")
def cancel_owner_snapshot(snapshot_id: str, session: SessionDep) -> OwnerSnapshotRead:
    return _read_snapshot(session, snapshots.cancel_snapshot(session, snapshot_id))
