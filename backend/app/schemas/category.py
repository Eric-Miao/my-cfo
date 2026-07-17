from pydantic import BaseModel, ConfigDict

from backend.app.models.category import SystemCategory
from backend.app.schemas.ids import public_id


class SystemCategoryCreate(BaseModel):
    item_type: str
    code: str
    name: str
    calculation_role: str
    display_order: int = 0


class SystemCategoryPatch(BaseModel):
    name: str | None = None
    calculation_role: str | None = None
    display_order: int | None = None
    active: bool | None = None


class SystemCategoryRead(BaseModel):
    id: str
    item_type: str
    code: str
    name: str
    calculation_role: str
    display_order: int
    active: bool

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, category: SystemCategory) -> "SystemCategoryRead":
        return cls(
            id=public_id("cat", category.id),
            item_type=category.item_type,
            code=category.code,
            name=category.name,
            calculation_role=category.calculation_role,
            display_order=category.display_order,
            active=category.active,
        )
