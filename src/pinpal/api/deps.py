"""FastAPI dependency injection utilities."""

from collections.abc import AsyncIterator

from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield an async DB session; commit on success, rollback on error."""
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_mongo_db(request: Request) -> AsyncIOMotorDatabase:  # type: ignore[type-arg]
    """Return the Motor database handle from app state."""
    return request.app.state.mongo_db  # type: ignore[no-any-return]
