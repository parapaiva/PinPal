"""Shared test fixtures."""

import uuid
from datetime import UTC, datetime

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from pinpal.api.app import create_app
from pinpal.config import Settings
from pinpal.db.base import Base
from pinpal.db.enums import (
    FactType,
    GroupType,
    RelationshipType,
    SourceType,
    Visibility,
)
from pinpal.db.models import (
    Fact,
    Group,
    Identity,
    Membership,
    Person,
    Relationship,
    User,
)
from pinpal.db.session import create_engine, create_session_factory


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
    async with LifespanManager(app) as manager:
        # Create tables using the app's own engine (created by lifespan)
        engine = app.state.engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url="http://test",
        ) as ac:
            yield ac

        # Teardown: drop tables + enum types
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            for enum_name in [
                "factstatus",
                "facttype",
                "sourcetype",
                "visibility",
                "sharingmode",
                "relationshiptype",
                "relationshipstatus",
                "grouptype",
                "sourceaccountstatus",
            ]:
                await conn.execute(text(f"DROP TYPE IF EXISTS {enum_name}"))


@pytest.fixture
async def db_session(settings: Settings) -> AsyncSession:  # type: ignore[misc]
    """Provide a fresh async DB session with tables created/dropped per test."""
    engine = create_engine(settings.postgres_dsn)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = create_session_factory(engine)
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        # Drop enum types created by SQLAlchemy
        for enum_name in [
            "sourcetype",
            "visibility",
            "sharingmode",
            "relationshiptype",
            "relationshipstatus",
            "grouptype",
            "sourceaccountstatus",
        ]:
            await conn.execute(text(f"DROP TYPE IF EXISTS {enum_name}"))

    await engine.dispose()


# ---- Factory helpers ----


async def create_test_user(
    session: AsyncSession,
    email: str | None = None,
    display_name: str = "Test User",
) -> User:
    user = User(
        email=email or f"{uuid.uuid4().hex[:8]}@test.com",
        display_name=display_name,
    )
    session.add(user)
    await session.flush()
    return user


async def create_test_person(
    session: AsyncSession,
    owner: User,
    display_name: str = "Test Person",
) -> Person:
    person = Person(owner_user_id=owner.id, display_name=display_name)
    session.add(person)
    await session.flush()
    return person


async def create_test_group(
    session: AsyncSession,
    owner: User,
    name: str = "Test Group",
    group_type: GroupType = GroupType.CUSTOM,
) -> Group:
    group = Group(owner_user_id=owner.id, group_type=group_type, name=name)
    session.add(group)
    await session.flush()
    return group


async def create_test_membership(
    session: AsyncSession,
    group: Group,
    person: Person,
) -> Membership:
    membership = Membership(group_id=group.id, person_id=person.id)
    session.add(membership)
    await session.flush()
    return membership


async def create_test_identity(
    session: AsyncSession,
    person: Person,
    source_type: SourceType = SourceType.WHATSAPP,
    handle: str | None = None,
) -> Identity:
    identity = Identity(person_id=person.id, source_type=source_type, handle=handle)
    session.add(identity)
    await session.flush()
    return identity


async def create_test_relationship(
    session: AsyncSession,
    person_a: Person,
    person_b: Person,
    relationship_type: RelationshipType = RelationshipType.MANUAL,
    confidence: float = 0.8,
) -> Relationship:
    a_id, b_id = sorted([person_a.id, person_b.id])
    rel = Relationship(
        person_a_id=a_id,
        person_b_id=b_id,
        relationship_type=relationship_type,
        confidence=confidence,
    )
    session.add(rel)
    await session.flush()
    return rel


async def create_test_fact(
    session: AsyncSession,
    owner: User,
    *,
    fact_type: FactType = FactType.MANUAL_NOTE,
    source_type: SourceType = SourceType.MANUAL,
    person: Person | None = None,
    confidence: float | None = None,
    observed_at: datetime | None = None,
    visibility: Visibility = Visibility.PRIVATE,
    evidence_ref: str | None = None,
) -> Fact:
    fact = Fact(
        owner_user_id=owner.id,
        fact_type=fact_type,
        source_type=source_type,
        payload={},
        confidence=confidence,
        observed_at=observed_at or datetime.now(UTC),
        visibility=visibility,
        evidence_ref=evidence_ref,
        person_id=person.id if person else None,
    )
    session.add(fact)
    await session.flush()
    return fact


# ---- Mongo fixtures ----


@pytest.fixture
async def mongo_db(app):  # type: ignore[no-untyped-def]
    """Provide the Motor database from the running app and clean up after test."""
    async with LifespanManager(app) as manager:
        db = manager.app.state.mongo_db
        yield db
        # Teardown: drop all test collections
        for coll_name in await db.list_collection_names():
            await db.drop_collection(coll_name)
