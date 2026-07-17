from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.app.models.owner import Owner
from backend.app.schemas.ids import public_id


class OwnerCreate(BaseModel):
    name: str
    display_order: int = 0


class OwnerPatch(BaseModel):
    name: str | None = None
    display_order: int | None = None


class OwnerRead(BaseModel):
    id: str
    name: str
    display_order: int
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, owner: Owner) -> "OwnerRead":
        return cls(
            id=public_id("owner", owner.id),
            name=owner.name,
            display_order=owner.display_order,
            active=owner.active,
            created_at=owner.created_at,
            updated_at=owner.updated_at,
        )
