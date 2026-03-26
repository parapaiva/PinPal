"""Handler: membership.observed → create Membership + timeline event."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError

from pinpal.db.enums import TimelineEventType
from pinpal.db.models import Membership
from pinpal.mongo.repositories import TimelineEventRepo
from pinpal.mongo.schemas import TimelineEventCreate, TimelineEventRefsCreate

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from sqlalchemy.ext.asyncio import AsyncSession

    from pinpal.events.envelope import CanonicalEvent
    from pinpal.events.router import ImportContext


async def handle_membership_observed(
    event: CanonicalEvent,
    session: AsyncSession,
    mongo_db: AsyncIOMotorDatabase,  # type: ignore[type-arg]
    ctx: ImportContext,
) -> None:
    """Create a Membership and record a timeline event."""
    payload = event.payload
    display_name: str = payload["display_name"]
    person_id = ctx.person_ids.get(display_name)
    if person_id is None or ctx.group_id is None:
        return

    membership = Membership(
        group_id=ctx.group_id,
        person_id=person_id,
        evidence_ref=event.evidence_ref,
    )
    session.add(membership)
    try:
        await session.flush()
        ctx.entities.memberships += 1
    except IntegrityError:
        # Membership already exists (unique constraint) — idempotent
        await session.rollback()
        return

    # Record timeline event in MongoDB
    repo = TimelineEventRepo(mongo_db)
    await repo.insert(
        TimelineEventCreate(
            owner_user_id=str(ctx.user_id),
            event_type=TimelineEventType.MEMBERSHIP_OBSERVED,
            summary=f"{display_name} observed in group",
            occurred_at=event.occurred_at,
            refs=TimelineEventRefsCreate(
                person_id=str(person_id),
                group_id=str(ctx.group_id),
            ),
        )
    )
    ctx.entities.timeline_events += 1
