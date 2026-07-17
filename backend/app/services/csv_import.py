from itsdangerous import BadSignature, URLSafeSerializer
from sqlmodel import Session, select

from backend.app.api.errors import ApiError
from backend.app.core.config import settings
from backend.app.domain.csv_import import (
    escape_csv_text,
    parse_template_csv,
    render_template_csv,
)
from backend.app.domain.money import validate_money_string
from backend.app.models.category import SystemCategory
from backend.app.models.owner import Owner
from backend.app.models.snapshot import OwnerSnapshot, SnapshotItem
from backend.app.models.tag import Tag
from backend.app.models.template import (
    BalanceSheetItemTemplate,
    BalanceSheetItemTemplateTag,
)
from backend.app.schemas.ids import public_id

PREVIEW_TOKEN_SALT = "csv-import-preview"


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


def preview_import(
    session: Session,
    *,
    reporting_at: str,
    csv_text: str,
) -> dict:
    try:
        rows = parse_template_csv(csv_text)
    except ApiError as exc:
        return _invalid_preview(reporting_at, exc.details)

    errors: list[dict[str, object]] = []
    valid_rows: list[dict[str, str]] = []
    owner_counts: dict[str, dict[str, object]] = {}
    for row_number, row in enumerate(rows, start=2):
        row_errors = validate_import_row(session, row_number, row)
        if row_errors:
            errors.extend(row_errors)
            continue
        valid_rows.append(row)
        owner_id = row["owner_id"]
        owner_counts.setdefault(
            owner_id,
            {"owner_id": owner_id, "owner_name": row["owner_name"], "item_count": 0},
        )
        owner_counts[owner_id]["item_count"] += 1

    if errors:
        return _invalid_preview(reporting_at, errors)

    token = URLSafeSerializer(settings.session_secret, salt=PREVIEW_TOKEN_SALT).dumps(
        {"reporting_at": reporting_at, "rows": valid_rows}
    )
    return {
        "valid": True,
        "preview_token": token,
        "reporting_at": reporting_at,
        "draft_snapshots": list(owner_counts.values()),
        "errors": [],
    }


def _invalid_preview(reporting_at: str, errors: list[dict]) -> dict:
    return {
        "valid": False,
        "preview_token": None,
        "reporting_at": reporting_at,
        "draft_snapshots": [],
        "errors": errors,
    }


def validate_import_row(
    session: Session,
    row_number: int,
    row: dict[str, str],
) -> list[dict[str, object]]:
    errors: list[dict[str, object]] = []
    template = _get_active_template(session, row.get("template_id", ""))
    if template is None:
        return [
            {
                "row": row_number,
                "field": "template_id",
                "reason": "Unknown or inactive template.",
            }
        ]
    owner = session.get(Owner, template.owner_id)
    category = session.get(SystemCategory, template.system_category_id)
    tags = _template_tags(session, template.id)
    if owner is None or not owner.active:
        errors.append(
            {"row": row_number, "field": "owner_id", "reason": "Inactive owner."}
        )
    if category is None or not category.active:
        errors.append(
            {
                "row": row_number,
                "field": "system_category_id",
                "reason": "Inactive category.",
            }
        )
    if owner is not None and row.get("owner_id") != public_id("owner", owner.id):
        errors.append(_metadata_error(row_number, "owner_id"))
    if owner is not None and row.get("owner_name") != escape_csv_text(owner.name):
        errors.append(_metadata_error(row_number, "owner_name"))
    if row.get("item_type") != template.item_type:
        errors.append(_metadata_error(row_number, "item_type"))
    if category is not None and row.get("system_category_id") != public_id(
        "cat",
        category.id,
    ):
        errors.append(_metadata_error(row_number, "system_category_id"))
    if category is not None and row.get("system_category_code") != category.code:
        errors.append(_metadata_error(row_number, "system_category_code"))
    if category is not None and row.get("system_category_name") != escape_csv_text(
        category.name
    ):
        errors.append(_metadata_error(row_number, "system_category_name"))
    if row.get("account_name") != escape_csv_text(template.account_name):
        errors.append(_metadata_error(row_number, "account_name"))
    if row.get("institution_name") != escape_csv_text(template.institution_name):
        errors.append(_metadata_error(row_number, "institution_name"))
    if row.get("currency") != template.currency:
        errors.append(_metadata_error(row_number, "currency"))

    expected_tag_ids = "|".join(public_id("tag", tag.id) for tag in tags)
    expected_tag_names = escape_csv_text("|".join(tag.name for tag in tags))
    if row.get("tag_ids") != expected_tag_ids:
        errors.append(_metadata_error(row_number, "tag_ids"))
    if row.get("tag_names") != expected_tag_names:
        errors.append(_metadata_error(row_number, "tag_names"))

    try:
        validate_money_string(row.get("amount_original", ""))
    except ApiError:
        errors.append(
            {
                "row": row_number,
                "field": "amount_original",
                "reason": "Amount must be non-negative with up to 8 decimals.",
            }
        )
    return errors


