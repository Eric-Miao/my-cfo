from http import HTTPStatus

from fastapi import APIRouter

from backend.app.api.deps import SessionDep
from backend.app.schemas.ids import parse_public_id
from backend.app.schemas.owner import OwnerCreate, OwnerPatch, OwnerRead
from backend.app.services import owners

router = APIRouter(prefix="/owners", tags=["owners"])


@router.get("")
def list_owners(session: SessionDep) -> dict[str, object]:
    return {
        "items": [
            OwnerRead.from_model(owner).model_dump(mode="json")
            for owner in owners.list_owners(session)
        ],
        "page": {"limit": 50, "next_cursor": None},
    }


@router.post("", status_code=HTTPStatus.CREATED)
def create_owner(
    payload: OwnerCreate,
    session: SessionDep,
) -> OwnerRead:
    return OwnerRead.from_model(owners.create_owner(session, payload))


@router.patch("/{owner_id}")
def patch_owner(
    owner_id: str,
    payload: OwnerPatch,
    session: SessionDep,
) -> OwnerRead:
    return OwnerRead.from_model(
        owners.patch_owner(session, parse_public_id("owner", owner_id), payload)
    )


@router.post("/{owner_id}/deactivate")
def deactivate_owner(
    owner_id: str,
    session: SessionDep,
) -> OwnerRead:
    return OwnerRead.from_model(
        owners.set_owner_active(session, parse_public_id("owner", owner_id), False)
    )


@router.post("/{owner_id}/recover")
def recover_owner(
    owner_id: str,
    session: SessionDep,
) -> OwnerRead:
    return OwnerRead.from_model(
        owners.set_owner_active(session, parse_public_id("owner", owner_id), True)
    )
