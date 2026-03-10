"""Unit tests for MongoDB repository classes (mocked Motor)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from pinpal.db.enums import SourceType, TimelineEventType, Visibility
from pinpal.mongo.repositories import (
    EvidenceBundleRepo,
    ObservationRepo,
    RawPayloadRepo,
    TimelineEventRepo,
)
from pinpal.mongo.schemas import (
    EvidenceBundleCreate,
    ObservationCreate,
    RawPayloadCreate,
    TimelineEventCreate,
    TimelineEventRefsCreate,
)


def _mock_db(collection_docs: list[dict[str, Any]] | None = None) -> MagicMock:
    """Create a mock Motor database with a mock collection."""
    db = MagicMock()
    coll = MagicMock()

    # insert_one returns an object with inserted_id
    inserted_id = ObjectId()
    insert_result = MagicMock()
    insert_result.inserted_id = inserted_id
    coll.insert_one = AsyncMock(return_value=insert_result)

    # find_one
    coll.find_one = AsyncMock(return_value=None)

    # find returns an async iterable cursor
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)

    docs = collection_docs or []

    async def _aiter(_self: Any) -> Any:
        for doc in docs:
            yield doc

    cursor.__aiter__ = _aiter
    coll.find = MagicMock(return_value=cursor)

    db.__getitem__ = MagicMock(return_value=coll)
    db._coll = coll
    db._inserted_id = inserted_id
    return db


class TestRawPayloadRepo:
    @pytest.mark.asyncio
    async def test_insert(self) -> None:
        db = _mock_db()
        repo = RawPayloadRepo(db)
        data = RawPayloadCreate(
            owner_user_id="user1",
            source_type=SourceType.WHATSAPP,
            payload={"test": True},
            content_hash="sha256:abc",
        )
        result = await repo.insert(data)
        assert result.owner_user_id == "user1"
        assert result.source_type == SourceType.WHATSAPP
        assert result.id == str(db._inserted_id)
        db._coll.insert_one.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_not_found(self) -> None:
        db = _mock_db()
        repo = RawPayloadRepo(db)
        result = await repo.get(str(ObjectId()))
        assert result is None

    @pytest.mark.asyncio
    async def test_get_found(self) -> None:
        db = _mock_db()
        oid = ObjectId()
        now = datetime.now(UTC)
        db._coll.find_one = AsyncMock(return_value={
            "_id": oid,
            "owner_user_id": "u1",
            "source_type": "whatsapp",
            "payload": {"data": 1},
            "content_hash": "h1",
            "created_at": now,
        })
        repo = RawPayloadRepo(db)
        result = await repo.get(str(oid))
        assert result is not None
        assert result.id == str(oid)

    @pytest.mark.asyncio
    async def test_list_for_user(self) -> None:
        oid = ObjectId()
        now = datetime.now(UTC)
        docs = [{
            "_id": oid,
            "owner_user_id": "u1",
            "source_type": "whatsapp",
            "payload": {},
            "content_hash": "h",
            "created_at": now,
        }]
        db = _mock_db(collection_docs=docs)
        repo = RawPayloadRepo(db)
        results = await repo.list_for_user("u1")
        assert len(results) == 1
        assert results[0].id == str(oid)


class TestObservationRepo:
    @pytest.mark.asyncio
    async def test_insert(self) -> None:
        db = _mock_db()
        repo = ObservationRepo(db)
        data = ObservationCreate(
            owner_user_id="u1",
            source_type=SourceType.MANUAL,
            body="Met at conference",
        )
        result = await repo.insert(data)
        assert result.body == "Met at conference"
        assert result.visibility == Visibility.PRIVATE

    @pytest.mark.asyncio
    async def test_list_for_user_with_person_filter(self) -> None:
        oid = ObjectId()
        now = datetime.now(UTC)
        docs = [{
            "_id": oid,
            "owner_user_id": "u1",
            "source_type": "manual",
            "subject_person_id": "p1",
            "body": "note",
            "visibility": "private",
            "version": 1,
            "supersedes": None,
            "created_at": now,
        }]
        db = _mock_db(collection_docs=docs)
        repo = ObservationRepo(db)
        results = await repo.list_for_user("u1", person_id="p1")
        assert len(results) == 1


class TestEvidenceBundleRepo:
    @pytest.mark.asyncio
    async def test_insert(self) -> None:
        db = _mock_db()
        repo = EvidenceBundleRepo(db)
        data = EvidenceBundleCreate(
            owner_user_id="u1",
            person_id="p1",
            summary="Known from WhatsApp",
            evidence_ids=["e1"],
            fact_ids=["f1"],
        )
        result = await repo.insert(data)
        assert result.summary == "Known from WhatsApp"
        assert result.evidence_ids == ["e1"]

    @pytest.mark.asyncio
    async def test_get_not_found(self) -> None:
        db = _mock_db()
        repo = EvidenceBundleRepo(db)
        result = await repo.get(str(ObjectId()))
        assert result is None


class TestTimelineEventRepo:
    @pytest.mark.asyncio
    async def test_insert(self) -> None:
        db = _mock_db()
        repo = TimelineEventRepo(db)
        now = datetime.now(UTC)
        data = TimelineEventCreate(
            owner_user_id="u1",
            event_type=TimelineEventType.FACT_RECORDED,
            summary="A fact was recorded",
            occurred_at=now,
            refs=TimelineEventRefsCreate(fact_id="f1"),
        )
        result = await repo.insert(data)
        assert result.event_type == TimelineEventType.FACT_RECORDED
        assert result.refs.fact_id == "f1"

    @pytest.mark.asyncio
    async def test_list_for_user(self) -> None:
        oid = ObjectId()
        now = datetime.now(UTC)
        docs = [{
            "_id": oid,
            "owner_user_id": "u1",
            "event_type": "fact_recorded",
            "summary": "test",
            "occurred_at": now,
            "refs": {"fact_id": "f1"},
            "created_at": now,
        }]
        db = _mock_db(collection_docs=docs)
        repo = TimelineEventRepo(db)
        results = await repo.list_for_user("u1")
        assert len(results) == 1
        assert results[0].refs.fact_id == "f1"

    @pytest.mark.asyncio
    async def test_list_with_event_type_filter(self) -> None:
        db = _mock_db(collection_docs=[])
        repo = TimelineEventRepo(db)
        results = await repo.list_for_user(
            "u1", event_type=TimelineEventType.EVIDENCE_ADDED.value
        )
        assert results == []
        # Verify filter was applied
        db._coll.find.assert_called_once()
        call_args = db._coll.find.call_args[0][0]
        assert call_args["event_type"] == "evidence_added"
