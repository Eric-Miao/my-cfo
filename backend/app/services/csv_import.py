from sqlmodel import Session, select

from backend.app.domain.csv_import import escape_csv_text, render_template_csv
from backend.app.models.category import SystemCategory
from backend.app.models.owner import Owner
from backend.app.models.tag import Tag
from backend.app.models.template import (
    BalanceSheetItemTemplate,
    BalanceSheetItemTemplateTag,
)
from backend.app.schemas.ids import public_id


def export_template_csv(session: Session) -> str:
    rows: list[dict[str, str]] = []
    templates = session.exec(
        select(BalanceSheetItemTemplate)
        .where(BalanceSheetItemTemplate.active.is_(True))
        .order_by(
            BalanceSheetItemTemplate.owner_id,
            BalanceSheetItemTemplate.display_order,
            BalanceSheetItemTemplate.id,
        )
    ).all()
    for template in templates:
        owner = session.get(Owner, template.owner_id)
        category = session.get(SystemCategory, template.system_category_id)
        if owner is None or category is None or not owner.active or not category.active:
            continue
        tags = _template_tags(session, template.id)
        rows.append(
            {
                "template_id": public_id("tpl", template.id),
                "owner_id": public_id("owner", owner.id),
                "owner_name": escape_csv_text(owner.name),
                "item_type": template.item_type,
                "system_category_id": public_id("cat", category.id),
                "system_category_code": category.code,
                "system_category_name": escape_csv_text(category.name),
                "account_name": escape_csv_text(template.account_name),
                "institution_name": escape_csv_text(template.institution_name),
                "currency": template.currency,
                "tag_ids": "|".join(public_id("tag", tag.id) for tag in tags),
                "tag_names": escape_csv_text("|".join(tag.name for tag in tags)),
                "amount_original": "",
                "note": "",
            }
        )
    return render_template_csv(rows)


def _template_tags(session: Session, template_id: int | None) -> list[Tag]:
    links = session.exec(
        select(BalanceSheetItemTemplateTag).where(
            BalanceSheetItemTemplateTag.template_id == template_id
        )
    ).all()
    if not links:
        return []
    tag_ids = [link.tag_id for link in links]
    return list(
        session.exec(select(Tag).where(Tag.id.in_(tag_ids)).order_by(Tag.normalized_name))
    )
