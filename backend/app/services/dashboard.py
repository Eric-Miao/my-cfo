from decimal import Decimal

from sqlmodel import Session, select

from backend.app.core.config import settings
from backend.app.domain.dashboard import format_money
from backend.app.models.category import SystemCategory
from backend.app.models.fx import FxRate
from backend.app.models.group import (
    SnapshotGroup,
    SnapshotGroupMember,
    SnapshotGroupRevision,
)
from backend.app.models.owner import Owner
from backend.app.services.snapshots import snapshot_items


def household_overview(session: Session, display_currency: str | None = None) -> dict:
    current = _latest_finalized_context(session)
    selected_display_currency = display_currency or settings.official_base_currency
    if current is None:
        return {
            "official_base_currency": settings.official_base_currency,
            "display_currency": selected_display_currency,
            "display_values_are_estimates": (
                selected_display_currency != settings.official_base_currency
            ),
            "current": None,
        }

    group, revision = current
    totals = _revision_totals(session, revision)
    return {
        "official_base_currency": revision.base_currency,
        "display_currency": selected_display_currency,
        "display_values_are_estimates": (
            selected_display_currency != revision.base_currency
        ),
        "current": {
            "group_id": f"group_{group.id}",
            "revision_id": f"rev_{revision.id}",
            "reporting_at": group.reporting_at,
            "net_worth_official": format_money(totals["net_worth"]),
            "total_assets_official": format_money(totals["assets"]),
            "total_liabilities_official": format_money(totals["liabilities"]),
            "net_worth_display": format_money(totals["net_worth"]),
        },
    }


def latest_group_detail(session: Session) -> dict:
    current = _latest_finalized_context(session)
    if current is None:
        return {"group_id": None, "revision_id": None, "members": []}
    group, revision = current
    return {
        "group_id": f"group_{group.id}",
        "revision_id": f"rev_{revision.id}",
        "members": _member_details(session, revision),
    }


def net_worth_trend(session: Session) -> dict:
    return {
        "items": [
            {
                "group_id": f"group_{group.id}",
                "revision_id": f"rev_{revision.id}",
                "reporting_at": group.reporting_at,
                "net_worth_official": format_money(
                    _revision_totals(session, revision)["net_worth"]
                ),
            }
            for group, revision in _finalized_contexts(session)
        ]
    }


def assets_liabilities_trend(session: Session) -> dict:
    items = []
    for group, revision in _finalized_contexts(session):
        totals = _revision_totals(session, revision)
        items.append(
            {
                "group_id": f"group_{group.id}",
                "revision_id": f"rev_{revision.id}",
                "reporting_at": group.reporting_at,
                "assets_official": format_money(totals["assets"]),
                "liabilities_official": format_money(totals["liabilities"]),
            }
        )
    return {"items": items}


def owner_net_worth_trend(session: Session) -> dict:
    items = []
    for group, revision in _finalized_contexts(session):
        for member in _member_details(session, revision):
            items.append(
                {
                    "group_id": f"group_{group.id}",
                    "revision_id": f"rev_{revision.id}",
                    "reporting_at": group.reporting_at,
                    **member,
                }
            )
    return {"items": items}


def composition(session: Session) -> dict:
    current = _latest_finalized_context(session)
    if current is None:
        return {
            "system_categories": [],
            "currency_exposure": [],
            "owner_contribution": [],
        }
    _group, revision = current
    return {
        "system_categories": _system_category_composition(session, revision),
        "currency_exposure": _currency_exposure(session, revision),
        "owner_contribution": _member_details(session, revision),
    }


def _latest_finalized_context(
    session: Session,
) -> tuple[SnapshotGroup, SnapshotGroupRevision] | None:
    revision = session.exec(
        select(SnapshotGroupRevision)
        .where(SnapshotGroupRevision.status == "finalized")
        .order_by(
            SnapshotGroupRevision.finalized_at.desc(),
            SnapshotGroupRevision.id.desc(),
        )
    ).first()
    if revision is None:
        return None
    group = session.get(SnapshotGroup, revision.snapshot_group_id)
    if group is None or group.active_revision_id != revision.id:
        return None
    return group, revision


def _finalized_contexts(
    session: Session,
) -> list[tuple[SnapshotGroup, SnapshotGroupRevision]]:
    contexts: list[tuple[SnapshotGroup, SnapshotGroupRevision]] = []
    revisions = session.exec(
        select(SnapshotGroupRevision)
        .where(SnapshotGroupRevision.status == "finalized")
        .order_by(SnapshotGroupRevision.finalized_at, SnapshotGroupRevision.id)
    ).all()
    for revision in revisions:
        group = session.get(SnapshotGroup, revision.snapshot_group_id)
        if group is not None and group.active_revision_id == revision.id:
            contexts.append((group, revision))
    return contexts


