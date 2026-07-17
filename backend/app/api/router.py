from fastapi import APIRouter, Depends

from backend.app.api.deps import require_admin
from backend.app.api.routes import auth, categories, owners, tags, templates
from backend.app.core.config import settings

router = APIRouter(prefix="/api/v1")
protected_router = APIRouter(dependencies=[Depends(require_admin)])


@protected_router.get("/meta", tags=["system"])
def meta() -> dict[str, str]:
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "api_version": "v1",
        "official_base_currency": settings.official_base_currency,
        "fx_provider": settings.fx_provider,
    }


protected_router.include_router(owners.router)
protected_router.include_router(categories.router)
protected_router.include_router(tags.router)
protected_router.include_router(templates.router)
router.include_router(auth.router)
router.include_router(protected_router)
