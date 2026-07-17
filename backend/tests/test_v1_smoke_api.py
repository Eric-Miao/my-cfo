import pytest

from backend.app.core.config import settings
from backend.app.core.security import hash_password


@pytest.mark.anyio
async def test_v1_api_happy_path(async_client) -> None:
    object.__setattr__(settings, "admin_password_hash", hash_password("test-password"))

    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"password": "test-password"},
    )
    assert login_response.status_code == 200

    owner_response = await async_client.post(
        "/api/v1/owners",
        json={"name": "Owner A", "display_order": 10},
    )
    owner_id = owner_response.json()["id"]

    tag_response = await async_client.post("/api/v1/tags", json={"name": "Liquid"})
    tag_id = tag_response.json()["id"]

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

    for item_type, category_id, account_name in [
        ("asset", asset_category_response.json()["id"], "USD Brokerage"),
        ("liability", liability_category_response.json()["id"], "CNY Card"),
    ]:
        template_response = await async_client.post(
            "/api/v1/templates",
            json={
                "owner_id": owner_id,
                "item_type": item_type,
                "system_category_id": category_id,
                "account_name": account_name,
                "institution_name": "Smoke Institution",
                "currency": "USD" if item_type == "asset" else "CNY",
                "display_order": 10,
                "tag_ids": [tag_id],
            },
        )
        assert template_response.status_code == 201

    snapshot_response = await async_client.post(
        "/api/v1/owner-snapshots",
        json={"owner_id": owner_id, "reporting_at": "2026-03-31T15:59:59Z"},
    )
    snapshot = snapshot_response.json()

    for item in snapshot["items"]:
        amount = "10.00000000" if item["item_type"] == "asset" else "0"
        update_response = await async_client.patch(
            f"/api/v1/owner-snapshots/{snapshot['id']}/items/{item['id']}",
            json={"amount_original": amount},
        )
        assert update_response.status_code == 200

    confirm_response = await async_client.post(
        f"/api/v1/owner-snapshots/{snapshot['id']}/confirm"
    )
    assert confirm_response.status_code == 200

    group_response = await async_client.post(
        "/api/v1/snapshot-groups",
        json={
            "label": "Smoke Group",
            "members": [{"owner_id": owner_id, "owner_snapshot_id": snapshot["id"]}],
        },
    )
    group = group_response.json()

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

    dashboard_response = await async_client.get("/api/v1/dashboard/household-overview")
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["current"]["total_assets_official"] == (
        "72.50000000"
    )
    assert dashboard_response.json()["current"]["net_worth_official"] == "72.50000000"

    logout_response = await async_client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200
    me_response = await async_client.get("/api/v1/auth/me")
    assert me_response.status_code == 401
