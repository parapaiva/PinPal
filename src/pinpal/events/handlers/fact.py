"""Handler: fact.recorded → create Fact in Postgres + timeline event."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pinpal.db.enums import FactType, SourceType, TimelineEventType
from pinpal.db.models import Fact
from pinpal.mongo.repositories import TimelineEventRepo
from pinpal.mongo.schemas import TimelineEventCreate, TimelineEventRefsCreate

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from sqlalchemy.ext.asyncio import AsyncSession

    from pinpal.events.envelope import CanonicalEvent
    from pinpal.events.router import ImportContext


async def handle_fact_recorded(
    event: CanonicalEvent,
    session: AsyncSession,
    mongo_db: AsyncIOMotorDatabase,  # type: ignore[type-arg]
    ctx: ImportContext,
) -> None:
    """Create a Fact and record a timeline event."""
    payload = event.payload
    display_name: str = payload.get("display_name", "")
    person_id = ctx.person_ids.get(display_name)

    fact_type = FactType(payload["fact_type"])
    source_type = SourceType(payload["source_type"])

    fact = Fact(
        owner_user_id=ctx.user_id,
        fact_type=fact_type,
        source_type=source_type,
        payload=payload,
        observed_at=event.occurred_at,
        visibility=event.visibility,
        evidence_ref=event.evidence_ref,
        person_id=person_id,
        group_id=ctx.group_id,
    )
    session.add(fact)
    await session.flush()
    ctx.entities.facts += 1

    # Record timeline event in MongoDB
    repo = TimelineEventRepo(mongo_db)
    await repo.insert(
        TimelineEventCreate(
            owner_user_id=str(ctx.user_id),
            event_type=TimelineEventType.FACT_RECORDED,
            summary=f"{fact_type.value} from {source_type.value}",
            occurred_at=event.occurred_at,
            refs=TimelineEventRefsCreate(
                fact_id=str(fact.id),
                person_id=str(person_id) if person_id else None,
                group_id=str(ctx.group_id) if ctx.group_id else None,
            ),
        )
    )
    ctx.entities.timeline_events += 1
