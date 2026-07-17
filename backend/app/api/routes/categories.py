from http import HTTPStatus

from fastapi import APIRouter

from backend.app.api.deps import SessionDep
from backend.app.schemas.category import (
    SystemCategoryCreate,
    SystemCategoryPatch,
    SystemCategoryRead,
)
from backend.app.schemas.ids import parse_public_id
from backend.app.services import categories

router = APIRouter(prefix="/system-categories", tags=["system-categories"])


@router.get("")
def list_system_categories(
    session: SessionDep,
) -> dict[str, object]:
    return {
        "items": [
            SystemCategoryRead.from_model(category).model_dump(mode="json")
            for category in categories.list_categories(session)
        ],
        "page": {"limit": 50, "next_cursor": None},
    }


@router.post("", status_code=HTTPStatus.CREATED)
def create_system_category(
    payload: SystemCategoryCreate,
    session: SessionDep,
) -> SystemCategoryRead:
    return SystemCategoryRead.from_model(categories.create_category(session, payload))


@router.patch("/{category_id}")
def patch_system_category(
    category_id: str,
    payload: SystemCategoryPatch,
    session: SessionDep,
) -> SystemCategoryRead:
    return SystemCategoryRead.from_model(
        categories.patch_category(session, parse_public_id("cat", category_id), payload)
    )
