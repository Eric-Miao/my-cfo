from decimal import Decimal

from sqlmodel import Session, select

from backend.app.core.config import settings
from backend.app.domain.dashboard import format_money
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
