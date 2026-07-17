from sqlmodel import Session, create_engine, select

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
