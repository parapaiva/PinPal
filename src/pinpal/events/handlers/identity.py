"""Handler: identity.linked → lookup-or-create Person + Identity."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from pinpal.db.enums import SourceType
from pinpal.db.models import Identity, Person

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from sqlalchemy.ext.asyncio import AsyncSession

    from pinpal.events.envelope import CanonicalEvent
    from pinpal.events.router import ImportContext


async def _get_or_create_person(
    session: AsyncSession,
    ctx: ImportContext,
    display_name: str,
) -> UUID:
    """Return existing person_id from context or DB, or create a new Person."""
    # Check import-local cache first
    if display_name in ctx.person_ids:
        return ctx.person_ids[display_name]

    # Check DB for existing person with same name under this user
    stmt = select(Person).where(
        Person.owner_user_id == ctx.user_id,
        Person.display_name == display_name,
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        ctx.person_ids[display_name] = existing.id
        return existing.id

    # Create new
    person = Person(owner_user_id=ctx.user_id, display_name=display_name)
    session.add(person)
    await session.flush()
    ctx.person_ids[display_name] = person.id
    ctx.entities.persons += 1
    return person.id


async def handle_identity_linked(
    event: CanonicalEvent,
    session: AsyncSession,
    mongo_db: AsyncIOMotorDatabase,  # type: ignore[type-arg]
    ctx: ImportContext,
) -> None:
    """Create Person (if needed) and Identity from an identity.linked event."""
    payload = event.payload
    display_name: str = payload["display_name"]
    person_id = await _get_or_create_person(session, ctx, display_name)

    source_type = SourceType(payload["source_type"])
    external_id = payload.get("external_id")
    handle = payload.get("handle")

    identity = Identity(
        person_id=person_id,
        source_type=source_type,
        external_id=external_id,
        handle=handle,
    )
    session.add(identity)
    try:
        await session.flush()
        ctx.entities.identities += 1
    except IntegrityError:
        # Identity already exists (unique constraint) — idempotent
        await session.rollback()
