from fastapi import APIRouter

from backend.app.api.deps import SessionDep
from backend.app.services import dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/household-overview")
def household_overview(
    session: SessionDep,
    display_currency: str | None = None,
) -> dict:
    return dashboard.household_overview(session, display_currency)


@router.get("/latest-group-detail")
def latest_group_detail(session: SessionDep) -> dict:
    return dashboard.latest_group_detail(session)


@router.get("/net-worth-trend")
def net_worth_trend(session: SessionDep) -> dict:
    return dashboard.net_worth_trend(session)


@router.get("/assets-liabilities-trend")
def assets_liabilities_trend(session: SessionDep) -> dict:
    return dashboard.assets_liabilities_trend(session)


@router.get("/owner-net-worth-trend")
def owner_net_worth_trend(session: SessionDep) -> dict:
    return dashboard.owner_net_worth_trend(session)


@router.get("/composition")
def composition(session: SessionDep) -> dict:
    return dashboard.composition(session)
