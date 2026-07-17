import pytest

from backend.app.core.config import Settings


def test_production_rejects_placeholder_session_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SESSION_SECRET", "change-me")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "$argon2id$placeholder")

    with pytest.raises(ValueError, match="SESSION_SECRET"):
        Settings.from_env()


@pytest.mark.anyio
async def test_openapi_schema_includes_api_v1_meta(async_client) -> None:
    response = await async_client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert "/api/v1/meta" in schema["paths"]


@pytest.mark.anyio
async def test_api_meta_requires_authentication(async_client) -> None:
    response = await async_client.get("/api/v1/meta")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
