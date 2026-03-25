"""Handler: group.imported → create Group in Postgres."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pinpal.db.enums import GroupType, Visibility
from pinpal.db.models import Group

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from sqlalchemy.ext.asyncio import AsyncSession

    from pinpal.events.envelope import CanonicalEvent
    from pinpal.events.router import ImportContext


async def handle_group_imported(
    event: CanonicalEvent,
    session: AsyncSession,
    mongo_db: AsyncIOMotorDatabase,  # type: ignore[type-arg]
    ctx: ImportContext,
) -> None:
    """Create a Group from a group.imported event."""
    payload = event.payload
    group = Group(
        owner_user_id=ctx.user_id,
        group_type=GroupType(payload["group_type"]),
        name=payload["group_name"],
        visibility=Visibility(event.visibility),
    )
    session.add(group)
    await session.flush()
    ctx.group_id = group.id
    ctx.entities.groups += 1
