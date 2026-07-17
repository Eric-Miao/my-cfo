from fastapi import APIRouter

router = APIRouter(prefix="/owners", tags=["owners"])


@router.get("")
def list_owners() -> dict[str, object]:
    return {"items": [], "page": {"limit": 50, "next_cursor": None}}
