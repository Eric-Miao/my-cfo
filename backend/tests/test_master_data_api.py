import pytest
from sqlmodel import Session, create_engine, select

from backend.app.core.config import settings
from backend.app.core.security import hash_password
from backend.app.db.base import SQLModel
from backend.app.models.category import SystemCategory
from backend.app.models.owner import Owner
from backend.app.models.tag import Tag
from backend.app.models.template import (
    BalanceSheetItemTemplate,
    BalanceSheetItemTemplateTag,
)


def test_owner_active_state_persists(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        owner = Owner(name="Owner A", display_order=10, active=True)
        session.add(owner)
        session.commit()
        session.refresh(owner)

        owner.active = False
        session.add(owner)
        session.commit()

    with Session(engine) as session:
        saved_owner = session.exec(select(Owner)).one()

    assert saved_owner.name == "Owner A"
    assert saved_owner.active is False


def test_template_tag_join_persists(tmp_path) -> None:
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
        tag = Tag(name="liquid", normalized_name="liquid")
        session.add_all([owner, category, tag])
        session.commit()
        session.refresh(owner)
        session.refresh(category)
        session.refresh(tag)

        template = BalanceSheetItemTemplate(
            owner_id=owner.id,
            item_type="asset",
            system_category_id=category.id,
            account_name="WeChat Wallet",
            institution_name="WeChat",
            currency="CNY",
            display_order=10,
        )
        session.add(template)
        session.commit()
        session.refresh(template)

        session.add(
            BalanceSheetItemTemplateTag(template_id=template.id, tag_id=tag.id)
        )
        session.commit()
        template_id = template.id
        tag_id = tag.id

    with Session(engine) as session:
        link = session.exec(select(BalanceSheetItemTemplateTag)).one()

    assert link.template_id == template_id
    assert link.tag_id == tag_id


async def login_admin(async_client) -> None:
    object.__setattr__(settings, "admin_password_hash", hash_password("test-password"))
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"password": "test-password"},
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_create_deactivate_and_recover_owner(async_client) -> None:
    await login_admin(async_client)

    create_response = await async_client.post(
        "/api/v1/owners",
        json={"name": "Owner A", "display_order": 10},
    )

    assert create_response.status_code == 201
    owner = create_response.json()
    assert owner["id"].startswith("owner_")
    assert owner["name"] == "Owner A"
    assert owner["active"] is True

    deactivate_response = await async_client.post(
        f"/api/v1/owners/{owner['id']}/deactivate"
    )
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["active"] is False

    recover_response = await async_client.post(f"/api/v1/owners/{owner['id']}/recover")
    assert recover_response.status_code == 200
    assert recover_response.json()["active"] is True


@pytest.mark.anyio
async def test_create_system_category(async_client) -> None:
    await login_admin(async_client)

    response = await async_client.post(
        "/api/v1/system-categories",
        json={
            "item_type": "asset",
            "code": "cash",
            "name": "Cash",
            "calculation_role": "asset_total",
            "display_order": 10,
        },
    )

    assert response.status_code == 201
    category = response.json()
    assert category["id"].startswith("cat_")
    assert category["code"] == "cash"
    assert category["active"] is True


@pytest.mark.anyio
async def test_create_duplicate_tag_returns_conflict(async_client) -> None:
    await login_admin(async_client)

    first_response = await async_client.post("/api/v1/tags", json={"name": "Liquid"})
    second_response = await async_client.post("/api/v1/tags", json={"name": " liquid "})

    assert first_response.status_code == 201
    assert first_response.json()["normalized_name"] == "liquid"
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == "conflict"
