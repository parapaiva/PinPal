"""Unit tests for MongoDB Pydantic schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pinpal.db.enums import SourceType, TimelineEventType, Visibility
from pinpal.mongo.schemas import (
    EvidenceBundleCreate,
    EvidenceBundleRead,
    ObservationCreate,
    ObservationRead,
    RawPayloadCreate,
    RawPayloadRead,
    TimelineEventCreate,
    TimelineEventRead,
    TimelineEventRefsCreate,
    TimelineEventRefsRead,
)


class TestRawPayloadSchemas:
    def test_create_valid(self) -> None:
        schema = RawPayloadCreate(
            owner_user_id="abc123",
            source_type=SourceType.WHATSAPP,
            payload={"messages": [1, 2]},
            content_hash="sha256:deadbeef",
        )
        assert schema.source_type == SourceType.WHATSAPP
        assert schema.payload == {"messages": [1, 2]}

    def test_create_missing_required(self) -> None:
        with pytest.raises(ValidationError):
            RawPayloadCreate(
                owner_user_id="abc",
                source_type=SourceType.WHATSAPP,
                # missing payload and content_hash
            )  # type: ignore[call-arg]

    def test_read_schema(self) -> None:
        now = datetime.now(UTC)
        schema = RawPayloadRead(
            id="60d5f8a0b1e2c3f4a5b6c7d8",
            owner_user_id="abc123",
            source_type=SourceType.INSTAGRAM,
            payload={"data": "test"},
            content_hash="sha256:abc",
            created_at=now,
        )
        assert schema.id == "60d5f8a0b1e2c3f4a5b6c7d8"


class TestObservationSchemas:
    def test_create_defaults(self) -> None:
        schema = ObservationCreate(
            owner_user_id="user1",
            source_type=SourceType.MANUAL,
            body="Met at conference",
        )
        assert schema.visibility == Visibility.PRIVATE
        assert schema.version == 1
        assert schema.supersedes is None

    def test_create_with_person(self) -> None:
        schema = ObservationCreate(
            owner_user_id="user1",
            source_type=SourceType.MANUAL,
            subject_person_id="person-uuid-hex",
            body="Works at Acme Corp",
            visibility=Visibility.FRIENDS,
            version=2,
            supersedes="prev-id",
        )
        assert schema.subject_person_id == "person-uuid-hex"
        assert schema.version == 2

    def test_read_schema(self) -> None:
        now = datetime.now(UTC)
        schema = ObservationRead(
            id="oid1",
            owner_user_id="u1",
            source_type=SourceType.MANUAL,
            subject_person_id=None,
            body="test",
            visibility=Visibility.PRIVATE,
            version=1,
            supersedes=None,
            created_at=now,
        )
        assert schema.body == "test"


class TestEvidenceBundleSchemas:
    def test_create_defaults(self) -> None:
        schema = EvidenceBundleCreate(
            owner_user_id="u1",
            person_id="p1",
            summary="Known from WhatsApp group",
        )
        assert schema.evidence_ids == []
        assert schema.fact_ids == []

    def test_create_with_ids(self) -> None:
        schema = EvidenceBundleCreate(
            owner_user_id="u1",
            person_id="p1",
            summary="Multiple sources",
            evidence_ids=["e1", "e2"],
            fact_ids=["f1"],
        )
        assert len(schema.evidence_ids) == 2

    def test_read_schema(self) -> None:
        now = datetime.now(UTC)
        schema = EvidenceBundleRead(
            id="oid1",
            owner_user_id="u1",
            person_id="p1",
            summary="test",
            evidence_ids=[],
            fact_ids=[],
            assembled_at=now,
            created_at=now,
        )
        assert schema.assembled_at == now


class TestTimelineEventSchemas:
    def test_create_minimal(self) -> None:
        now = datetime.now(UTC)
        schema = TimelineEventCreate(
            owner_user_id="u1",
            event_type=TimelineEventType.FACT_RECORDED,
            summary="New fact recorded",
            occurred_at=now,
        )
        assert schema.refs.evidence_id is None

    def test_create_with_refs(self) -> None:
        now = datetime.now(UTC)
        refs = TimelineEventRefsCreate(
            fact_id="fact-1",
            person_id="person-1",
        )
        schema = TimelineEventCreate(
            owner_user_id="u1",
            event_type=TimelineEventType.EVIDENCE_ADDED,
            summary="Evidence added",
            occurred_at=now,
            refs=refs,
        )
        assert schema.refs.fact_id == "fact-1"

    def test_read_schema(self) -> None:
        now = datetime.now(UTC)
        schema = TimelineEventRead(
            id="oid1",
            owner_user_id="u1",
            event_type=TimelineEventType.IDENTITY_LINKED,
            summary="test",
            occurred_at=now,
            refs=TimelineEventRefsRead(),
            created_at=now,
        )
        assert schema.refs.person_id is None
