from datetime import UTC, datetime

from sqlmodel import Session, select

from backend.app.api.errors import ApiError
from backend.app.models.category import SystemCategory
from backend.app.models.owner import Owner
from backend.app.models.tag import Tag
from backend.app.models.template import (
    BalanceSheetItemTemplate,
    BalanceSheetItemTemplateTag,
)
from backend.app.schemas.ids import parse_public_id, public_id
from backend.app.schemas.template import TemplateCreate, TemplatePatch, TemplateTagRead


def _get_owner(session: Session, owner_public_id: str) -> Owner:
    owner = session.get(Owner, parse_public_id("owner", owner_public_id))
    if owner is None:
        raise ApiError(404, "not_found", "Owner was not found.")
    return owner


def _get_category(session: Session, category_public_id: str) -> SystemCategory:
    category = session.get(SystemCategory, parse_public_id("cat", category_public_id))
    if category is None:
        raise ApiError(404, "not_found", "System category was not found.")
    return category


def _get_tags(session: Session, tag_public_ids: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    for tag_public_id in tag_public_ids:
        tag = session.get(Tag, parse_public_id("tag", tag_public_id))
        if tag is None:
            raise ApiError(404, "not_found", "Tag was not found.")
        tags.append(tag)
    return tags


def _template_tags(
    session: Session,
    template: BalanceSheetItemTemplate,
) -> list[TemplateTagRead]:
    links = session.exec(
        select(BalanceSheetItemTemplateTag).where(
            BalanceSheetItemTemplateTag.template_id == template.id
        )
    ).all()
    if not links:
        return []
    tag_ids = [link.tag_id for link in links]
    tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()
    sorted_tags = sorted(tags, key=lambda tag: tag.normalized_name)
    return [
        TemplateTagRead(id=public_id("tag", tag.id), name=tag.name)
        for tag in sorted_tags
    ]


def serialize_template(
    session: Session,
    template: BalanceSheetItemTemplate,
) -> tuple[BalanceSheetItemTemplate, list[TemplateTagRead]]:
    return template, _template_tags(session, template)


def list_templates(session: Session) -> list[BalanceSheetItemTemplate]:
    return list(
        session.exec(
            select(BalanceSheetItemTemplate).order_by(
                BalanceSheetItemTemplate.display_order,
                BalanceSheetItemTemplate.id,
            )
        )
    )


def create_template(
    session: Session,
    payload: TemplateCreate,
) -> BalanceSheetItemTemplate:
    owner = _get_owner(session, payload.owner_id)
    category = _get_category(session, payload.system_category_id)
    tags = _get_tags(session, payload.tag_ids)
    if category.item_type != payload.item_type:
        raise ApiError(
            422,
            "validation_error",
            "Template item_type must match the system category item_type.",
            [{"field": "system_category_id", "reason": "Item type mismatch."}],
        )

    template = BalanceSheetItemTemplate(
        owner_id=owner.id,
        item_type=payload.item_type,
        system_category_id=category.id,
        account_name=payload.account_name,
        institution_name=payload.institution_name,
        currency=payload.currency.upper(),
        display_order=payload.display_order,
        note=payload.note,
    )
    session.add(template)
    session.commit()
    session.refresh(template)

    for tag in tags:
        session.add(BalanceSheetItemTemplateTag(template_id=template.id, tag_id=tag.id))
    session.commit()
    session.refresh(template)
    return template


def get_template(session: Session, template_id: int) -> BalanceSheetItemTemplate:
    template = session.get(BalanceSheetItemTemplate, template_id)
    if template is None:
        raise ApiError(404, "not_found", "Template was not found.")
    return template


def patch_template(
    session: Session,
    template_id: int,
    payload: TemplatePatch,
) -> BalanceSheetItemTemplate:
    template = get_template(session, template_id)
    update_data = payload.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)
    for field, value in update_data.items():
        if field == "currency" and value is not None:
            value = value.upper()
        setattr(template, field, value)
    template.updated_at = datetime.now(UTC)
    session.add(template)

    if tag_ids is not None:
        existing_links = session.exec(
            select(BalanceSheetItemTemplateTag).where(
                BalanceSheetItemTemplateTag.template_id == template.id
            )
        ).all()
        for link in existing_links:
            session.delete(link)
        for tag in _get_tags(session, tag_ids):
            session.add(
                BalanceSheetItemTemplateTag(template_id=template.id, tag_id=tag.id)
            )

    session.commit()
    session.refresh(template)
    return template


def set_template_active(
    session: Session,
    template_id: int,
    active: bool,
) -> BalanceSheetItemTemplate:
    template = get_template(session, template_id)
    template.active = active
    template.updated_at = datetime.now(UTC)
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def institution_suggestions(session: Session, query: str) -> list[str]:
    normalized_query = query.strip().lower()
    statement = select(BalanceSheetItemTemplate).where(
        BalanceSheetItemTemplate.institution_name.is_not(None)
    )
    names = {
        template.institution_name.strip()
        for template in session.exec(statement)
        if template.institution_name
        and normalized_query in template.institution_name.lower()
    }
    return sorted(names)
