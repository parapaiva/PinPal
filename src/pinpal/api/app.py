"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from pinpal.api.health import router as health_router
from pinpal.api.routers import (
    evidence_router,
    facts_router,
    groups_router,
    imports_router,
    persons_router,
    relationships_router,
    timeline_router,
    users_router,
)
from pinpal.config import Settings
from pinpal.db.session import create_engine, create_session_factory
from pinpal.logging import setup_logging
from pinpal.mongo.client import create_mongo_client, get_mongo_db
from pinpal.mongo.indexes import ensure_indexes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup/shutdown of database connections."""
    settings: Settings = app.state.settings

    # Postgres
    engine = create_engine(settings.postgres_dsn)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    # MongoDB
    mongo_client = create_mongo_client(settings.mongo_dsn)
    app.state.mongo_client = mongo_client
    app.state.mongo_db = get_mongo_db(mongo_client, settings.mongo_db)

    await ensure_indexes(app.state.mongo_db)

    yield

    # Shutdown
    await engine.dispose()
    mongo_client.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and return the FastAPI application."""
    if settings is None:
        settings = Settings()

    setup_logging(log_level=settings.log_level, log_format=settings.log_format)

    app = FastAPI(title="PinPal", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings

    app.include_router(health_router)
    app.include_router(users_router)
    app.include_router(persons_router)
    app.include_router(groups_router)
    app.include_router(relationships_router)
    app.include_router(facts_router)
    app.include_router(evidence_router)
    app.include_router(timeline_router)
    app.include_router(imports_router)

    return app
