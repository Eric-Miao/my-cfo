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


async def create_confirmed_snapshot(
    async_client,
    *,
    owner_name: str,
    currency: str,
    amount: str,
) -> tuple[str, str]:
    owner_response = await async_client.post(
        "/api/v1/owners",
        json={"name": owner_name, "display_order": 10},
    )
    assert owner_response.status_code == 201
    owner_id = owner_response.json()["id"]

    category_response = await async_client.post(
        "/api/v1/system-categories",
        json={
            "item_type": "asset",
            "code": f"cash_{owner_name.lower().replace(' ', '_')}",
            "name": "Cash",
            "calculation_role": "asset_total",
            "display_order": 10,
        },
    )
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    template_response = await async_client.post(
        "/api/v1/templates",
        json={
            "owner_id": owner_id,
            "item_type": "asset",
            "system_category_id": category_id,
            "account_name": f"{owner_name} Wallet",
            "institution_name": "Wallet",
            "currency": currency,
            "display_order": 10,
            "tag_ids": [],
        },
    )
    assert template_response.status_code == 201

    snapshot_response = await async_client.post(
        "/api/v1/owner-snapshots",
        json={"owner_id": owner_id, "reporting_at": "2026-03-31T15:59:59Z"},
    )
    assert snapshot_response.status_code == 201
    snapshot = snapshot_response.json()
    item_id = snapshot["items"][0]["id"]

    update_response = await async_client.patch(
        f"/api/v1/owner-snapshots/{snapshot['id']}/items/{item_id}",
        json={"amount_original": amount},
    )
    assert update_response.status_code == 200

    confirm_response = await async_client.post(
        f"/api/v1/owner-snapshots/{snapshot['id']}/confirm"
    )
    assert confirm_response.status_code == 200
    return owner_id, snapshot["id"]


@pytest.mark.anyio
async def test_create_group_requires_every_active_owner(async_client) -> None:
    await login_admin(async_client)
    owner_a, snapshot_a = await create_confirmed_snapshot(
        async_client,
        owner_name="Owner A",
        currency="CNY",
        amount="100.00",
    )
    await create_confirmed_snapshot(
        async_client,
        owner_name="Owner B",
        currency="USD",
        amount="10.00",
    )

    response = await async_client.post(
        "/api/v1/snapshot-groups",
        json={
            "label": "March Household",
            "members": [{"owner_id": owner_a, "owner_snapshot_id": snapshot_a}],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.anyio
async def test_create_and_finalize_group_with_manual_fx(async_client) -> None:
    await login_admin(async_client)
    owner_a, snapshot_a = await create_confirmed_snapshot(
        async_client,
        owner_name="Owner A",
        currency="CNY",
        amount="100.00",
    )
    owner_b, snapshot_b = await create_confirmed_snapshot(
        async_client,
        owner_name="Owner B",
        currency="USD",
        amount="10.00",
    )

    create_response = await async_client.post(
        "/api/v1/snapshot-groups",
        json={
            "label": "March Household",
            "members": [
                {"owner_id": owner_a, "owner_snapshot_id": snapshot_a},
                {"owner_id": owner_b, "owner_snapshot_id": snapshot_b},
            ],
        },
    )

    assert create_response.status_code == 201
    group = create_response.json()
    assert group["id"].startswith("group_")
    assert group["reporting_at"].endswith("Z")
    assert group["active_revision"]["status"] == "draft"
    assert len(group["active_revision"]["members"]) == 2

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
    finalized = finalize_response.json()
    assert finalized["active_revision"]["status"] == "finalized"
    assert finalized["active_revision"]["fx_rate_set_id"].startswith("fxset_")

    rate_set_id = finalized["active_revision"]["fx_rate_set_id"]
    rate_set_response = await async_client.get(f"/api/v1/fx-rate-sets/{rate_set_id}")
    assert rate_set_response.status_code == 200
    assert rate_set_response.json()["rates"] == [
        {"currency": "USD", "rate_to_base": "7.25000000"}
    ]


@pytest.mark.anyio
async def test_group_member_snapshot_must_be_confirmed(async_client) -> None:
    await login_admin(async_client)
    owner_response = await async_client.post(
        "/api/v1/owners",
        json={"name": "Owner A", "display_order": 10},
    )
    owner_id = owner_response.json()["id"]
    category_response = await async_client.post(
        "/api/v1/system-categories",
        json={
            "item_type": "asset",
            "code": "cash",
            "name": "Cash",
            "calculation_role": "asset_total",
            "display_order": 10,
        },
    )
    await async_client.post(
        "/api/v1/templates",
        json={
            "owner_id": owner_id,
            "item_type": "asset",
            "system_category_id": category_response.json()["id"],
            "account_name": "Wallet",
            "institution_name": "Wallet",
            "currency": "CNY",
            "display_order": 10,
            "tag_ids": [],
        },
    )
    draft_response = await async_client.post(
        "/api/v1/owner-snapshots",
        json={"owner_id": owner_id, "reporting_at": "2026-03-31T15:59:59Z"},
    )

    response = await async_client.post(
        "/api/v1/snapshot-groups",
        json={
            "label": "Draft household",
            "members": [
                {"owner_id": owner_id, "owner_snapshot_id": draft_response.json()["id"]}
            ],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
