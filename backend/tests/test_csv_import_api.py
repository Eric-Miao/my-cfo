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


def render_csv(rows: list[dict[str, str]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TEMPLATE_EXPORT_COLUMNS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def fill_amounts(csv_text: str, amount: str = "100.00000000") -> str:
    rows = parse_csv(csv_text)
    for row in rows:
        row["amount_original"] = amount
    return render_csv(rows)


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


@pytest.mark.anyio
async def test_preview_rejects_changed_template_metadata(async_client) -> None:
    await login_admin(async_client)
    await create_export_template(async_client)
    export_response = await async_client.get("/api/v1/csv/templates/export")
    rows = parse_csv(fill_amounts(export_response.text))
    rows[0]["account_name"] = "Changed Wallet"

    response = await async_client.post(
        "/api/v1/csv/owner-snapshots/import/preview",
        json={
            "reporting_at": "2026-03-31T15:59:59Z",
            "csv_text": render_csv(rows),
        },
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["errors"][0]["field"] == "account_name"


@pytest.mark.anyio
async def test_preview_rejects_invalid_amounts(async_client) -> None:
    await login_admin(async_client)
    await create_export_template(async_client)
    export_response = await async_client.get("/api/v1/csv/templates/export")
    rows = parse_csv(export_response.text)
    rows[0]["amount_original"] = "-1"

    negative_response = await async_client.post(
        "/api/v1/csv/owner-snapshots/import/preview",
        json={
            "reporting_at": "2026-03-31T15:59:59Z",
            "csv_text": render_csv(rows),
        },
    )
    rows[0]["amount_original"] = "1.123456789"
    precision_response = await async_client.post(
        "/api/v1/csv/owner-snapshots/import/preview",
        json={
            "reporting_at": "2026-03-31T15:59:59Z",
            "csv_text": render_csv(rows),
        },
    )

    assert negative_response.json()["valid"] is False
    assert precision_response.json()["valid"] is False
    assert negative_response.json()["errors"][0]["field"] == "amount_original"


@pytest.mark.anyio
async def test_commit_creates_one_draft_snapshot_per_owner(async_client) -> None:
    await login_admin(async_client)
    await create_export_template(async_client, owner_name="Owner A", tag_name="A")
    await create_export_template(
        async_client,
        owner_name="Owner B",
        account_name="Second Wallet",
        tag_name="B",
    )
    export_response = await async_client.get("/api/v1/csv/templates/export")
    preview_response = await async_client.post(
        "/api/v1/csv/owner-snapshots/import/preview",
        json={
            "reporting_at": "2026-03-31T15:59:59Z",
            "csv_text": fill_amounts(export_response.text),
        },
    )
    assert preview_response.status_code == 200
    assert preview_response.json()["valid"] is True

    commit_response = await async_client.post(
        "/api/v1/csv/owner-snapshots/import/commit",
        json={"preview_token": preview_response.json()["preview_token"]},
    )

    assert commit_response.status_code == 201
    snapshots = commit_response.json()["draft_snapshots"]
    assert len(snapshots) == 2
    assert {snapshot["item_count"] for snapshot in snapshots} == {1}


@pytest.mark.anyio
async def test_commit_rejects_duplicate_draft_snapshot(async_client) -> None:
    await login_admin(async_client)
    await create_export_template(async_client)
    export_response = await async_client.get("/api/v1/csv/templates/export")

    preview_response = await async_client.post(
        "/api/v1/csv/owner-snapshots/import/preview",
        json={
            "reporting_at": "2026-03-31T15:59:59Z",
            "csv_text": fill_amounts(export_response.text),
        },
    )
    first_commit = await async_client.post(
        "/api/v1/csv/owner-snapshots/import/commit",
        json={"preview_token": preview_response.json()["preview_token"]},
    )
    second_preview = await async_client.post(
        "/api/v1/csv/owner-snapshots/import/preview",
        json={
            "reporting_at": "2026-03-31T15:59:59Z",
            "csv_text": fill_amounts(export_response.text),
        },
    )
    duplicate_commit = await async_client.post(
        "/api/v1/csv/owner-snapshots/import/commit",
        json={"preview_token": second_preview.json()["preview_token"]},
    )

    assert first_commit.status_code == 201
    assert duplicate_commit.status_code == 409
