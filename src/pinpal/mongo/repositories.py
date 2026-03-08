"""Thin repository classes wrapping Motor queries for MongoDB collections."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from pinpal.mongo.schemas import (
    EvidenceBundleCreate,
    EvidenceBundleRead,
    ObservationCreate,
    ObservationRead,
    RawPayloadCreate,
    RawPayloadRead,
    TimelineEventCreate,
    TimelineEventRead,
    TimelineEventRefsRead,
)


def _oid(doc: dict[str, Any]) -> str:
    """Convert MongoDB ObjectId to hex string."""
    return str(doc["_id"])


class RawPayloadRepo:
    COLLECTION = "raw_payloads"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._coll = db[self.COLLECTION]

    async def insert(self, data: RawPayloadCreate) -> RawPayloadRead:
        doc = {
            **data.model_dump(),
            "created_at": datetime.now(UTC),
        }
        result = await self._coll.insert_one(doc)
        doc["_id"] = result.inserted_id
        return RawPayloadRead(
            id=_oid(doc),
            owner_user_id=doc["owner_user_id"],
            source_type=doc["source_type"],
            payload=doc["payload"],
            content_hash=doc["content_hash"],
            created_at=doc["created_at"],
        )

    async def get(self, doc_id: str) -> RawPayloadRead | None:
        from bson import ObjectId

        doc = await self._coll.find_one({"_id": ObjectId(doc_id)})
        if doc is None:
            return None
        return RawPayloadRead(
            id=_oid(doc),
            owner_user_id=doc["owner_user_id"],
            source_type=doc["source_type"],
            payload=doc["payload"],
            content_hash=doc["content_hash"],
            created_at=doc["created_at"],
        )

    async def list_for_user(
        self,
        owner_user_id: str,
        *,
        source_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RawPayloadRead]:
        query: dict[str, Any] = {"owner_user_id": owner_user_id}
        if source_type is not None:
            query["source_type"] = source_type
        cursor = (
            self._coll.find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        results: list[RawPayloadRead] = []
        async for doc in cursor:
            results.append(
                RawPayloadRead(
                    id=_oid(doc),
                    owner_user_id=doc["owner_user_id"],
                    source_type=doc["source_type"],
                    payload=doc["payload"],
                    content_hash=doc["content_hash"],
                    created_at=doc["created_at"],
                )
            )
        return results


class ObservationRepo:
    COLLECTION = "observations"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._coll = db[self.COLLECTION]

    async def insert(self, data: ObservationCreate) -> ObservationRead:
        doc = {
            **data.model_dump(),
            "created_at": datetime.now(UTC),
        }
        result = await self._coll.insert_one(doc)
        doc["_id"] = result.inserted_id
        return ObservationRead(
            id=_oid(doc),
            owner_user_id=doc["owner_user_id"],
            source_type=doc["source_type"],
            subject_person_id=doc["subject_person_id"],
            body=doc["body"],
            visibility=doc["visibility"],
            version=doc["version"],
            supersedes=doc["supersedes"],
            created_at=doc["created_at"],
        )

    async def get(self, doc_id: str) -> ObservationRead | None:
        from bson import ObjectId

        doc = await self._coll.find_one({"_id": ObjectId(doc_id)})
        if doc is None:
            return None
        return ObservationRead(
            id=_oid(doc),
            owner_user_id=doc["owner_user_id"],
            source_type=doc["source_type"],
            subject_person_id=doc.get("subject_person_id"),
            body=doc["body"],
            visibility=doc["visibility"],
            version=doc["version"],
            supersedes=doc.get("supersedes"),
            created_at=doc["created_at"],
        )

    async def list_for_user(
        self,
        owner_user_id: str,
        *,
        person_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ObservationRead]:
        query: dict[str, Any] = {"owner_user_id": owner_user_id}
        if person_id is not None:
            query["subject_person_id"] = person_id
        cursor = (
            self._coll.find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        results: list[ObservationRead] = []
        async for doc in cursor:
            results.append(
                ObservationRead(
                    id=_oid(doc),
                    owner_user_id=doc["owner_user_id"],
                    source_type=doc["source_type"],
                    subject_person_id=doc.get("subject_person_id"),
                    body=doc["body"],
                    visibility=doc["visibility"],
                    version=doc["version"],
                    supersedes=doc.get("supersedes"),
                    created_at=doc["created_at"],
                )
            )
        return results


class EvidenceBundleRepo:
    COLLECTION = "evidence_bundles"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._coll = db[self.COLLECTION]

    async def insert(self, data: EvidenceBundleCreate) -> EvidenceBundleRead:
        now = datetime.now(UTC)
        doc = {
            **data.model_dump(),
            "assembled_at": now,
            "created_at": now,
        }
        result = await self._coll.insert_one(doc)
        doc["_id"] = result.inserted_id
        return EvidenceBundleRead(
            id=_oid(doc),
            owner_user_id=doc["owner_user_id"],
            person_id=doc["person_id"],
            summary=doc["summary"],
            evidence_ids=doc["evidence_ids"],
            fact_ids=doc["fact_ids"],
            assembled_at=doc["assembled_at"],
            created_at=doc["created_at"],
        )

    async def get(self, doc_id: str) -> EvidenceBundleRead | None:
        from bson import ObjectId

        doc = await self._coll.find_one({"_id": ObjectId(doc_id)})
        if doc is None:
            return None
        return EvidenceBundleRead(
            id=_oid(doc),
            owner_user_id=doc["owner_user_id"],
            person_id=doc["person_id"],
            summary=doc["summary"],
            evidence_ids=doc["evidence_ids"],
            fact_ids=doc["fact_ids"],
            assembled_at=doc["assembled_at"],
            created_at=doc["created_at"],
        )

    async def list_for_user(
        self,
        owner_user_id: str,
        *,
        person_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EvidenceBundleRead]:
        query: dict[str, Any] = {"owner_user_id": owner_user_id}
        if person_id is not None:
            query["person_id"] = person_id
        cursor = (
            self._coll.find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        results: list[EvidenceBundleRead] = []
        async for doc in cursor:
            results.append(
                EvidenceBundleRead(
                    id=_oid(doc),
                    owner_user_id=doc["owner_user_id"],
                    person_id=doc["person_id"],
                    summary=doc["summary"],
                    evidence_ids=doc["evidence_ids"],
                    fact_ids=doc["fact_ids"],
                    assembled_at=doc["assembled_at"],
                    created_at=doc["created_at"],
                )
            )
        return results


class TimelineEventRepo:
    COLLECTION = "timeline_events"

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._coll = db[self.COLLECTION]

    async def insert(self, data: TimelineEventCreate) -> TimelineEventRead:
        doc = {
            **data.model_dump(),
            "created_at": datetime.now(UTC),
        }
        result = await self._coll.insert_one(doc)
        doc["_id"] = result.inserted_id
        refs = doc.get("refs", {})
        return TimelineEventRead(
            id=_oid(doc),
            owner_user_id=doc["owner_user_id"],
            event_type=doc["event_type"],
            summary=doc["summary"],
            occurred_at=doc["occurred_at"],
            refs=TimelineEventRefsRead(**refs),
            created_at=doc["created_at"],
        )

    async def list_for_user(
        self,
        owner_user_id: str,
        *,
        event_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TimelineEventRead]:
        query: dict[str, Any] = {"owner_user_id": owner_user_id}
        if event_type is not None:
            query["event_type"] = event_type
        cursor = (
            self._coll.find(query)
            .sort("occurred_at", -1)
            .skip(offset)
            .limit(limit)
        )
        results: list[TimelineEventRead] = []
        async for doc in cursor:
            refs = doc.get("refs", {})
            results.append(
                TimelineEventRead(
                    id=_oid(doc),
                    owner_user_id=doc["owner_user_id"],
                    event_type=doc["event_type"],
                    summary=doc["summary"],
                    occurred_at=doc["occurred_at"],
                    refs=TimelineEventRefsRead(**refs),
                    created_at=doc["created_at"],
                )
            )
        return results
