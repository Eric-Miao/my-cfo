import pytest


@pytest.mark.anyio
async def test_health_endpoint_returns_service_status(async_client) -> None:
    response = await async_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "my-cfo",
        "environment": "development",
    }


@pytest.mark.anyio
async def test_openapi_schema_includes_health_endpoint(async_client) -> None:
    response = await async_client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "my-cfo"
    assert "/health" in schema["paths"]
