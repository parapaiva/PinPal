"""Integration tests for the import API endpoint."""

import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


# ---- Helpers ----


async def _create_user(client: AsyncClient) -> dict:  # type: ignore[type-arg]
    resp = await client.post(
        "/api/v1/users",
        json={"email": f"{uuid.uuid4().hex[:8]}@test.com", "display_name": "Test User"},
    )
    assert resp.status_code == 201
    return resp.json()


# ---- WhatsApp ----


class TestWhatsAppImport:
    async def test_import_group_with_participants(self, client: AsyncClient) -> None:
        user = await _create_user(client)
        user_id = user["id"]

        resp = await client.post(
            f"/api/v1/users/{user_id}/imports",
            json={
                "source_type": "whatsapp",
                "payload": {
                    "group_name": "Family Chat",
                    "participants": [
                        {"display_name": "Alice", "phone_number": "+1111"},
                        {"display_name": "Bob", "phone_number": "+2222"},
                        {"display_name": "Charlie", "handle": "@charlie"},
                    ],
                },
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source_type"] == "whatsapp"
        assert data["duplicate"] is False
        assert data["events_produced"] == 10  # 1 group + 3x3 per-participant

        entities = data["entities_created"]
        assert entities["groups"] == 1
        assert entities["persons"] == 3
        assert entities["identities"] == 3
        assert entities["memberships"] == 3
        assert entities["facts"] == 3
        assert entities["timeline_events"] >= 3

        # Verify entities exist via GET endpoints
        groups_resp = await client.get(f"/api/v1/users/{user_id}/groups")
        assert groups_resp.status_code == 200
        groups = groups_resp.json()
        assert len(groups) == 1
        assert groups[0]["name"] == "Family Chat"

        persons_resp = await client.get(f"/api/v1/users/{user_id}/persons")
        assert persons_resp.status_code == 200
        assert len(persons_resp.json()) == 3

    async def test_duplicate_detection(self, client: AsyncClient) -> None:
        user = await _create_user(client)
        user_id = user["id"]
        payload = {
            "source_type": "whatsapp",
            "payload": {
                "group_name": "Dup Group",
                "participants": [{"display_name": "Alice"}],
            },
        }

        resp1 = await client.post(f"/api/v1/users/{user_id}/imports", json=payload)
        assert resp1.status_code == 201
        assert resp1.json()["duplicate"] is False

        resp2 = await client.post(f"/api/v1/users/{user_id}/imports", json=payload)
        assert resp2.status_code == 201
        data2 = resp2.json()
        assert data2["duplicate"] is True
        assert data2["events_produced"] == 0

    async def test_missing_group_name(self, client: AsyncClient) -> None:
        user = await _create_user(client)
        resp = await client.post(
            f"/api/v1/users/{user['id']}/imports",
            json={
                "source_type": "whatsapp",
                "payload": {"participants": [{"display_name": "Alice"}]},
            },
        )
        assert resp.status_code == 422

    async def test_empty_participants(self, client: AsyncClient) -> None:
        user = await _create_user(client)
        resp = await client.post(
            f"/api/v1/users/{user['id']}/imports",
            json={
                "source_type": "whatsapp",
                "payload": {"group_name": "Empty", "participants": []},
            },
        )
        assert resp.status_code == 422


# ---- Instagram ----


class TestInstagramImport:
    async def test_import_follows(self, client: AsyncClient) -> None:
        user = await _create_user(client)
        user_id = user["id"]

        resp = await client.post(
            f"/api/v1/users/{user_id}/imports",
            json={
                "source_type": "instagram",
                "payload": {
                    "follows": [
                        {"username": "alice_ig", "display_name": "Alice"},
                        {"username": "bob_ig"},
                    ],
                },
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["events_produced"] == 4  # 2 follows x 2 events
        entities = data["entities_created"]
        assert entities["persons"] == 2
        assert entities["identities"] == 2
        assert entities["facts"] == 2

    async def test_duplicate_detection(self, client: AsyncClient) -> None:
        user = await _create_user(client)
        user_id = user["id"]
        payload = {
            "source_type": "instagram",
            "payload": {"follows": [{"username": "alice_ig"}]},
        }

        resp1 = await client.post(f"/api/v1/users/{user_id}/imports", json=payload)
        assert resp1.status_code == 201

        resp2 = await client.post(f"/api/v1/users/{user_id}/imports", json=payload)
        assert resp2.status_code == 201
        assert resp2.json()["duplicate"] is True

    async def test_invalid_payload(self, client: AsyncClient) -> None:
        user = await _create_user(client)
        resp = await client.post(
            f"/api/v1/users/{user['id']}/imports",
            json={
                "source_type": "instagram",
                "payload": {"follows": []},
            },
        )
        assert resp.status_code == 422


# ---- Manual ----


class TestManualImport:
    async def test_creates_observation_and_fact(self, client: AsyncClient) -> None:
        user = await _create_user(client)
        user_id = user["id"]

        resp = await client.post(
            f"/api/v1/users/{user_id}/imports",
            json={
                "source_type": "manual",
                "payload": {
                    "person_display_name": "Dave",
                    "body": "Met at PyCon 2025",
                },
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["events_produced"] == 2
        entities = data["entities_created"]
        assert entities["observations"] == 1
        assert entities["facts"] == 1
        assert entities["persons"] == 1

    async def test_links_to_existing_person(self, client: AsyncClient) -> None:
        user = await _create_user(client)
        user_id = user["id"]

        # Create person first
        person_resp = await client.post(
            f"/api/v1/users/{user_id}/persons",
            json={"display_name": "Existing Person"},
        )
        person_id = person_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/users/{user_id}/imports",
            json={
                "source_type": "manual",
                "payload": {
                    "person_display_name": "Existing Person",
                    "person_id": person_id,
                    "body": "Additional note",
                },
            },
        )
        assert resp.status_code == 201
        entities = resp.json()["entities_created"]
        # Should not create a new person since person_id was provided
        assert entities["persons"] == 0

    async def test_creates_new_person_without_id(self, client: AsyncClient) -> None:
        user = await _create_user(client)
        user_id = user["id"]

        resp = await client.post(
            f"/api/v1/users/{user_id}/imports",
            json={
                "source_type": "manual",
                "payload": {
                    "person_display_name": "New Person",
                    "body": "First observation",
                },
            },
        )
        assert resp.status_code == 201
        entities = resp.json()["entities_created"]
        assert entities["persons"] == 1

    async def test_visibility_always_private(self, client: AsyncClient) -> None:
        user = await _create_user(client)
        resp = await client.post(
            f"/api/v1/users/{user['id']}/imports",
            json={
                "source_type": "manual",
                "payload": {
                    "person_display_name": "Someone",
                    "body": "A note",
                    "visibility": "friends",
                },
            },
        )
        assert resp.status_code == 201
        # Fact should be created with PRIVATE visibility regardless


# ---- Error cases ----


class TestImportErrors:
    async def test_user_not_found(self, client: AsyncClient) -> None:
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/api/v1/users/{fake_id}/imports",
            json={
                "source_type": "whatsapp",
                "payload": {
                    "group_name": "Test",
                    "participants": [{"display_name": "Alice"}],
                },
            },
        )
        assert resp.status_code == 404

    async def test_unsupported_source_type(self, client: AsyncClient) -> None:
        user = await _create_user(client)
        resp = await client.post(
            f"/api/v1/users/{user['id']}/imports",
            json={
                "source_type": "linkedin",
                "payload": {},
            },
        )
        assert resp.status_code == 422