def _revision_totals(
    session: Session,
    revision: SnapshotGroupRevision,
) -> dict[str, Decimal]:
    assets = Decimal("0")
    liabilities = Decimal("0")
    rates = _fx_rates(session, revision)
    for member in _revision_members(session, revision):
        for item in snapshot_items(session, member.owner_snapshot_id):
            amount = Decimal(item.amount_original or "0")
            official_amount = amount * rates.get(item.currency, Decimal("1"))
            if item.item_type == "asset":
                assets += official_amount
            elif item.item_type == "liability":
                liabilities += official_amount
    return {
        "assets": assets,
        "liabilities": liabilities,
        "net_worth": assets - liabilities,
    }


def _member_details(session: Session, revision: SnapshotGroupRevision) -> list[dict]:
    rates = _fx_rates(session, revision)
    details = []
    for member in _revision_members(session, revision):
        owner = session.get(Owner, member.owner_id)
        assets = Decimal("0")
        liabilities = Decimal("0")
        for item in snapshot_items(session, member.owner_snapshot_id):
            amount = Decimal(item.amount_original or "0")
            official_amount = amount * rates.get(item.currency, Decimal("1"))
            if item.item_type == "asset":
                assets += official_amount
            elif item.item_type == "liability":
                liabilities += official_amount
        details.append(
            {
                "owner_id": f"owner_{member.owner_id}",
                "owner_name": owner.name if owner else None,
                "owner_snapshot_id": f"snap_{member.owner_snapshot_id}",
                "asset_total_official": format_money(assets),
                "liability_total_official": format_money(liabilities),
                "net_worth_official": format_money(assets - liabilities),
            }
        )
    return details


def _revision_members(
    session: Session,
    revision: SnapshotGroupRevision,
) -> list[SnapshotGroupMember]:
    return list(
        session.exec(
            select(SnapshotGroupMember)
            .where(SnapshotGroupMember.snapshot_group_revision_id == revision.id)
            .order_by(SnapshotGroupMember.owner_id)
        )
    )


def _fx_rates(
    session: Session,
    revision: SnapshotGroupRevision,
) -> dict[str, Decimal]:
    rates = {revision.base_currency: Decimal("1")}
    if revision.fx_rate_set_id is None:
        return rates
    for rate in session.exec(
        select(FxRate).where(FxRate.fx_rate_set_id == revision.fx_rate_set_id)
    ):
        rates[rate.currency] = Decimal(rate.rate_to_base)
    return rates


def _system_category_composition(
    session: Session,
    revision: SnapshotGroupRevision,
) -> list[dict]:
    rates = _fx_rates(session, revision)
    totals: dict[int, Decimal] = {}
    for member in _revision_members(session, revision):
        for item in snapshot_items(session, member.owner_snapshot_id):
            amount = Decimal(item.amount_original or "0")
            totals[item.system_category_id] = totals.get(
                item.system_category_id, Decimal("0")
            ) + amount * rates.get(item.currency, Decimal("1"))
    rows = []
    for category_id, total in sorted(totals.items()):
        category = session.get(SystemCategory, category_id)
        rows.append(
            {
                "system_category_id": f"cat_{category_id}",
                "system_category_code": category.code if category else None,
                "system_category_name": category.name if category else None,
                "amount_official": format_money(total),
            }
        )
    return rows


def _currency_exposure(
    session: Session,
    revision: SnapshotGroupRevision,
) -> list[dict]:
    rates = _fx_rates(session, revision)
    original_totals: dict[str, Decimal] = {}
    official_totals: dict[str, Decimal] = {}
    for member in _revision_members(session, revision):
        for item in snapshot_items(session, member.owner_snapshot_id):
            amount = Decimal(item.amount_original or "0")
            original_totals[item.currency] = original_totals.get(
                item.currency, Decimal("0")
            ) + amount
            official_totals[item.currency] = official_totals.get(
                item.currency, Decimal("0")
            ) + amount * rates.get(item.currency, Decimal("1"))
    return [
        {
            "currency": currency,
            "amount_original": format_money(original_totals[currency]),
            "amount_official": format_money(official_totals[currency]),
        }
        for currency in sorted(original_totals)
    ]
