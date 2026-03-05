"""Integration tests for Relationship CRUD + /why endpoint."""

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
async def test_create_relationship(client: AsyncClient) -> None:
    uid = await _create_user(client)
    pid_a = await _create_person(client, uid, "Alice")
    pid_b = await _create_person(client, uid, "Bob")
    resp = await client.post(
        f"/api/v1/users/{uid}/relationships",
        json={
            "person_a_id": pid_a,
            "person_b_id": pid_b,
            "relationship_type": "manual",
            "confidence": 0.9,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["relationship_type"] == "manual"
    assert body["confidence"] == 0.9
    assert body["status"] == "suggested"
    # Verify ordering: a < b
    assert body["person_a_id"] < body["person_b_id"]


@pytest.mark.integration
async def test_list_relationships(client: AsyncClient) -> None:
    uid = await _create_user(client)
    pid_a = await _create_person(client, uid, "A")
    pid_b = await _create_person(client, uid, "B")
    pid_c = await _create_person(client, uid, "C")
    await client.post(
        f"/api/v1/users/{uid}/relationships",
        json={"person_a_id": pid_a, "person_b_id": pid_b, "relationship_type": "manual"},
    )
    await client.post(
        f"/api/v1/users/{uid}/relationships",
        json={"person_a_id": pid_b, "person_b_id": pid_c, "relationship_type": "follow"},
    )
    resp = await client.get(f"/api/v1/users/{uid}/relationships")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.integration
async def test_update_relationship(client: AsyncClient) -> None:
    uid = await _create_user(client)
    pid_a = await _create_person(client, uid, "A")
    pid_b = await _create_person(client, uid, "B")
    create = await client.post(
        f"/api/v1/users/{uid}/relationships",
        json={"person_a_id": pid_a, "person_b_id": pid_b, "relationship_type": "manual"},
    )
    rid = create.json()["id"]
    resp = await client.patch(
        f"/api/v1/users/{uid}/relationships/{rid}",
        json={"status": "confirmed", "confidence": 1.0},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"
    assert resp.json()["confidence"] == 1.0


@pytest.mark.integration
async def test_create_relationship_person_not_found(client: AsyncClient) -> None:
    uid = await _create_user(client)
    pid = await _create_person(client, uid, "A")
    resp = await client.post(
        f"/api/v1/users/{uid}/relationships",
        json={
            "person_a_id": pid,
            "person_b_id": str(uuid.uuid4()),
            "relationship_type": "manual",
        },
    )
    assert resp.status_code == 404


# ---- Why endpoint ----


@pytest.mark.integration
async def test_why_endpoint_full_scenario(client: AsyncClient) -> None:
    """Full scenario: group membership + relationship + identity → why reasons."""
    uid = await _create_user(client)
    pid = await _create_person(client, uid, "Alice")
    pid2 = await _create_person(client, uid, "Bob")

    # Add group + membership
    g = await client.post(
        f"/api/v1/users/{uid}/groups",
        json={"group_type": "whatsapp_group", "name": "College Friends"},
    )
    gid = g.json()["id"]
    await client.post(
        f"/api/v1/users/{uid}/groups/{gid}/members",
        json={"person_id": pid},
    )

    # Add relationship
    await client.post(
        f"/api/v1/users/{uid}/relationships",
        json={
            "person_a_id": pid,
            "person_b_id": pid2,
            "relationship_type": "co_member",
            "confidence": 0.8,
        },
    )

    # Add identity
    await client.post(
        f"/api/v1/users/{uid}/persons/{pid}/identities",
        json={"source_type": "whatsapp", "handle": "+1234"},
    )

    # Query why
    resp = await client.get(f"/api/v1/users/{uid}/persons/{pid}/why")
    assert resp.status_code == 200
    body = resp.json()
    assert body["person_id"] == pid
    assert body["display_name"] == "Alice"
    assert len(body["reasons"]) == 3
    reason_types = {r["reason_type"] for r in body["reasons"]}
    assert reason_types == {"shared_group", "direct_relationship", "identity_source"}


@pytest.mark.integration
async def test_why_endpoint_unknown_person(client: AsyncClient) -> None:
    uid = await _create_user(client)
    resp = await client.get(f"/api/v1/users/{uid}/persons/{uuid.uuid4()}/why")
    assert resp.status_code == 200
    assert resp.json()["reasons"] == []
