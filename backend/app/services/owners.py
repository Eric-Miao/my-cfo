from datetime import UTC, datetime

from sqlmodel import Session, select

from backend.app.api.errors import ApiError
from backend.app.models.owner import Owner
from backend.app.schemas.owner import OwnerCreate, OwnerPatch


def list_owners(session: Session) -> list[Owner]:
    return list(session.exec(select(Owner).order_by(Owner.display_order, Owner.id)))


def create_owner(session: Session, payload: OwnerCreate) -> Owner:
    owner = Owner(name=payload.name, display_order=payload.display_order)
    session.add(owner)
    session.commit()
    session.refresh(owner)
    return owner


def get_owner(session: Session, owner_id: int) -> Owner:
    owner = session.get(Owner, owner_id)
    if owner is None:
        raise ApiError(404, "not_found", "Owner was not found.")
    return owner


def patch_owner(session: Session, owner_id: int, payload: OwnerPatch) -> Owner:
    owner = get_owner(session, owner_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(owner, field, value)
    owner.updated_at = datetime.now(UTC)
    session.add(owner)
    session.commit()
    session.refresh(owner)
    return owner


def set_owner_active(session: Session, owner_id: int, active: bool) -> Owner:
    owner = get_owner(session, owner_id)
    owner.active = active
    owner.updated_at = datetime.now(UTC)
    session.add(owner)
    session.commit()
    session.refresh(owner)
    return owner
