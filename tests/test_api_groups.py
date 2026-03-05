"""Integration tests for Group + Membership CRUD API endpoints."""

import uuid

import pytest
from httpx import AsyncClient


async def _create_user(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/users",
        json={"email": f"{uuid.uuid4().hex[:8]}@test.com", "display_name": "Owner"},
    )
    return resp.json()["id"]


async def _create_person(client: AsyncClient, user_id: str, name: str = "P") -> str:
    resp = await client.post(f"/api/v1/users/{user_id}/persons", json={"display_name": name})
    return resp.json()["id"]


@pytest.mark.integration
async def test_create_group(client: AsyncClient) -> None:
    uid = await _create_user(client)
    resp = await client.post(
        f"/api/v1/users/{uid}/groups",
        json={"group_type": "custom", "name": "My Group"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "My Group"
    assert resp.json()["group_type"] == "custom"
    assert resp.json()["visibility"] == "private"


@pytest.mark.integration
async def test_list_groups(client: AsyncClient) -> None:
    uid = await _create_user(client)
    await client.post(
        f"/api/v1/users/{uid}/groups",
        json={"group_type": "custom", "name": "G1"},
    )
    await client.post(
        f"/api/v1/users/{uid}/groups",
        json={"group_type": "event", "name": "G2"},
    )
    resp = await client.get(f"/api/v1/users/{uid}/groups")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.integration
async def test_get_group(client: AsyncClient) -> None:
    uid = await _create_user(client)
    create = await client.post(
        f"/api/v1/users/{uid}/groups",
        json={"group_type": "cohort", "name": "Class of 2020"},
    )
    gid = create.json()["id"]
    resp = await client.get(f"/api/v1/users/{uid}/groups/{gid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Class of 2020"


@pytest.mark.integration
async def test_update_group(client: AsyncClient) -> None:
    uid = await _create_user(client)
    create = await client.post(
        f"/api/v1/users/{uid}/groups",
        json={"group_type": "custom", "name": "Old Name"},
    )
    gid = create.json()["id"]
    resp = await client.patch(
        f"/api/v1/users/{uid}/groups/{gid}",
        json={"name": "New Name", "visibility": "friends"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
    assert resp.json()["visibility"] == "friends"


@pytest.mark.integration
async def test_delete_group(client: AsyncClient) -> None:
    uid = await _create_user(client)
    create = await client.post(
        f"/api/v1/users/{uid}/groups",
        json={"group_type": "custom", "name": "Temp"},
    )
    gid = create.json()["id"]
    resp = await client.delete(f"/api/v1/users/{uid}/groups/{gid}")
    assert resp.status_code == 204


@pytest.mark.integration
async def test_get_group_wrong_user(client: AsyncClient) -> None:
    uid1 = await _create_user(client)
    uid2 = await _create_user(client)
    create = await client.post(
        f"/api/v1/users/{uid1}/groups",
        json={"group_type": "custom", "name": "Private"},
    )
    gid = create.json()["id"]
    resp = await client.get(f"/api/v1/users/{uid2}/groups/{gid}")
    assert resp.status_code == 404


# ---- Membership sub-resource ----


@pytest.mark.integration
async def test_add_member(client: AsyncClient) -> None:
    uid = await _create_user(client)
    pid = await _create_person(client, uid, "Alice")
    g = await client.post(
        f"/api/v1/users/{uid}/groups",
        json={"group_type": "custom", "name": "G"},
    )
    gid = g.json()["id"]
    resp = await client.post(
        f"/api/v1/users/{uid}/groups/{gid}/members",
        json={"person_id": pid},
    )
    assert resp.status_code == 201
    assert resp.json()["person_id"] == pid
    assert resp.json()["group_id"] == gid


@pytest.mark.integration
async def test_list_members(client: AsyncClient) -> None:
    uid = await _create_user(client)
    pid1 = await _create_person(client, uid, "A")
    pid2 = await _create_person(client, uid, "B")
    g = await client.post(
        f"/api/v1/users/{uid}/groups",
        json={"group_type": "custom", "name": "G"},
    )
    gid = g.json()["id"]
    await client.post(f"/api/v1/users/{uid}/groups/{gid}/members", json={"person_id": pid1})
    await client.post(f"/api/v1/users/{uid}/groups/{gid}/members", json={"person_id": pid2})
    resp = await client.get(f"/api/v1/users/{uid}/groups/{gid}/members")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.integration
async def test_remove_member(client: AsyncClient) -> None:
    uid = await _create_user(client)
    pid = await _create_person(client, uid, "C")
    g = await client.post(
        f"/api/v1/users/{uid}/groups",
        json={"group_type": "custom", "name": "G"},
    )
    gid = g.json()["id"]
    m = await client.post(f"/api/v1/users/{uid}/groups/{gid}/members", json={"person_id": pid})
    mid = m.json()["id"]
    resp = await client.delete(f"/api/v1/users/{uid}/groups/{gid}/members/{mid}")
    assert resp.status_code == 204
