"""Handler: observation.recorded → create Observation in MongoDB."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select

from pinpal.db.enums import SourceType
from pinpal.db.models import Person
from pinpal.mongo.repositories import ObservationRepo
from pinpal.mongo.schemas import ObservationCreate

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from sqlalchemy.ext.asyncio import AsyncSession

    from pinpal.events.envelope import CanonicalEvent
    from pinpal.events.router import ImportContext


async def _resolve_person_id(
    session: AsyncSession,
    ctx: ImportContext,
    payload: dict,  # type: ignore[type-arg]
) -> UUID | None:
    """Resolve person_id from payload or by display_name lookup."""
    # Explicit person_id in payload
    if payload.get("person_id"):
        return UUID(payload["person_id"])

    display_name: str = payload.get("person_display_name", "")

    # Check import-local cache
    if display_name in ctx.person_ids:
        return ctx.person_ids[display_name]

    # Check DB
    stmt = select(Person).where(
        Person.owner_user_id == ctx.user_id,
        Person.display_name == display_name,
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        ctx.person_ids[display_name] = existing.id
        return existing.id

    # Create new person
    person = Person(owner_user_id=ctx.user_id, display_name=display_name)
    session.add(person)
    await session.flush()
    ctx.person_ids[display_name] = person.id
    ctx.entities.persons += 1
    return person.id


async def handle_observation_recorded(
    event: CanonicalEvent,
    session: AsyncSession,
    mongo_db: AsyncIOMotorDatabase,  # type: ignore[type-arg]
    ctx: ImportContext,
) -> None:
    """Create an Observation in MongoDB."""
    payload = event.payload
    person_id = await _resolve_person_id(session, ctx, payload)

    repo = ObservationRepo(mongo_db)
    await repo.insert(
        ObservationCreate(
            owner_user_id=str(ctx.user_id),
            source_type=SourceType(payload["source_type"]),
            subject_person_id=str(person_id) if person_id else None,
            body=payload["body"],
            visibility=event.visibility,
        )
    )
    ctx.entities.observations += 1
