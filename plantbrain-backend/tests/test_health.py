"""Health endpoint tests for the PlantBrain API."""

import pytest


@pytest.mark.asyncio
async def test_root_health(client) -> None:
    """Root health endpoint returns healthy status."""

    response = await client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_api_health_has_timestamp(client) -> None:
    """Versioned health endpoint returns healthy status and timestamp."""

    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "timestamp" in body


@pytest.mark.asyncio
async def test_nonexistent_route_returns_404(client) -> None:
    """Unknown routes return 404."""

    response = await client.get("/nonexistent")

    assert response.status_code == 404
