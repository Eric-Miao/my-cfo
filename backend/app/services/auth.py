from backend.app.core.config import settings
from backend.app.core.security import verify_password


def authenticate_admin(password: str) -> bool:
    return verify_password(password, settings.admin_password_hash)
