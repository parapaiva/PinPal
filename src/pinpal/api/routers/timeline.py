"""Timeline event endpoints (MongoDB)."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from pinpal.api.deps import get_mongo_db
from pinpal.db.enums import TimelineEventType
from pinpal.mongo.repositories import TimelineEventRepo
from pinpal.mongo.schemas import TimelineEventCreate, TimelineEventRead

router = APIRouter(prefix="/api/v1/users/{user_id}/timeline", tags=["timeline"])

MongoDB = Annotated[AsyncIOMotorDatabase[dict[str, Any]], Depends(get_mongo_db)]


@router.post("", response_model=TimelineEventRead, status_code=201)
async def record_event(user_id: UUID, body: TimelineEventCreate, db: MongoDB) -> TimelineEventRead:
    body.owner_user_id = str(user_id)
    repo = TimelineEventRepo(db)
    return await repo.insert(body)


@router.get("", response_model=list[TimelineEventRead])
async def list_events(
    user_id: UUID,
    db: MongoDB,
    event_type: TimelineEventType | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[TimelineEventRead]:
    repo = TimelineEventRepo(db)
    return await repo.list_for_user(
        str(user_id),
        event_type=event_type.value if event_type else None,
        limit=limit,
        offset=offset,
    )
