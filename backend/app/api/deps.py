from http import HTTPStatus

from fastapi import Request

from backend.app.api.errors import ApiError
from backend.app.core.config import settings
from backend.app.core.security import SESSION_COOKIE_NAME, verify_session_token


def require_admin(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token or not verify_session_token(settings.session_secret, token):
        raise ApiError(
            status_code=HTTPStatus.UNAUTHORIZED,
            code="unauthenticated",
            message="Authentication is required.",
        )
    return "admin"
