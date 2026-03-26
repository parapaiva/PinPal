"""Unit tests for EventRouter and handlers — uses mocked DB sessions."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from pinpal.events.envelope import CanonicalEvent
from pinpal.events.router import EventRouter, ImportContext
from pinpal.events.types import (
    FACT_RECORDED,
    GROUP_IMPORTED,
    IDENTITY_LINKED,
)


def _make_event(event_type: str, payload: dict | None = None) -> CanonicalEvent:  # type: ignore[type-arg]
    cid = uuid4()
    return CanonicalEvent(
        correlation_id=cid,
        causation_id=cid,
        tenant_id=uuid4(),
        producer="test",
        event_type=event_type,
        occurred_at=datetime.now(UTC),
        payload=payload or {},
    )


class TestEventRouter:
    @pytest.fixture
    def session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mongo_db(self) -> MagicMock:
        return MagicMock()

    async def test_dispatches_known_event_types(
        self, session: AsyncMock, mongo_db: MagicMock
    ) -> None:
        router = EventRouter(session, mongo_db)
        handler = AsyncMock()
        router._handlers[GROUP_IMPORTED] = handler

        event = _make_event(GROUP_IMPORTED)
        ctx = ImportContext(user_id=uuid4())
        await router.dispatch_all([event], ctx)

        handler.assert_awaited_once_with(event, session, mongo_db, ctx)

    async def test_skips_unknown_event_types(
        self, session: AsyncMock, mongo_db: MagicMock
    ) -> None:
        router = EventRouter(session, mongo_db)
        event = _make_event("unknown.event.v1")
        ctx = ImportContext(user_id=uuid4())
        # Should not raise
        result = await router.dispatch_all([event], ctx)
        assert result is ctx

    async def test_dispatch_order_preserved(self, session: AsyncMock, mongo_db: MagicMock) -> None:
        router = EventRouter(session, mongo_db)
        call_order: list[str] = []

        async def track_handler(event, session, mongo_db, ctx):  # type: ignore[no-untyped-def]
            call_order.append(event.event_type)

        router._handlers[GROUP_IMPORTED] = track_handler
        router._handlers[IDENTITY_LINKED] = track_handler
        router._handlers[FACT_RECORDED] = track_handler

        events = [
            _make_event(GROUP_IMPORTED),
            _make_event(IDENTITY_LINKED),
            _make_event(FACT_RECORDED),
        ]
        ctx = ImportContext(user_id=uuid4())
        await router.dispatch_all(events, ctx)

        assert call_order == [GROUP_IMPORTED, IDENTITY_LINKED, FACT_RECORDED]

    async def test_context_accumulates_entities(
        self, session: AsyncMock, mongo_db: MagicMock
    ) -> None:
        router = EventRouter(session, mongo_db)

        async def increment_groups(event, session, mongo_db, ctx):  # type: ignore[no-untyped-def]
            ctx.entities.groups += 1

        router._handlers[GROUP_IMPORTED] = increment_groups

        events = [_make_event(GROUP_IMPORTED), _make_event(GROUP_IMPORTED)]
        ctx = ImportContext(user_id=uuid4())
        result = await router.dispatch_all(events, ctx)

        assert result.entities.groups == 2


class TestImportContext:
    def test_defaults(self) -> None:
        ctx = ImportContext()
        assert ctx.user_id is None
        assert ctx.group_id is None
        assert ctx.person_ids == {}
        assert ctx.entities.persons == 0

    def test_person_ids_tracking(self) -> None:
        ctx = ImportContext(user_id=uuid4())
        pid = uuid4()
        ctx.person_ids["Alice"] = pid
        assert ctx.person_ids["Alice"] == pid
