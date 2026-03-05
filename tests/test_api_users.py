"""Integration tests for User CRUD API endpoints."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_create_user(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/users",
        json={"email": "alice@example.com", "display_name": "Alice"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["display_name"] == "Alice"
    assert "id" in body
    assert "created_at" in body


@pytest.mark.integration
async def test_get_user(client: AsyncClient) -> None:
    create = await client.post(
        "/api/v1/users",
        json={"email": "bob@example.com", "display_name": "Bob"},
    )
    user_id = create.json()["id"]
    resp = await client.get(f"/api/v1/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Bob"


@pytest.mark.integration
async def test_get_user_not_found(client: AsyncClient) -> None:
    resp = await client.get(f"/api/v1/users/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.integration
async def test_update_user(client: AsyncClient) -> None:
    create = await client.post(
        "/api/v1/users",
        json={"email": "carol@example.com", "display_name": "Carol"},
    )
    user_id = create.json()["id"]
    resp = await client.patch(
        f"/api/v1/users/{user_id}",
        json={"display_name": "Carolina"},
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Carolina"
    assert resp.json()["email"] == "carol@example.com"


@pytest.mark.integration
async def test_delete_user(client: AsyncClient) -> None:
    create = await client.post(
        "/api/v1/users",
        json={"email": "dave@example.com", "display_name": "Dave"},
    )
    user_id = create.json()["id"]
    resp = await client.delete(f"/api/v1/users/{user_id}")
    assert resp.status_code == 204
    get = await client.get(f"/api/v1/users/{user_id}")
    assert get.status_code == 404


@pytest.mark.integration
async def test_create_user_duplicate_email(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/users",
        json={"email": "dup@example.com", "display_name": "Dup1"},
    )
    resp = await client.post(
        "/api/v1/users",
        json={"email": "dup@example.com", "display_name": "Dup2"},
    )
    assert resp.status_code == 409
