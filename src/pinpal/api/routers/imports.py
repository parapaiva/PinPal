"""Import endpoint — ingest data from external sources."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from pinpal.api.deps import get_db_session, get_mongo_db
from pinpal.api.schemas import ImportRequest, ImportResultRead
from pinpal.db.enums import SourceType
from pinpal.db.models import User
from pinpal.events.pipeline import ImportPipeline

router = APIRouter(prefix="/api/v1/users/{user_id}/imports", tags=["imports"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
MongoDB = Annotated[AsyncIOMotorDatabase[dict[str, Any]], Depends(get_mongo_db)]

_IMPORTABLE_SOURCES = {SourceType.WHATSAPP, SourceType.INSTAGRAM, SourceType.MANUAL}


@router.post("", response_model=ImportResultRead, status_code=201)
async def create_import(
    user_id: UUID,
    body: ImportRequest,
    session: DbSession,
    mongo_db: MongoDB,
) -> ImportResultRead:
    """Ingest data from an external source through the import pipeline."""
    # Validate user exists
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate source_type is importable
    if body.source_type not in _IMPORTABLE_SOURCES:
        raise HTTPException(
            status_code=422,
            detail=f"Source type '{body.source_type}' is not supported for import",
        )

    # Run pipeline
    pipeline = ImportPipeline(session, mongo_db)
    try:
        return await pipeline.execute(user_id, body.source_type, body.payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
