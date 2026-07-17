from datetime import UTC, datetime

from sqlmodel import Session, select

from backend.app.api.errors import ApiError
from backend.app.models.category import SystemCategory
from backend.app.schemas.category import SystemCategoryCreate, SystemCategoryPatch


def list_categories(session: Session) -> list[SystemCategory]:
    return list(
        session.exec(
            select(SystemCategory).order_by(
                SystemCategory.display_order,
                SystemCategory.id,
            )
        )
    )


def create_category(
    session: Session,
    payload: SystemCategoryCreate,
) -> SystemCategory:
    category = SystemCategory(
        item_type=payload.item_type,
        code=payload.code,
        name=payload.name,
        calculation_role=payload.calculation_role,
        display_order=payload.display_order,
    )
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def get_category(session: Session, category_id: int) -> SystemCategory:
    category = session.get(SystemCategory, category_id)
    if category is None:
        raise ApiError(404, "not_found", "System category was not found.")
    return category


def patch_category(
    session: Session,
    category_id: int,
    payload: SystemCategoryPatch,
) -> SystemCategory:
    category = get_category(session, category_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    category.updated_at = datetime.now(UTC)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category
