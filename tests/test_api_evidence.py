"""Integration tests for Evidence API endpoints (MongoDB)."""

import uuid

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
        json={"display_name": "Bob"},
    )
    assert resp.status_code == 201
    return uuid.UUID(resp.json()["id"])


class TestRawPayloads:
    async def test_store_and_get(self, client: AsyncClient, user_id: uuid.UUID) -> None:
        resp = await client.post(
            f"/api/v1/users/{user_id}/evidence/raw-payloads",
            json={
                "owner_user_id": str(user_id),
                "source_type": "whatsapp",
                "payload": {"messages": [{"text": "hello"}]},
                "content_hash": "sha256:abc123",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source_type"] == "whatsapp"
        payload_id = data["id"]

        get_resp = await client.get(f"/api/v1/users/{user_id}/evidence/raw-payloads/{payload_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["content_hash"] == "sha256:abc123"

    async def test_list_payloads(self, client: AsyncClient, user_id: uuid.UUID) -> None:
        for i in range(3):
            await client.post(
                f"/api/v1/users/{user_id}/evidence/raw-payloads",
                json={
                    "owner_user_id": str(user_id),
                    "source_type": "whatsapp",
                    "payload": {"batch": i},
                    "content_hash": f"sha256:hash{i}",
                },
            )
        resp = await client.get(f"/api/v1/users/{user_id}/evidence/raw-payloads")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    async def test_get_not_found(self, client: AsyncClient, user_id: uuid.UUID) -> None:
        resp = await client.get(
            f"/api/v1/users/{user_id}/evidence/raw-payloads/60d5f8a0b1e2c3f4a5b6c7d8"
        )
        assert resp.status_code == 404


class TestObservations:
    async def test_store_and_get(
        self, client: AsyncClient, user_id: uuid.UUID, person_id: uuid.UUID
    ) -> None:
        resp = await client.post(
            f"/api/v1/users/{user_id}/evidence/observations",
            json={
                "owner_user_id": str(user_id),
                "source_type": "manual",
                "subject_person_id": str(person_id),
                "body": "Met at PyCon 2026",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["body"] == "Met at PyCon 2026"
        obs_id = data["id"]

        get_resp = await client.get(f"/api/v1/users/{user_id}/evidence/observations/{obs_id}")
        assert get_resp.status_code == 200

    async def test_list_with_person_filter(
        self, client: AsyncClient, user_id: uuid.UUID, person_id: uuid.UUID
    ) -> None:
        await client.post(
            f"/api/v1/users/{user_id}/evidence/observations",
            json={
                "owner_user_id": str(user_id),
                "source_type": "manual",
                "subject_person_id": str(person_id),
                "body": "Note 1",
            },
        )
        await client.post(
            f"/api/v1/users/{user_id}/evidence/observations",
            json={
                "owner_user_id": str(user_id),
                "source_type": "manual",
                "body": "Unrelated note",
            },
        )
        resp = await client.get(
            f"/api/v1/users/{user_id}/evidence/observations",
            params={"person_id": str(person_id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["subject_person_id"] == str(person_id)


class TestEvidenceBundles:
    async def test_create_and_get(
        self, client: AsyncClient, user_id: uuid.UUID, person_id: uuid.UUID
    ) -> None:
        resp = await client.post(
            f"/api/v1/users/{user_id}/evidence/bundles",
            json={
                "owner_user_id": str(user_id),
                "person_id": str(person_id),
                "summary": "Known from WhatsApp group + LinkedIn",
                "evidence_ids": ["e1", "e2"],
                "fact_ids": ["f1"],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["summary"] == "Known from WhatsApp group + LinkedIn"
        bundle_id = data["id"]

        get_resp = await client.get(f"/api/v1/users/{user_id}/evidence/bundles/{bundle_id}")
        assert get_resp.status_code == 200

    async def test_list_bundles(
        self, client: AsyncClient, user_id: uuid.UUID, person_id: uuid.UUID
    ) -> None:
        await client.post(
            f"/api/v1/users/{user_id}/evidence/bundles",
            json={
                "owner_user_id": str(user_id),
                "person_id": str(person_id),
                "summary": "Bundle 1",
            },
        )
        resp = await client.get(
            f"/api/v1/users/{user_id}/evidence/bundles",
            params={"person_id": str(person_id)},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
