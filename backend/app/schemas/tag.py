from pydantic import BaseModel, ConfigDict

from backend.app.models.tag import Tag
from backend.app.schemas.ids import public_id


class TagCreate(BaseModel):
    name: str
    color: str | None = None
    description: str | None = None


class TagPatch(BaseModel):
    name: str | None = None
    color: str | None = None
    description: str | None = None
    active: bool | None = None


class TagRead(BaseModel):
    id: str
    name: str
    normalized_name: str
    color: str | None
    description: str | None
    active: bool

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, tag: Tag) -> "TagRead":
        return cls(
            id=public_id("tag", tag.id),
            name=tag.name,
            normalized_name=tag.normalized_name,
            color=tag.color,
            description=tag.description,
            active=tag.active,
        )
