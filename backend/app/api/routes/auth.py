from http import HTTPStatus

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from backend.app.api.deps import require_admin
from backend.app.api.errors import ApiError
from backend.app.core.config import settings
from backend.app.core.security import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    create_session_token,
)
from backend.app.services.auth import authenticate_admin

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
def login(payload: LoginRequest, response: Response) -> dict[str, str | bool]:
    if not authenticate_admin(payload.password):
        raise ApiError(
            status_code=HTTPStatus.UNAUTHORIZED,
            code="unauthenticated",
            message="Invalid password.",
        )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(settings.session_secret),
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return {"authenticated": True, "principal": "admin"}


@router.post("/logout", dependencies=[Depends(require_admin)])
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        samesite="lax",
        secure=settings.cookie_secure,
        httponly=True,
    )
    return {"authenticated": False}


@router.get("/me", dependencies=[Depends(require_admin)])
def me() -> dict[str, str | bool]:
    return {"authenticated": True, "principal": "admin"}
