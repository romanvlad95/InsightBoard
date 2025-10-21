import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")

    assert response.status_code == 200

    response_data = response.json()
    assert response_data["status"] == "ok"

    assert "services" in response_data
    assert isinstance(response_data["services"], dict)

    # In a test environment, we might only have the core API and DB running.
    # We check for the API service specifically.
    assert response_data["services"].get("api") == "healthy"
