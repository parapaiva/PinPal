"""Content-based event router — dispatches canonical events to type-specific handlers."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from pinpal.api.schemas import ImportEntitiesSummary
from pinpal.events.envelope import CanonicalEvent
from pinpal.events.handlers.fact import handle_fact_recorded
from pinpal.events.handlers.group import handle_group_imported
from pinpal.events.handlers.identity import handle_identity_linked
from pinpal.events.handlers.membership import handle_membership_observed
from pinpal.events.handlers.observation import handle_observation_recorded
from pinpal.events.types import (
    FACT_RECORDED,
    GROUP_IMPORTED,
    IDENTITY_LINKED,
    MEMBERSHIP_OBSERVED,
    OBSERVATION_RECORDED,
)

logger = logging.getLogger(__name__)

HandlerFn = Callable[
    [CanonicalEvent, AsyncSession, AsyncIOMotorDatabase, "ImportContext"],  # type: ignore[type-arg]
    Awaitable[None],
]


@dataclass
class ImportContext:
    """Accumulated state shared across handlers during a single import."""

    user_id: UUID | None = None
    group_id: UUID | None = None
    person_ids: dict[str, UUID] = field(default_factory=dict)
    entities: ImportEntitiesSummary = field(default_factory=ImportEntitiesSummary)


class EventRouter:
    """Routes canonical events to registered handler functions by event_type."""

    def __init__(
        self,
        session: AsyncSession,
        mongo_db: AsyncIOMotorDatabase,  # type: ignore[type-arg]
    ) -> None:
        self._session = session
        self._mongo_db = mongo_db
        self._handlers: dict[str, HandlerFn] = {
            GROUP_IMPORTED: handle_group_imported,
            IDENTITY_LINKED: handle_identity_linked,
            MEMBERSHIP_OBSERVED: handle_membership_observed,
            FACT_RECORDED: handle_fact_recorded,
            OBSERVATION_RECORDED: handle_observation_recorded,
        }

    async def dispatch_all(
        self,
        events: list[CanonicalEvent],
        ctx: ImportContext,
    ) -> ImportContext:
        """Dispatch each event in order. Unknown event types are skipped."""
        for event in events:
            handler = self._handlers.get(event.event_type)
            if handler is None:
                logger.warning("No handler for event_type=%s, skipping", event.event_type)
                continue
            await handler(event, self._session, self._mongo_db, ctx)
        return ctx
