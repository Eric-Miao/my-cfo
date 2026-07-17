from pydantic import BaseModel, ConfigDict

from backend.app.models.template import BalanceSheetItemTemplate
from backend.app.schemas.ids import public_id


class TemplateTagRead(BaseModel):
    id: str
    name: str


class TemplateCreate(BaseModel):
    owner_id: str
    item_type: str
    system_category_id: str
    account_name: str
    institution_name: str | None = None
    currency: str
    display_order: int = 0
    note: str | None = None
    tag_ids: list[str] = []


class TemplatePatch(BaseModel):
    account_name: str | None = None
    institution_name: str | None = None
    currency: str | None = None
    display_order: int | None = None
    note: str | None = None
    active: bool | None = None
    tag_ids: list[str] | None = None


class TemplateRead(BaseModel):
    id: str
    owner_id: str
    item_type: str
    system_category_id: str
    account_name: str
    institution_name: str | None
    currency: str
    display_order: int
    active: bool
    note: str | None
    tags: list[TemplateTagRead]

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(
        cls,
        template: BalanceSheetItemTemplate,
        tags: list[TemplateTagRead],
    ) -> "TemplateRead":
        return cls(
            id=public_id("tpl", template.id),
            owner_id=public_id("owner", template.owner_id),
            item_type=template.item_type,
            system_category_id=public_id("cat", template.system_category_id),
            account_name=template.account_name,
            institution_name=template.institution_name,
            currency=template.currency,
            display_order=template.display_order,
            active=template.active,
            note=template.note,
            tags=tags,
        )
