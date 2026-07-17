from datetime import UTC, datetime

from sqlmodel import Session, select

from backend.app.api.errors import ApiError
from backend.app.models.tag import Tag
from backend.app.schemas.tag import TagCreate, TagPatch


def normalize_tag_name(name: str) -> str:
    return " ".join(name.lower().split())


def list_tags(session: Session) -> list[Tag]:
    return list(session.exec(select(Tag).order_by(Tag.normalized_name, Tag.id)))


def create_tag(session: Session, payload: TagCreate) -> Tag:
    normalized_name = normalize_tag_name(payload.name)
    existing = session.exec(
        select(Tag).where(Tag.normalized_name == normalized_name)
    ).first()
    if existing is not None:
        raise ApiError(409, "conflict", "Tag already exists.")

    tag = Tag(
        name=payload.name.strip(),
        normalized_name=normalized_name,
        color=payload.color,
        description=payload.description,
    )
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


def get_tag(session: Session, tag_id: int) -> Tag:
    tag = session.get(Tag, tag_id)
    if tag is None:
        raise ApiError(404, "not_found", "Tag was not found.")
    return tag


def patch_tag(session: Session, tag_id: int, payload: TagPatch) -> Tag:
    tag = get_tag(session, tag_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data:
        normalized_name = normalize_tag_name(update_data["name"])
        existing = session.exec(
            select(Tag).where(Tag.normalized_name == normalized_name, Tag.id != tag.id)
        ).first()
        if existing is not None:
            raise ApiError(409, "conflict", "Tag already exists.")
        tag.name = update_data.pop("name").strip()
        tag.normalized_name = normalized_name
    for field, value in update_data.items():
        setattr(tag, field, value)
    tag.updated_at = datetime.now(UTC)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag
