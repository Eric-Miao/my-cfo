from sqlmodel import Session, create_engine, select

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
