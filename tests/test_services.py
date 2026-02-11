"""Tests for the service monitoring API."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_list_services(client):
    response = await client.get("/api/services")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_service_stats(client):
    response = await client.get("/api/services/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "online" in data
    assert "avg_response_time_ms" in data


@pytest.mark.asyncio
async def test_create_and_delete_service(client):
    # Create
    response = await client.post("/api/services", json={
        "name": "Test Service",
        "url": "https://httpbin.org/status/200",
        "check_type": "http",
    })
    assert response.status_code == 201
    service = response.json()
    assert service["name"] == "Test Service"
    service_id = service["id"]

    # Get
    response = await client.get(f"/api/services/{service_id}")
    assert response.status_code == 200

    # Delete
    response = await client.delete(f"/api/services/{service_id}")
    assert response.status_code == 200

    # Verify deleted
    response = await client.get(f"/api/services/{service_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_service_not_found(client):
    response = await client.get("/api/services/99999")
    assert response.status_code == 404
