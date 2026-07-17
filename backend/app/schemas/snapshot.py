from pydantic import BaseModel

from backend.app.models.snapshot import OwnerSnapshot, SnapshotItem
from backend.app.schemas.ids import public_id


class OwnerSnapshotCreate(BaseModel):
    owner_id: str
    reporting_at: str
    label: str | None = None


class SnapshotItemPatch(BaseModel):
    amount_original: str | None = None
    note: str | None = None


class SnapshotItemRead(BaseModel):
    id: str
    template_id: str
    item_type: str
    system_category_id: str
    system_category_code_snapshot: str
    system_category_name_snapshot: str
    account_name_snapshot: str
    institution_name_snapshot: str | None
    currency: str
    amount_original: str | None
    note: str | None
    display_order: int

    @classmethod
    def from_model(cls, item: SnapshotItem) -> "SnapshotItemRead":
        return cls(
            id=public_id("item", item.id),
            template_id=public_id("tpl", item.template_id),
            item_type=item.item_type,
            system_category_id=public_id("cat", item.system_category_id),
            system_category_code_snapshot=item.system_category_code_snapshot,
            system_category_name_snapshot=item.system_category_name_snapshot,
            account_name_snapshot=item.account_name_snapshot,
            institution_name_snapshot=item.institution_name_snapshot,
            currency=item.currency,
            amount_original=item.amount_original,
            note=item.note,
            display_order=item.display_order,
        )


class OwnerSnapshotRead(BaseModel):
    id: str
    owner_id: str
    reporting_at: str
    status: str
    source: str
    label: str | None
    items: list[SnapshotItemRead]

    @classmethod
    def from_model(
        cls,
        snapshot: OwnerSnapshot,
        items: list[SnapshotItem],
    ) -> "OwnerSnapshotRead":
        return cls(
            id=public_id("snap", snapshot.id),
            owner_id=public_id("owner", snapshot.owner_id),
            reporting_at=snapshot.reporting_at,
            status=snapshot.status,
            source=snapshot.source,
            label=snapshot.label,
            items=[SnapshotItemRead.from_model(item) for item in items],
        )
