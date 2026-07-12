import httpx
import pytest

from backend.app.main import app


@pytest.mark.anyio
async def test_health_endpoint_returns_service_status() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "my-cfo",
        "environment": "development",
    }


@pytest.mark.anyio
async def test_openapi_schema_includes_health_endpoint() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "my-cfo"
    assert "/health" in schema["paths"]
