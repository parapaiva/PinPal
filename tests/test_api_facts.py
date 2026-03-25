"""Integration tests for Fact API endpoints."""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


@pytest.fixture
async def user_id(client: AsyncClient) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/users",
        json={"email": f"{uuid.uuid4().hex[:8]}@test.com", "display_name": "Test User"},
    )
    assert resp.status_code == 201
    return uuid.UUID(resp.json()["id"])


@pytest.fixture
async def person_id(client: AsyncClient, user_id: uuid.UUID) -> uuid.UUID:
    resp = await client.post(
        f"/api/v1/users/{user_id}/persons",
        json={"display_name": "Alice"},
    )
    assert resp.status_code == 201
    return uuid.UUID(resp.json()["id"])


class TestFactCRUD:
    async def test_create_fact(
        self, client: AsyncClient, user_id: uuid.UUID, person_id: uuid.UUID
    ) -> None:
        resp = await client.post(
            f"/api/v1/users/{user_id}/facts",
            json={
                "fact_type": "manual_note",
                "source_type": "manual",
                "payload": {"note": "Met at PyCon"},
                "observed_at": datetime.now(UTC).isoformat(),
                "person_id": str(person_id),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["fact_type"] == "manual_note"
        assert data["status"] == "active"
        assert data["person_id"] == str(person_id)

    async def test_list_facts(
        self, client: AsyncClient, user_id: uuid.UUID, person_id: uuid.UUID
    ) -> None:
        # Create two facts
        for ft in ("manual_note", "follow_observed"):
            await client.post(
                f"/api/v1/users/{user_id}/facts",
                json={
                    "fact_type": ft,
                    "source_type": "manual",
                    "payload": {},
                    "observed_at": datetime.now(UTC).isoformat(),
                    "person_id": str(person_id),
                },
            )
        resp = await client.get(f"/api/v1/users/{user_id}/facts")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_list_facts_filter_by_type(
        self, client: AsyncClient, user_id: uuid.UUID, person_id: uuid.UUID
    ) -> None:
        await client.post(
            f"/api/v1/users/{user_id}/facts",
            json={
                "fact_type": "manual_note",
                "source_type": "manual",
                "payload": {},
                "observed_at": datetime.now(UTC).isoformat(),
            },
        )
        await client.post(
            f"/api/v1/users/{user_id}/facts",
            json={
                "fact_type": "follow_observed",
                "source_type": "instagram",
                "payload": {},
                "observed_at": datetime.now(UTC).isoformat(),
            },
        )
        resp = await client.get(
            f"/api/v1/users/{user_id}/facts", params={"fact_type": "manual_note"}
        )
        assert resp.status_code == 200
        facts = resp.json()
        assert len(facts) == 1
        assert facts[0]["fact_type"] == "manual_note"

    async def test_get_fact(self, client: AsyncClient, user_id: uuid.UUID) -> None:
        create_resp = await client.post(
            f"/api/v1/users/{user_id}/facts",
            json={
                "fact_type": "manual_note",
                "source_type": "manual",
                "payload": {"key": "value"},
                "observed_at": datetime.now(UTC).isoformat(),
            },
        )
        fact_id = create_resp.json()["id"]
        resp = await client.get(f"/api/v1/users/{user_id}/facts/{fact_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == fact_id

    async def test_get_fact_not_found(self, client: AsyncClient, user_id: uuid.UUID) -> None:
        resp = await client.get(f"/api/v1/users/{user_id}/facts/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_retract_fact(self, client: AsyncClient, user_id: uuid.UUID) -> None:
        create_resp = await client.post(
            f"/api/v1/users/{user_id}/facts",
            json={
                "fact_type": "manual_note",
                "source_type": "manual",
                "payload": {},
                "observed_at": datetime.now(UTC).isoformat(),
            },
        )
        fact_id = create_resp.json()["id"]
        resp = await client.post(f"/api/v1/users/{user_id}/facts/{fact_id}/retract")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "retracted"
        assert data["retracted_at"] is not None

    async def test_retract_already_retracted(
        self, client: AsyncClient, user_id: uuid.UUID
    ) -> None:
        create_resp = await client.post(
            f"/api/v1/users/{user_id}/facts",
            json={
                "fact_type": "manual_note",
                "source_type": "manual",
                "payload": {},
                "observed_at": datetime.now(UTC).isoformat(),
            },
        )
        fact_id = create_resp.json()["id"]
        await client.post(f"/api/v1/users/{user_id}/facts/{fact_id}/retract")
        resp = await client.post(f"/api/v1/users/{user_id}/facts/{fact_id}/retract")
        assert resp.status_code == 409

    async def test_update_fact(self, client: AsyncClient, user_id: uuid.UUID) -> None:
        create_resp = await client.post(
            f"/api/v1/users/{user_id}/facts",
            json={
                "fact_type": "manual_note",
                "source_type": "manual",
                "payload": {},
                "observed_at": datetime.now(UTC).isoformat(),
            },
        )
        fact_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/users/{user_id}/facts/{fact_id}",
            json={"visibility": "friends"},
        )
        assert resp.status_code == 200
        assert resp.json()["visibility"] == "friends"

    async def test_user_not_found(self, client: AsyncClient) -> None:
        resp = await client.get(f"/api/v1/users/{uuid.uuid4()}/facts")
        assert resp.status_code == 404
