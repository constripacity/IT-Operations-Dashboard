"""Tests for the network tools API."""

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
async def test_dns_lookup(client):
    response = await client.post("/api/network/dns", json={
        "domain": "google.com",
        "record_type": "A",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "google.com"
    assert "records" in data or "error" in data


@pytest.mark.asyncio
async def test_dns_lookup_invalid(client):
    response = await client.post("/api/network/dns", json={
        "domain": "this-domain-does-not-exist-12345.xyz",
        "record_type": "A",
    })
    assert response.status_code == 200
    data = response.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_geoip_lookup(client):
    response = await client.post("/api/network/geoip", json={
        "ip": "8.8.8.8",
    })
    assert response.status_code == 200
    data = response.json()
    assert "country" in data or "error" in data


@pytest.mark.asyncio
async def test_reverse_dns(client):
    response = await client.post("/api/network/reverse-dns", json={
        "ip": "8.8.8.8",
    })
    assert response.status_code == 200
    data = response.json()
    assert "hostnames" in data or "error" in data


@pytest.mark.asyncio
async def test_portscan(client):
    response = await client.post("/api/network/portscan", json={
        "host": "google.com",
        "ports": [80, 443],
    })
    assert response.status_code == 200
    data = response.json()
    assert "ports" in data
    assert data["host"] == "google.com"
