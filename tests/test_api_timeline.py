"""Integration tests for Timeline API endpoints (MongoDB)."""

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


class TestTimeline:
    async def test_record_and_list(self, client: AsyncClient, user_id: uuid.UUID) -> None:
        now = datetime.now(UTC).isoformat()
        resp = await client.post(
            f"/api/v1/users/{user_id}/timeline",
            json={
                "owner_user_id": str(user_id),
                "event_type": "fact_recorded",
                "summary": "New fact recorded about Alice",
                "occurred_at": now,
                "refs": {"person_id": str(uuid.uuid4())},
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["event_type"] == "fact_recorded"

        list_resp = await client.get(f"/api/v1/users/{user_id}/timeline")
        assert list_resp.status_code == 200
        events = list_resp.json()
        assert len(events) == 1

    async def test_filter_by_event_type(self, client: AsyncClient, user_id: uuid.UUID) -> None:
        now = datetime.now(UTC).isoformat()
        await client.post(
            f"/api/v1/users/{user_id}/timeline",
            json={
                "owner_user_id": str(user_id),
                "event_type": "fact_recorded",
                "summary": "Fact",
                "occurred_at": now,
            },
        )
        await client.post(
            f"/api/v1/users/{user_id}/timeline",
            json={
                "owner_user_id": str(user_id),
                "event_type": "evidence_added",
                "summary": "Evidence",
                "occurred_at": now,
            },
        )
        resp = await client.get(
            f"/api/v1/users/{user_id}/timeline",
            params={"event_type": "fact_recorded"},
        )
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) == 1
        assert events[0]["event_type"] == "fact_recorded"

    async def test_list_empty(self, client: AsyncClient, user_id: uuid.UUID) -> None:
        resp = await client.get(f"/api/v1/users/{user_id}/timeline")
        assert resp.status_code == 200
        assert resp.json() == []
