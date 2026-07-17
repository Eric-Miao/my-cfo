from http import HTTPStatus

from fastapi import APIRouter

from backend.app.api.deps import SessionDep
from backend.app.schemas.ids import parse_public_id
from backend.app.schemas.tag import TagCreate, TagPatch, TagRead
from backend.app.services import tags

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("")
def list_tags(session: SessionDep) -> dict[str, object]:
    return {
        "items": [
            TagRead.from_model(tag).model_dump(mode="json")
            for tag in tags.list_tags(session)
        ],
        "page": {"limit": 50, "next_cursor": None},
    }


@router.post("", status_code=HTTPStatus.CREATED)
def create_tag(
    payload: TagCreate,
    session: SessionDep,
) -> TagRead:
    return TagRead.from_model(tags.create_tag(session, payload))


@router.patch("/{tag_id}")
def patch_tag(
    tag_id: str,
    payload: TagPatch,
    session: SessionDep,
) -> TagRead:
    return TagRead.from_model(
        tags.patch_tag(session, parse_public_id("tag", tag_id), payload)
    )
