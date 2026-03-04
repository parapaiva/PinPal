"""Async MongoDB client using Motor."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


def create_mongo_client(dsn: str) -> AsyncIOMotorClient:  # type: ignore[type-arg]
    """Create an async Motor client."""
    return AsyncIOMotorClient(dsn)


def get_mongo_db(
    client: AsyncIOMotorClient,  # type: ignore[type-arg]
    db_name: str,
) -> AsyncIOMotorDatabase:  # type: ignore[type-arg]
    """Return a Motor database handle."""
    return client[db_name]
