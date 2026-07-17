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


async def create_owner(async_client) -> str:
    response = await async_client.post(
        "/api/v1/owners",
        json={"name": "Owner A", "display_order": 10},
    )
    assert response.status_code == 201
    return response.json()["id"]


async def create_category(async_client, item_type: str = "asset") -> str:
    response = await async_client.post(
        "/api/v1/system-categories",
        json={
            "item_type": item_type,
            "code": f"{item_type}_cash",
            "name": f"{item_type.title()} Cash",
            "calculation_role": f"{item_type}_total",
            "display_order": 10,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def create_tag(async_client) -> str:
    response = await async_client.post("/api/v1/tags", json={"name": "Liquid"})
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.anyio
async def test_create_template_with_tags(async_client) -> None:
    await login_admin(async_client)
    owner_id = await create_owner(async_client)
    category_id = await create_category(async_client)
    tag_id = await create_tag(async_client)

    response = await async_client.post(
        "/api/v1/templates",
        json={
            "owner_id": owner_id,
            "item_type": "asset",
            "system_category_id": category_id,
            "account_name": "WeChat Wallet",
            "institution_name": "WeChat",
            "currency": "CNY",
            "display_order": 10,
            "tag_ids": [tag_id],
        },
    )

    assert response.status_code == 201
    template = response.json()
    assert template["id"].startswith("tpl_")
    assert template["owner_id"] == owner_id
    assert template["tags"] == [{"id": tag_id, "name": "Liquid"}]


@pytest.mark.anyio
async def test_template_rejects_category_item_type_mismatch(async_client) -> None:
    await login_admin(async_client)
    owner_id = await create_owner(async_client)
    category_id = await create_category(async_client, item_type="liability")

    response = await async_client.post(
        "/api/v1/templates",
        json={
            "owner_id": owner_id,
            "item_type": "asset",
            "system_category_id": category_id,
            "account_name": "Credit Card",
            "institution_name": "Chase",
            "currency": "USD",
            "display_order": 10,
            "tag_ids": [],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.anyio
async def test_institution_suggestions_derive_from_templates(async_client) -> None:
    await login_admin(async_client)
    owner_id = await create_owner(async_client)
    category_id = await create_category(async_client)

    create_response = await async_client.post(
        "/api/v1/templates",
        json={
            "owner_id": owner_id,
            "item_type": "asset",
            "system_category_id": category_id,
            "account_name": "Fidelity Brokerage",
            "institution_name": "Fidelity",
            "currency": "USD",
            "display_order": 10,
            "tag_ids": [],
        },
    )
    assert create_response.status_code == 201

    response = await async_client.get("/api/v1/institution-suggestions?query=del")

    assert response.status_code == 200
    assert response.json()["items"] == ["Fidelity"]
