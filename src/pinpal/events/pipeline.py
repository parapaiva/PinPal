"""Import pipeline orchestrator — claim check, translate, route."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from pinpal.api.schemas import (
    ImportResultRead,
    InstagramFollowsPayload,
    ManualObservationPayload,
    WhatsAppGroupPayload,
)
from pinpal.db.enums import SourceType
from pinpal.events.router import EventRouter, ImportContext
from pinpal.events.translators.instagram import translate_instagram_follows
from pinpal.events.translators.manual import translate_manual_observation
from pinpal.events.translators.whatsapp import translate_whatsapp_group
from pinpal.mongo.repositories import RawPayloadRepo
from pinpal.mongo.schemas import RawPayloadCreate


def _content_hash(payload: dict[str, Any]) -> str:
    """Compute SHA-256 hash of JSON-serialized payload."""
    raw = json.dumps(payload, sort_keys=True, default=str)
    return f"sha256:{hashlib.sha256(raw.encode()).hexdigest()}"


class ImportPipeline:
    """Orchestrates the full import flow: claim check → translate → route."""

    def __init__(
        self,
        session: AsyncSession,
        mongo_db: AsyncIOMotorDatabase,  # type: ignore[type-arg]
    ) -> None:
        self._session = session
        self._mongo_db = mongo_db

    async def execute(
        self,
        user_id: UUID,
        source_type: SourceType,
        raw_payload: dict[str, Any],
    ) -> ImportResultRead:
        """Run the full import pipeline and return results."""
        import_id = uuid4()
        correlation_id = uuid4()
        content_hash = _content_hash(raw_payload)
        now = datetime.now(UTC)

        # 1. Claim Check — deduplicate by content hash
        repo = RawPayloadRepo(self._mongo_db)
        existing = await self._mongo_db["raw_payloads"].find_one(
            {"owner_user_id": str(user_id), "content_hash": content_hash}
        )
        if existing is not None:
            return ImportResultRead(
                import_id=import_id,
                source_type=source_type,
                raw_payload_ref=str(existing["_id"]),
                events_produced=0,
                duplicate=True,
            )

        # 2. Store raw payload
        stored = await repo.insert(
            RawPayloadCreate(
                owner_user_id=str(user_id),
                source_type=source_type,
                payload=raw_payload,
                content_hash=content_hash,
            )
        )
        evidence_ref = stored.id

        # 3. Translate — validate + convert to canonical events
        events = self._translate(
            source_type=source_type,
            raw_payload=raw_payload,
            tenant_id=user_id,
            correlation_id=correlation_id,
            evidence_ref=evidence_ref,
            occurred_at=now,
        )

        # 4. Route — dispatch events to handlers
        ctx = ImportContext(user_id=user_id)
        router = EventRouter(self._session, self._mongo_db)
        ctx = await router.dispatch_all(events, ctx)

        return ImportResultRead(
            import_id=import_id,
            source_type=source_type,
            raw_payload_ref=evidence_ref,
            events_produced=len(events),
            entities_created=ctx.entities,
        )

    def _translate(
        self,
        *,
        source_type: SourceType,
        raw_payload: dict[str, Any],
        tenant_id: UUID,
        correlation_id: UUID,
        evidence_ref: str,
        occurred_at: datetime,
    ) -> list:  # type: ignore[type-arg]
        """Dispatch to the correct translator based on source_type."""
        if source_type == SourceType.WHATSAPP:
            wa_payload = WhatsAppGroupPayload(**raw_payload)
            return translate_whatsapp_group(
                wa_payload,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                evidence_ref=evidence_ref,
                occurred_at=occurred_at,
            )
        if source_type == SourceType.INSTAGRAM:
            ig_payload = InstagramFollowsPayload(**raw_payload)
            return translate_instagram_follows(
                ig_payload,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                evidence_ref=evidence_ref,
                occurred_at=occurred_at,
            )
        if source_type == SourceType.MANUAL:
            manual_payload = ManualObservationPayload(**raw_payload)
            return translate_manual_observation(
                manual_payload,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                evidence_ref=evidence_ref,
                occurred_at=occurred_at,
            )
        raise ValueError(f"Unsupported source type for import: {source_type}")
