"""Idempotent MongoDB index creation."""

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
    """Create all MongoDB indexes idempotently. Safe to call on every startup."""

    # raw_payloads
    await db["raw_payloads"].create_indexes([
        IndexModel([("owner_user_id", ASCENDING), ("created_at", DESCENDING)]),
        IndexModel([("owner_user_id", ASCENDING), ("source_type", ASCENDING)]),
        IndexModel(
            [("owner_user_id", ASCENDING), ("content_hash", ASCENDING)],
            unique=True,
            sparse=True,
        ),
    ])

    # observations
    await db["observations"].create_indexes([
        IndexModel([("owner_user_id", ASCENDING), ("created_at", DESCENDING)]),
        IndexModel(
            [("subject_person_id", ASCENDING), ("created_at", DESCENDING)],
            sparse=True,
        ),
    ])

    # evidence_bundles
    await db["evidence_bundles"].create_indexes([
        IndexModel([("owner_user_id", ASCENDING), ("person_id", ASCENDING)]),
        IndexModel([("person_id", ASCENDING)]),
    ])

    # timeline_events
    await db["timeline_events"].create_indexes([
        IndexModel([("owner_user_id", ASCENDING), ("occurred_at", DESCENDING)]),
        IndexModel([
            ("owner_user_id", ASCENDING),
            ("event_type", ASCENDING),
            ("occurred_at", DESCENDING),
        ]),
    ])
