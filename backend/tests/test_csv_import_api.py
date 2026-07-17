import csv
import io
import json
from pathlib import Path

import pytest

from backend.app.core.config import settings
from backend.app.core.security import hash_password
from backend.app.domain.csv_import import TEMPLATE_EXPORT_COLUMNS


async def login_admin(async_client) -> None:
    object.__setattr__(settings, "admin_password_hash", hash_password("test-password"))
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"password": "test-password"},
    )
    assert response.status_code == 200


async def create_export_template(
    async_client,
    *,
    owner_name: str = "Owner A",
    category_name: str = "Cash",
    account_name: str = "Wallet",
    institution_name: str = "Wallet",
    tag_name: str = "Liquid",
) -> dict:
    owner_response = await async_client.post(
        "/api/v1/owners",
        json={"name": owner_name, "display_order": 10},
    )
    owner_id = owner_response.json()["id"]
    category_response = await async_client.post(
        "/api/v1/system-categories",
        json={
            "item_type": "asset",
            "code": "cash",
            "name": category_name,
            "calculation_role": "asset_total",
            "display_order": 10,
        },
    )
    category_id = category_response.json()["id"]
    tag_response = await async_client.post("/api/v1/tags", json={"name": tag_name})
    tag_id = tag_response.json()["id"]
    template_response = await async_client.post(
        "/api/v1/templates",
        json={
            "owner_id": owner_id,
            "item_type": "asset",
            "system_category_id": category_id,
            "account_name": account_name,
            "institution_name": institution_name,
            "currency": "CNY",
            "display_order": 10,
            "tag_ids": [tag_id],
        },
    )
    assert template_response.status_code == 201
    return template_response.json()


def parse_csv(text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def test_sanitized_sample_fixture_exists() -> None:
    path = Path("backend/tests/fixtures/sample_balance_sheet.json")
    data = json.loads(path.read_text())

    assert data["owners"] == ["Owner A", "Owner B"]
    assert "CNY" in data["currencies"]
    assert "USD" in data["currencies"]
    assert data["templates"][0]["account_name"] == "WeChat Wallet"


@pytest.mark.anyio
async def test_export_template_csv_column_order_and_active_filter(async_client) -> None:
    await login_admin(async_client)
    active_template = await create_export_template(async_client)
    inactive_template = await create_export_template(
        async_client,
        owner_name="Owner B",
        account_name="Inactive Wallet",
        tag_name="Inactive",
    )
    await async_client.post(f"/api/v1/templates/{inactive_template['id']}/deactivate")

    response = await async_client.get("/api/v1/csv/templates/export")

    assert response.status_code == 200
    header = response.text.splitlines()[0].split(",")
    assert header == TEMPLATE_EXPORT_COLUMNS
    rows = parse_csv(response.text)
    assert len(rows) == 1
    assert rows[0]["template_id"] == active_template["id"]
    assert rows[0]["amount_original"] == ""
    assert rows[0]["note"] == ""


@pytest.mark.anyio
async def test_export_escapes_formula_triggering_text(async_client) -> None:
    await login_admin(async_client)
    await create_export_template(
        async_client,
        owner_name="=Owner",
        category_name="-Cash",
        account_name="+Wallet",
        institution_name="@Wallet",
    )

    response = await async_client.get("/api/v1/csv/templates/export")

    assert response.status_code == 200
    row = parse_csv(response.text)[0]
    assert row["owner_name"] == "'=Owner"
    assert row["system_category_name"] == "'-Cash"
    assert row["account_name"] == "'+Wallet"
    assert row["institution_name"] == "'@Wallet"
