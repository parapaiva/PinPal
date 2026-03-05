"""Integration tests for Person + Identity CRUD API endpoints."""

import uuid

import pytest
from httpx import AsyncClient


async def _create_user(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/users",
        json={"email": f"{uuid.uuid4().hex[:8]}@test.com", "display_name": "Owner"},
    )
    return resp.json()["id"]


@pytest.mark.integration
async def test_create_person(client: AsyncClient) -> None:
    uid = await _create_user(client)
    resp = await client.post(
        f"/api/v1/users/{uid}/persons",
        json={"display_name": "Alice"},
    )
    assert resp.status_code == 201
    assert resp.json()["display_name"] == "Alice"
    assert resp.json()["owner_user_id"] == uid


@pytest.mark.integration
async def test_list_persons(client: AsyncClient) -> None:
    uid = await _create_user(client)
    await client.post(f"/api/v1/users/{uid}/persons", json={"display_name": "A"})
    await client.post(f"/api/v1/users/{uid}/persons", json={"display_name": "B"})
    resp = await client.get(f"/api/v1/users/{uid}/persons")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.integration
async def test_get_person(client: AsyncClient) -> None:
    uid = await _create_user(client)
    create = await client.post(f"/api/v1/users/{uid}/persons", json={"display_name": "Bob"})
    pid = create.json()["id"]
    resp = await client.get(f"/api/v1/users/{uid}/persons/{pid}")
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Bob"


@pytest.mark.integration
async def test_get_person_wrong_user(client: AsyncClient) -> None:
    uid1 = await _create_user(client)
    uid2 = await _create_user(client)
    create = await client.post(f"/api/v1/users/{uid1}/persons", json={"display_name": "Carol"})
    pid = create.json()["id"]
    resp = await client.get(f"/api/v1/users/{uid2}/persons/{pid}")
    assert resp.status_code == 404


@pytest.mark.integration
async def test_update_person(client: AsyncClient) -> None:
    uid = await _create_user(client)
    create = await client.post(f"/api/v1/users/{uid}/persons", json={"display_name": "Dave"})
    pid = create.json()["id"]
    resp = await client.patch(
        f"/api/v1/users/{uid}/persons/{pid}",
        json={"display_name": "David"},
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "David"


@pytest.mark.integration
async def test_delete_person(client: AsyncClient) -> None:
    uid = await _create_user(client)
    create = await client.post(f"/api/v1/users/{uid}/persons", json={"display_name": "Eve"})
    pid = create.json()["id"]
    resp = await client.delete(f"/api/v1/users/{uid}/persons/{pid}")
    assert resp.status_code == 204


# ---- Identity sub-resource ----


@pytest.mark.integration
async def test_add_identity(client: AsyncClient) -> None:
    uid = await _create_user(client)
    p = await client.post(f"/api/v1/users/{uid}/persons", json={"display_name": "F"})
    pid = p.json()["id"]
    resp = await client.post(
        f"/api/v1/users/{uid}/persons/{pid}/identities",
        json={"source_type": "whatsapp", "handle": "+1234567890"},
    )
    assert resp.status_code == 201
    assert resp.json()["source_type"] == "whatsapp"
    assert resp.json()["handle"] == "+1234567890"


@pytest.mark.integration
async def test_list_identities(client: AsyncClient) -> None:
    uid = await _create_user(client)
    p = await client.post(f"/api/v1/users/{uid}/persons", json={"display_name": "G"})
    pid = p.json()["id"]
    await client.post(
        f"/api/v1/users/{uid}/persons/{pid}/identities",
        json={"source_type": "whatsapp"},
    )
    await client.post(
        f"/api/v1/users/{uid}/persons/{pid}/identities",
        json={"source_type": "instagram", "handle": "@g"},
    )
    resp = await client.get(f"/api/v1/users/{uid}/persons/{pid}/identities")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.integration
async def test_delete_identity(client: AsyncClient) -> None:
    uid = await _create_user(client)
    p = await client.post(f"/api/v1/users/{uid}/persons", json={"display_name": "H"})
    pid = p.json()["id"]
    iid_resp = await client.post(
        f"/api/v1/users/{uid}/persons/{pid}/identities",
        json={"source_type": "linkedin"},
    )
    iid = iid_resp.json()["id"]
    resp = await client.delete(f"/api/v1/users/{uid}/persons/{pid}/identities/{iid}")
    assert resp.status_code == 204
