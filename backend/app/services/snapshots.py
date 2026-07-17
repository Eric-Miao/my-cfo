from datetime import UTC, datetime

from sqlmodel import Session, select

from backend.app.api.errors import ApiError
from backend.app.domain.money import validate_money_string
from backend.app.models.category import SystemCategory
from backend.app.models.owner import Owner
from backend.app.models.snapshot import OwnerSnapshot, SnapshotItem
from backend.app.models.template import BalanceSheetItemTemplate
from backend.app.schemas.ids import parse_public_id
from backend.app.schemas.snapshot import (
    OwnerSnapshotCreate,
    OwnerSnapshotReplacementCreate,
    SnapshotItemPatch,
)


def _get_owner(session: Session, owner_public_id: str) -> Owner:
    owner = session.get(Owner, parse_public_id("owner", owner_public_id))
    if owner is None:
        raise ApiError(404, "not_found", "Owner was not found.")
    return owner


def get_snapshot(session: Session, snapshot_public_id: str) -> OwnerSnapshot:
    snapshot = session.get(OwnerSnapshot, parse_public_id("snap", snapshot_public_id))
    if snapshot is None:
        raise ApiError(404, "not_found", "Snapshot was not found.")
    return snapshot


def _get_item(session: Session, item_public_id: str) -> SnapshotItem:
    item = session.get(SnapshotItem, parse_public_id("item", item_public_id))
    if item is None:
        raise ApiError(404, "not_found", "Snapshot item was not found.")
    return item


def snapshot_items(session: Session, snapshot_id: int | None) -> list[SnapshotItem]:
    return list(
        session.exec(
            select(SnapshotItem)
            .where(SnapshotItem.owner_snapshot_id == snapshot_id)
            .order_by(SnapshotItem.display_order, SnapshotItem.id)
        )
    )


def create_owner_snapshot(
    session: Session,
    payload: OwnerSnapshotCreate,
) -> OwnerSnapshot:
    owner = _get_owner(session, payload.owner_id)
    templates = session.exec(
        select(BalanceSheetItemTemplate)
        .where(
            BalanceSheetItemTemplate.owner_id == owner.id,
            BalanceSheetItemTemplate.active.is_(True),
        )
        .order_by(BalanceSheetItemTemplate.display_order, BalanceSheetItemTemplate.id)
    ).all()

    snapshot = OwnerSnapshot(
        owner_id=owner.id,
        reporting_at=payload.reporting_at,
        status="draft",
        source="manual",
        label=payload.label,
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    for template in templates:
        category = session.get(SystemCategory, template.system_category_id)
        if category is None:
            raise ApiError(409, "conflict", "Template category no longer exists.")
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
                amount_original=None,
                display_order=template.display_order,
            )
        )
    session.commit()
    session.refresh(snapshot)
    return snapshot


def update_snapshot_item(
    session: Session,
    snapshot_public_id: str,
    item_public_id: str,
    payload: SnapshotItemPatch,
) -> OwnerSnapshot:
    snapshot = get_snapshot(session, snapshot_public_id)
    if snapshot.status != "draft":
        raise ApiError(409, "conflict", "Only draft snapshots can be edited.")

    item = _get_item(session, item_public_id)
    if item.owner_snapshot_id != snapshot.id:
        raise ApiError(404, "not_found", "Snapshot item was not found.")

    if payload.amount_original is not None:
        item.amount_original = validate_money_string(payload.amount_original)
    if payload.note is not None:
        item.note = payload.note
    item.updated_at = datetime.now(UTC)
    session.add(item)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def confirm_snapshot(session: Session, snapshot_public_id: str) -> OwnerSnapshot:
    snapshot = get_snapshot(session, snapshot_public_id)
    if snapshot.status != "draft":
        raise ApiError(409, "conflict", "Only draft snapshots can be confirmed.")
    items = snapshot_items(session, snapshot.id)
    if any(item.amount_original is None for item in items):
        raise ApiError(
            422,
            "validation_error",
            "All snapshot items must have an amount before confirmation.",
            [{"field": "items", "reason": "Incomplete item amounts."}],
        )
    snapshot.status = "confirmed"
    snapshot.confirmed_at = datetime.now(UTC)
    snapshot.updated_at = datetime.now(UTC)
    session.add(snapshot)
    if snapshot.replaces_snapshot_id is not None:
        original = session.get(OwnerSnapshot, snapshot.replaces_snapshot_id)
        if original is not None:
            original.status = "superseded"
            original.superseded_by_snapshot_id = snapshot.id
            original.superseded_at = snapshot.confirmed_at
            original.updated_at = snapshot.updated_at
            session.add(original)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def cancel_snapshot(session: Session, snapshot_public_id: str) -> OwnerSnapshot:
    snapshot = get_snapshot(session, snapshot_public_id)
    if snapshot.status != "draft":
        raise ApiError(409, "conflict", "Only draft snapshots can be cancelled.")
    snapshot.status = "cancelled"
    snapshot.updated_at = datetime.now(UTC)
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def create_replacement_snapshot(
    session: Session,
    snapshot_public_id: str,
    payload: OwnerSnapshotReplacementCreate,
) -> OwnerSnapshot:
    original = get_snapshot(session, snapshot_public_id)
    if original.status != "confirmed":
        raise ApiError(409, "conflict", "Only confirmed snapshots can be replaced.")

    replacement = OwnerSnapshot(
        owner_id=original.owner_id,
        reporting_at=original.reporting_at,
        status="draft",
        source="manual",
        label=original.label,
        replaces_snapshot_id=original.id,
        revision_note=payload.revision_note,
    )
    session.add(replacement)
    session.commit()
    session.refresh(replacement)

    for item in snapshot_items(session, original.id):
        session.add(
            SnapshotItem(
                owner_snapshot_id=replacement.id,
                template_id=item.template_id,
                item_type=item.item_type,
                system_category_id=item.system_category_id,
                system_category_code_snapshot=item.system_category_code_snapshot,
                system_category_name_snapshot=item.system_category_name_snapshot,
                account_name_snapshot=item.account_name_snapshot,
                institution_name_snapshot=item.institution_name_snapshot,
                currency=item.currency,
                amount_original=item.amount_original,
                note=item.note,
                display_order=item.display_order,
            )
        )
    session.commit()
    session.refresh(replacement)
    return replacement
