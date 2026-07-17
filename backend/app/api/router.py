from fastapi import APIRouter

from backend.app.core.config import settings

router = APIRouter(prefix="/api/v1")


@router.get("/meta", tags=["system"])
def meta() -> dict[str, str]:
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "api_version": "v1",
        "official_base_currency": settings.official_base_currency,
        "fx_provider": settings.fx_provider,
    }
