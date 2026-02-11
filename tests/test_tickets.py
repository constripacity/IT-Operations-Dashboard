"""Tests for the ticket management API."""

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
async def test_list_tickets(client):
    response = await client.get("/api/tickets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_ticket_stats(client):
    response = await client.get("/api/tickets/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "open" in data
    assert "by_priority" in data


@pytest.mark.asyncio
async def test_create_update_delete_ticket(client):
    # Create
    response = await client.post("/api/tickets", json={
        "title": "Test Ticket",
        "description": "This is a test ticket",
        "priority": "high",
        "category": "software",
    })
    assert response.status_code == 201
    ticket = response.json()
    assert ticket["title"] == "Test Ticket"
    assert ticket["status"] == "open"
    ticket_id = ticket["id"]

    # Update status to resolved
    response = await client.put(f"/api/tickets/{ticket_id}", json={
        "status": "resolved",
    })
    assert response.status_code == 200
    updated = response.json()
    assert updated["status"] == "resolved"
    assert updated["resolved_at"] is not None

    # Delete
    response = await client.delete(f"/api/tickets/{ticket_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ticket_filters(client):
    response = await client.get("/api/tickets?status=open&priority=high")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ticket_not_found(client):
    response = await client.get("/api/tickets/99999")
    assert response.status_code == 404