def _metadata_error(row_number: int, field: str) -> dict[str, object]:
    return {
        "row": row_number,
        "field": field,
        "reason": "Exported metadata no longer matches current template data.",
    }


def _get_active_template(
    session: Session,
    template_public_id: str,
) -> BalanceSheetItemTemplate | None:
    if not template_public_id.startswith("tpl_"):
        return None
    raw_id = template_public_id.removeprefix("tpl_")
    if not raw_id.isdigit():
        return None
    template = session.get(BalanceSheetItemTemplate, int(raw_id))
    if template is None or not template.active:
        return None
    return template


def commit_import(session: Session, *, preview_token: str) -> dict:
    try:
        payload = URLSafeSerializer(
            settings.session_secret,
            salt=PREVIEW_TOKEN_SALT,
        ).loads(preview_token)
    except BadSignature as exc:
        raise ApiError(422, "validation_error", "Invalid preview token.") from exc

    reporting_at = payload["reporting_at"]
    rows: list[dict[str, str]] = payload["rows"]
    owner_ids = sorted({row["owner_id"] for row in rows})
    for owner_public_id in owner_ids:
        owner_id = int(owner_public_id.removeprefix("owner_"))
        existing = session.exec(
            select(OwnerSnapshot).where(
                OwnerSnapshot.owner_id == owner_id,
                OwnerSnapshot.reporting_at == reporting_at,
                OwnerSnapshot.status == "draft",
            )
        ).first()
        if existing is not None:
            raise ApiError(
                409,
                "conflict",
                "Draft snapshot already exists for owner and reporting_at.",
            )

    try:
        created: list[dict[str, object]] = []
        for owner_public_id in owner_ids:
            owner_id = int(owner_public_id.removeprefix("owner_"))
            owner_rows = [row for row in rows if row["owner_id"] == owner_public_id]
            snapshot = OwnerSnapshot(
                owner_id=owner_id,
                reporting_at=reporting_at,
                status="draft",
                source="csv_import",
            )
            session.add(snapshot)
            session.flush()
            for row in owner_rows:
                template = _get_active_template(session, row["template_id"])
                if template is None:
                    raise ApiError(409, "conflict", "Template changed after preview.")
                category = session.get(SystemCategory, template.system_category_id)
                if category is None:
                    raise ApiError(409, "conflict", "Category changed after preview.")
                session.add(
                    SnapshotItem(
                        owner_snapshot_id=snapshot.id,
                        template_id=template.id,
                        item_type=template.item_type,
                        system_category_id=category.id,
                        system_category_code_snapshot=category.code,
                        system_category_name_snapshot=category.name,
                        account_name_snapshot=template.account_name,
                        institution_name_snapshot=template.institution_name,
                        currency=template.currency,
                        amount_original=validate_money_string(row["amount_original"]),
                        note=(row["note"].strip() or None),
                        display_order=template.display_order,
                    )
                )
            created.append(
                {
                    "owner_id": owner_public_id,
                    "snapshot_id": public_id("snap", snapshot.id),
                    "item_count": len(owner_rows),
                }
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"draft_snapshots": created}
