"""Shared test fixtures."""

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from pinpal.api.app import create_app
from pinpal.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Return default settings (matching docker-compose)."""
    return Settings()


@pytest.fixture
def app(settings: Settings):
    """Create a FastAPI app instance for testing."""
    return create_app(settings=settings)


@pytest.fixture
async def client(app) -> AsyncClient:  # type: ignore[type-arg]
    """Async HTTP client wired to the FastAPI app."""
    async with (
        LifespanManager(app) as manager,
        AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url="http://test",
        ) as ac,
    ):
        yield ac
