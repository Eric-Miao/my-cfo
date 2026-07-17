import pytest

from backend.app.core.config import settings
from backend.app.core.security import hash_password


async def login_admin(async_client) -> None:
    object.__setattr__(settings, "admin_password_hash", hash_password("test-password"))
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"password": "test-password"},
    )
    assert response.status_code == 200


async def create_owner_snapshot_with_asset_and_liability(
    async_client,
) -> tuple[str, str]:
    owner_response = await async_client.post(
        "/api/v1/owners",
        json={"name": "Owner A", "display_order": 10},
    )
    owner_id = owner_response.json()["id"]

    asset_category_response = await async_client.post(
        "/api/v1/system-categories",
        json={
            "item_type": "asset",
            "code": "cash",
            "name": "Cash",
            "calculation_role": "asset_total",
            "display_order": 10,
        },
    )
    liability_category_response = await async_client.post(
        "/api/v1/system-categories",
        json={
            "item_type": "liability",
            "code": "credit_card",
            "name": "Credit Card",
            "calculation_role": "liability_total",
            "display_order": 20,
        },
    )
    asset_category_id = asset_category_response.json()["id"]
    liability_category_id = liability_category_response.json()["id"]

    await async_client.post(
        "/api/v1/templates",
        json={
            "owner_id": owner_id,
            "item_type": "asset",
            "system_category_id": asset_category_id,
            "account_name": "USD Brokerage",
            "institution_name": "Brokerage",
            "currency": "USD",
            "display_order": 10,
            "tag_ids": [],
        },
    )
    await async_client.post(
        "/api/v1/templates",
        json={
            "owner_id": owner_id,
            "item_type": "liability",
            "system_category_id": liability_category_id,
            "account_name": "CNY Card",
            "institution_name": "Card",
            "currency": "CNY",
            "display_order": 20,
            "tag_ids": [],
        },
    )

    snapshot_response = await async_client.post(
        "/api/v1/owner-snapshots",
        json={"owner_id": owner_id, "reporting_at": "2026-03-31T15:59:59Z"},
    )
    snapshot = snapshot_response.json()
    for item in snapshot["items"]:
        amount = "10.00000000" if item["item_type"] == "asset" else "20.00000000"
        await async_client.patch(
            f"/api/v1/owner-snapshots/{snapshot['id']}/items/{item['id']}",
            json={"amount_original": amount},
        )
    confirm_response = await async_client.post(
        f"/api/v1/owner-snapshots/{snapshot['id']}/confirm"
    )
    assert confirm_response.status_code == 200
    return owner_id, snapshot["id"]


async def create_finalized_group(async_client) -> dict:
    owner_id, snapshot_id = await create_owner_snapshot_with_asset_and_liability(
        async_client
    )
    create_response = await async_client.post(
        "/api/v1/snapshot-groups",
        json={
            "label": "March Household",
            "members": [{"owner_id": owner_id, "owner_snapshot_id": snapshot_id}],
        },
    )
    group = create_response.json()
    finalize_response = await async_client.post(
        f"/api/v1/snapshot-groups/{group['id']}/finalize",
        json={
            "fx_rates": {
                "mode": "manual",
                "manual_rates": [
                    {"currency": "USD", "rate_to_base": "7.25000000"}
                ],
            }
        },
    )
    assert finalize_response.status_code == 200
    return finalize_response.json()


@pytest.mark.anyio
async def test_household_overview_uses_latest_finalized_group_fx(async_client) -> None:
    await login_admin(async_client)
    finalized_group = await create_finalized_group(async_client)

    response = await async_client.get("/api/v1/dashboard/household-overview")

    assert response.status_code == 200
    overview = response.json()
    assert overview["official_base_currency"] == "CNY"
    assert overview["display_values_are_estimates"] is False
    assert overview["current"]["group_id"] == finalized_group["id"]
    assert overview["current"]["total_assets_official"] == "72.50000000"
    assert overview["current"]["total_liabilities_official"] == "20.00000000"
    assert overview["current"]["net_worth_official"] == "52.50000000"


@pytest.mark.anyio
async def test_latest_group_detail_returns_frozen_members(async_client) -> None:
    await login_admin(async_client)
    finalized_group = await create_finalized_group(async_client)

    response = await async_client.get("/api/v1/dashboard/latest-group-detail")

    assert response.status_code == 200
    detail = response.json()
    assert detail["group_id"] == finalized_group["id"]
    assert len(detail["members"]) == 1
    assert detail["members"][0]["owner_name"] == "Owner A"
    assert detail["members"][0]["asset_total_official"] == "72.50000000"
    assert detail["members"][0]["liability_total_official"] == "20.00000000"
