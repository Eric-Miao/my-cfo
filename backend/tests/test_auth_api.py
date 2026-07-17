from http import HTTPStatus

import pytest

from backend.app.core.config import settings
from backend.app.core.security import hash_password


@pytest.fixture(autouse=True)
def auth_settings():
    original_hash = settings.admin_password_hash
    original_secret = settings.session_secret
    original_cookie_secure = settings.cookie_secure
    original_deployment_network = settings.deployment_network

    object.__setattr__(
        settings,
        "admin_password_hash",
        hash_password("correct-password"),
    )
    object.__setattr__(settings, "session_secret", "test-session-secret")
    object.__setattr__(settings, "cookie_secure", False)
    object.__setattr__(settings, "deployment_network", "lan")

    yield

    object.__setattr__(settings, "admin_password_hash", original_hash)
    object.__setattr__(settings, "session_secret", original_secret)
    object.__setattr__(settings, "cookie_secure", original_cookie_secure)
    object.__setattr__(settings, "deployment_network", original_deployment_network)


@pytest.mark.anyio
async def test_wrong_password_returns_401(async_client) -> None:
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"password": "wrong-password"},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["error"]["code"] == "unauthenticated"


@pytest.mark.anyio
async def test_correct_password_sets_http_only_cookie(async_client) -> None:
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"password": "correct-password"},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"authenticated": True, "principal": "admin"}
    set_cookie = response.headers["set-cookie"]
    assert "my_cfo_session=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "samesite=lax" in set_cookie.lower()


@pytest.mark.anyio
async def test_me_requires_session(async_client) -> None:
    response = await async_client.get("/api/v1/auth/me")

    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.anyio
async def test_protected_owners_rejects_no_session(async_client) -> None:
    response = await async_client.get("/api/v1/owners")

    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.anyio
async def test_logout_clears_cookie(async_client) -> None:
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"password": "correct-password"},
    )
    assert login_response.status_code == HTTPStatus.OK

    logout_response = await async_client.post("/api/v1/auth/logout")

    assert logout_response.status_code == HTTPStatus.OK
    assert logout_response.json() == {"authenticated": False}
    set_cookie = logout_response.headers["set-cookie"]
    assert "my_cfo_session=" in set_cookie
    assert "Max-Age=0" in set_cookie
