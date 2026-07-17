import pytest
from sqlmodel import Session, create_engine, select

from backend.app.core.config import settings
from backend.app.core.security import hash_password
from backend.app.db.base import SQLModel
from backend.app.models.category import SystemCategory
from backend.app.models.owner import Owner
from backend.app.models.snapshot import OwnerSnapshot, SnapshotItem
from backend.app.models.template import BalanceSheetItemTemplate


def test_snapshot_item_keeps_copied_template_fields(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        owner = Owner(name="Owner A", display_order=10)
        category = SystemCategory(
            item_type="asset",
            code="cash",
            name="Cash",
            calculation_role="asset_total",
            display_order=10,
        )
        session.add_all([owner, category])
        session.commit()
        session.refresh(owner)
        session.refresh(category)

        template = BalanceSheetItemTemplate(
            owner_id=owner.id,
            item_type="asset",
            system_category_id=category.id,
            account_name="Original Name",
            institution_name="Original Institution",
            currency="CNY",
            display_order=10,
        )
        session.add(template)
        session.commit()
        session.refresh(template)

        snapshot = OwnerSnapshot(
            owner_id=owner.id,
            reporting_at="2026-03-31T15:59:59Z",
            status="draft",
            source="manual",
            label="March",
        )
        session.add(snapshot)
        session.commit()
        session.refresh(snapshot)

        item = SnapshotItem(
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
        session.add(item)
        session.commit()

        template.account_name = "Renamed Future Template"
        session.add(template)
        session.commit()

    with Session(engine) as session:
        saved_item = session.exec(select(SnapshotItem)).one()

    assert saved_item.account_name_snapshot == "Original Name"
    assert saved_item.institution_name_snapshot == "Original Institution"
    assert saved_item.system_category_code_snapshot == "cash"


async def login_admin(async_client) -> None:
    object.__setattr__(settings, "admin_password_hash", hash_password("test-password"))
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"password": "test-password"},
    )
    assert response.status_code == 200


async def create_snapshot_template(async_client) -> tuple[str, str]:
    owner_response = await async_client.post(
        "/api/v1/owners",
        json={"name": "Owner A", "display_order": 10},
    )
    assert owner_response.status_code == 201
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
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    template_response = await async_client.post(
        "/api/v1/templates",
        json={
            "owner_id": owner_id,
            "item_type": "asset",
            "system_category_id": category_id,
            "account_name": "WeChat Wallet",
            "institution_name": "WeChat",
            "currency": "CNY",
            "display_order": 10,
            "tag_ids": [],
        },
    )
    assert template_response.status_code == 201
    return owner_id, template_response.json()["id"]


@pytest.mark.anyio
async def test_create_draft_snapshot_from_active_templates(async_client) -> None:
    await login_admin(async_client)
    owner_id, template_id = await create_snapshot_template(async_client)

    response = await async_client.post(
        "/api/v1/owner-snapshots",
        json={"owner_id": owner_id, "reporting_at": "2026-03-31T15:59:59Z"},
    )

    assert response.status_code == 201
    snapshot = response.json()
    assert snapshot["id"].startswith("snap_")
    assert snapshot["status"] == "draft"
    assert snapshot["items"][0]["template_id"] == template_id
    assert snapshot["items"][0]["account_name_snapshot"] == "WeChat Wallet"
    assert snapshot["items"][0]["amount_original"] is None


@pytest.mark.anyio
async def test_update_item_and_confirm_snapshot(async_client) -> None:
    await login_admin(async_client)
    owner_id, _template_id = await create_snapshot_template(async_client)
    create_response = await async_client.post(
        "/api/v1/owner-snapshots",
        json={"owner_id": owner_id, "reporting_at": "2026-03-31T15:59:59Z"},
    )
    snapshot = create_response.json()
    item_id = snapshot["items"][0]["id"]

    negative_response = await async_client.patch(
        f"/api/v1/owner-snapshots/{snapshot['id']}/items/{item_id}",
        json={"amount_original": "-1.00"},
    )
    assert negative_response.status_code == 422

    update_response = await async_client.patch(
        f"/api/v1/owner-snapshots/{snapshot['id']}/items/{item_id}",
        json={"amount_original": "3455.42000000", "note": "checked"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["items"][0]["amount_original"] == "3455.42000000"

    confirm_response = await async_client.post(
        f"/api/v1/owner-snapshots/{snapshot['id']}/confirm"
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "confirmed"

    stale_update_response = await async_client.patch(
        f"/api/v1/owner-snapshots/{snapshot['id']}/items/{item_id}",
        json={"amount_original": "1.00"},
    )
    assert stale_update_response.status_code == 409


@pytest.mark.anyio
async def test_confirm_rejects_incomplete_snapshot(async_client) -> None:
    await login_admin(async_client)
    owner_id, _template_id = await create_snapshot_template(async_client)
    create_response = await async_client.post(
        "/api/v1/owner-snapshots",
        json={"owner_id": owner_id, "reporting_at": "2026-03-31T15:59:59Z"},
    )
    snapshot = create_response.json()

    response = await async_client.post(
        f"/api/v1/owner-snapshots/{snapshot['id']}/confirm"
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.anyio
async def test_cancel_draft_snapshot(async_client) -> None:
    await login_admin(async_client)
    owner_id, _template_id = await create_snapshot_template(async_client)
    create_response = await async_client.post(
        "/api/v1/owner-snapshots",
        json={"owner_id": owner_id, "reporting_at": "2026-03-31T15:59:59Z"},
    )
    snapshot = create_response.json()

    response = await async_client.post(
        f"/api/v1/owner-snapshots/{snapshot['id']}/cancel"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.anyio
async def test_replacement_snapshot_supersedes_original(async_client) -> None:
    await login_admin(async_client)
    owner_id, _template_id = await create_snapshot_template(async_client)
    create_response = await async_client.post(
        "/api/v1/owner-snapshots",
        json={"owner_id": owner_id, "reporting_at": "2026-03-31T15:59:59Z"},
    )
    original = create_response.json()
    item_id = original["items"][0]["id"]
    await async_client.patch(
        f"/api/v1/owner-snapshots/{original['id']}/items/{item_id}",
        json={"amount_original": "100.00"},
    )
    confirm_response = await async_client.post(
        f"/api/v1/owner-snapshots/{original['id']}/confirm"
    )
    assert confirm_response.status_code == 200

    replacement_response = await async_client.post(
        f"/api/v1/owner-snapshots/{original['id']}/replacements",
        json={"revision_note": "corrected balance"},
    )
    assert replacement_response.status_code == 201
    replacement = replacement_response.json()
    replacement_item_id = replacement["items"][0]["id"]
    assert replacement["status"] == "draft"
    assert replacement["items"][0]["amount_original"] == "100.00"

    await async_client.patch(
        f"/api/v1/owner-snapshots/{replacement['id']}/items/{replacement_item_id}",
        json={"amount_original": "101.00"},
    )
    replacement_confirm_response = await async_client.post(
        f"/api/v1/owner-snapshots/{replacement['id']}/confirm"
    )

    assert replacement_confirm_response.status_code == 200
    assert replacement_confirm_response.json()["status"] == "confirmed"

    original_detail_response = await async_client.get(
        f"/api/v1/owner-snapshots/{original['id']}"
    )
    assert original_detail_response.status_code == 200
    assert original_detail_response.json()["status"] == "superseded"
