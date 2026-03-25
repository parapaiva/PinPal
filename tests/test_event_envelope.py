"""Unit tests for CanonicalEvent envelope and import schemas."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from pinpal.api.schemas import (
    ImportEntitiesSummary,
    ImportRequest,
    ImportResultRead,
    InstagramFollowEntry,
    InstagramFollowsPayload,
    ManualObservationPayload,
    WhatsAppGroupPayload,
    WhatsAppParticipant,
)
from pinpal.db.enums import SourceType, Visibility
from pinpal.events.envelope import CanonicalEvent


class TestCanonicalEvent:
    def test_construction_with_defaults(self) -> None:
        cid = uuid4()
        event = CanonicalEvent(
            correlation_id=cid,
            causation_id=cid,
            tenant_id=uuid4(),
            producer="test",
            event_type="test.event.v1",
            occurred_at=datetime.now(UTC),
        )
        assert event.message_id is not None
        assert event.event_version == 1
        assert event.visibility == Visibility.PRIVATE
        assert event.payload == {}
        assert event.evidence_ref is None

    def test_serialization_round_trip(self) -> None:
        cid = uuid4()
        event = CanonicalEvent(
            correlation_id=cid,
            causation_id=cid,
            tenant_id=uuid4(),
            producer="test",
            event_type="test.event.v1",
            occurred_at=datetime.now(UTC),
            payload={"key": "value"},
            evidence_ref="ref-123",
        )
        data = event.model_dump(mode="json")
        restored = CanonicalEvent(**data)
        assert restored.message_id == event.message_id
        assert restored.payload == {"key": "value"}
        assert restored.evidence_ref == "ref-123"

    def test_unique_message_ids(self) -> None:
        cid = uuid4()
        kwargs = {
            "correlation_id": cid,
            "causation_id": cid,
            "tenant_id": uuid4(),
            "producer": "test",
            "event_type": "test.v1",
            "occurred_at": datetime.now(UTC),
        }
        e1 = CanonicalEvent(**kwargs)
        e2 = CanonicalEvent(**kwargs)
        assert e1.message_id != e2.message_id


class TestWhatsAppSchemas:
    def test_valid_whatsapp_payload(self) -> None:
        payload = WhatsAppGroupPayload(
            group_name="Family",
            participants=[WhatsAppParticipant(display_name="Alice", phone_number="+1234")],
        )
        assert payload.group_name == "Family"
        assert len(payload.participants) == 1

    def test_empty_participants_rejected(self) -> None:
        with pytest.raises(ValidationError):
            WhatsAppGroupPayload(group_name="Empty", participants=[])

    def test_missing_group_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            WhatsAppGroupPayload(
                participants=[WhatsAppParticipant(display_name="Alice")]
            )

    def test_participant_optional_fields(self) -> None:
        p = WhatsAppParticipant(display_name="Bob")
        assert p.phone_number is None
        assert p.handle is None


class TestInstagramSchemas:
    def test_valid_instagram_payload(self) -> None:
        payload = InstagramFollowsPayload(
            follows=[InstagramFollowEntry(username="alice_ig")]
        )
        assert len(payload.follows) == 1

    def test_empty_follows_rejected(self) -> None:
        with pytest.raises(ValidationError):
            InstagramFollowsPayload(follows=[])

    def test_display_name_optional(self) -> None:
        entry = InstagramFollowEntry(username="bob")
        assert entry.display_name is None


class TestManualObservationSchema:
    def test_valid_manual(self) -> None:
        obs = ManualObservationPayload(
            person_display_name="Charlie",
            body="Met at conference",
        )
        assert obs.visibility == Visibility.PRIVATE
        assert obs.person_id is None

    def test_with_person_id(self) -> None:
        pid = uuid4()
        obs = ManualObservationPayload(
            person_display_name="Charlie",
            person_id=pid,
            body="Met at conference",
        )
        assert obs.person_id == pid

    def test_empty_body_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ManualObservationPayload(person_display_name="Charlie", body="")


class TestImportSchemas:
    def test_import_request(self) -> None:
        req = ImportRequest(source_type=SourceType.WHATSAPP, payload={"key": "val"})
        assert req.source_type == SourceType.WHATSAPP

    def test_import_entities_summary_defaults(self) -> None:
        summary = ImportEntitiesSummary()
        assert summary.persons == 0
        assert summary.timeline_events == 0

    def test_import_result_read(self) -> None:
        result = ImportResultRead(
            import_id=uuid4(),
            source_type=SourceType.WHATSAPP,
            raw_payload_ref="abc123",
            events_produced=5,
        )
        assert result.duplicate is False
        assert result.entities_created.persons == 0
