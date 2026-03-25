"""Unit tests for source translators — pure functions, no DB required."""

from datetime import UTC, datetime
from uuid import uuid4

from pinpal.api.schemas import (
    InstagramFollowEntry,
    InstagramFollowsPayload,
    ManualObservationPayload,
    WhatsAppGroupPayload,
    WhatsAppParticipant,
)
from pinpal.db.enums import Visibility
from pinpal.events.translators.instagram import translate_instagram_follows
from pinpal.events.translators.manual import translate_manual_observation
from pinpal.events.translators.whatsapp import translate_whatsapp_group
from pinpal.events.types import (
    FACT_RECORDED,
    GROUP_IMPORTED,
    IDENTITY_LINKED,
    MEMBERSHIP_OBSERVED,
    OBSERVATION_RECORDED,
)


def _ctx(**kwargs):  # type: ignore[no-untyped-def]
    defaults = {
        "tenant_id": uuid4(),
        "correlation_id": uuid4(),
        "evidence_ref": "ev-ref-123",
        "occurred_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return defaults


class TestWhatsAppTranslator:
    def test_event_count(self) -> None:
        payload = WhatsAppGroupPayload(
            group_name="Test Group",
            participants=[
                WhatsAppParticipant(display_name="Alice"),
                WhatsAppParticipant(display_name="Bob"),
                WhatsAppParticipant(display_name="Charlie"),
            ],
        )
        events = translate_whatsapp_group(payload, **_ctx())
        # 1 group + 3 participants x 3 events each = 10
        assert len(events) == 10

    def test_group_event_first(self) -> None:
        payload = WhatsAppGroupPayload(
            group_name="G1",
            participants=[WhatsAppParticipant(display_name="A")],
        )
        events = translate_whatsapp_group(payload, **_ctx())
        assert events[0].event_type == GROUP_IMPORTED

    def test_per_participant_event_types(self) -> None:
        payload = WhatsAppGroupPayload(
            group_name="G1",
            participants=[WhatsAppParticipant(display_name="A")],
        )
        events = translate_whatsapp_group(payload, **_ctx())
        # After group event: identity, membership, fact
        assert events[1].event_type == IDENTITY_LINKED
        assert events[2].event_type == MEMBERSHIP_OBSERVED
        assert events[3].event_type == FACT_RECORDED

    def test_shared_correlation_id(self) -> None:
        cid = uuid4()
        payload = WhatsAppGroupPayload(
            group_name="G1",
            participants=[WhatsAppParticipant(display_name="A")],
        )
        events = translate_whatsapp_group(payload, **_ctx(correlation_id=cid))
        for event in events:
            assert event.correlation_id == cid

    def test_unique_message_ids(self) -> None:
        payload = WhatsAppGroupPayload(
            group_name="G1",
            participants=[WhatsAppParticipant(display_name="A")],
        )
        events = translate_whatsapp_group(payload, **_ctx())
        ids = [e.message_id for e in events]
        assert len(set(ids)) == len(ids)

    def test_causation_chain(self) -> None:
        payload = WhatsAppGroupPayload(
            group_name="G1",
            participants=[WhatsAppParticipant(display_name="A")],
        )
        events = translate_whatsapp_group(payload, **_ctx())
        group_id = events[0].message_id
        # All participant events reference group event
        for event in events[1:]:
            assert event.causation_id == group_id

    def test_evidence_ref_propagation(self) -> None:
        ref = "ev-ref-abc"
        payload = WhatsAppGroupPayload(
            group_name="G1",
            participants=[WhatsAppParticipant(display_name="A")],
        )
        events = translate_whatsapp_group(payload, **_ctx(evidence_ref=ref))
        for event in events:
            assert event.evidence_ref == ref

    def test_producer(self) -> None:
        payload = WhatsAppGroupPayload(
            group_name="G1",
            participants=[WhatsAppParticipant(display_name="A")],
        )
        events = translate_whatsapp_group(payload, **_ctx())
        for event in events:
            assert event.producer == "pinpal.translator.whatsapp"

    def test_group_payload_content(self) -> None:
        payload = WhatsAppGroupPayload(
            group_name="Family Chat",
            participants=[
                WhatsAppParticipant(display_name="Alice"),
                WhatsAppParticipant(display_name="Bob"),
            ],
        )
        events = translate_whatsapp_group(payload, **_ctx())
        group_event = events[0]
        assert group_event.payload["group_name"] == "Family Chat"
        assert group_event.payload["participant_count"] == 2


class TestInstagramTranslator:
    def test_event_count(self) -> None:
        payload = InstagramFollowsPayload(
            follows=[
                InstagramFollowEntry(username="alice"),
                InstagramFollowEntry(username="bob"),
            ],
        )
        events = translate_instagram_follows(payload, **_ctx())
        # 2 follows x 2 events each = 4
        assert len(events) == 4

    def test_event_types(self) -> None:
        payload = InstagramFollowsPayload(
            follows=[InstagramFollowEntry(username="alice")],
        )
        events = translate_instagram_follows(payload, **_ctx())
        assert events[0].event_type == IDENTITY_LINKED
        assert events[1].event_type == FACT_RECORDED

    def test_visibility_defaults(self) -> None:
        payload = InstagramFollowsPayload(
            follows=[InstagramFollowEntry(username="alice")],
        )
        events = translate_instagram_follows(payload, **_ctx())
        for event in events:
            assert event.visibility == Visibility.PRIVATE

    def test_payload_contents(self) -> None:
        payload = InstagramFollowsPayload(
            follows=[InstagramFollowEntry(username="alice_ig", display_name="Alice")],
        )
        events = translate_instagram_follows(payload, **_ctx())
        identity_event = events[0]
        assert identity_event.payload["handle"] == "alice_ig"
        assert identity_event.payload["display_name"] == "Alice"
        assert identity_event.payload["source_type"] == "instagram"

    def test_display_name_fallback(self) -> None:
        payload = InstagramFollowsPayload(
            follows=[InstagramFollowEntry(username="bob")],
        )
        events = translate_instagram_follows(payload, **_ctx())
        assert events[0].payload["display_name"] == "bob"

    def test_producer(self) -> None:
        payload = InstagramFollowsPayload(
            follows=[InstagramFollowEntry(username="alice")],
        )
        events = translate_instagram_follows(payload, **_ctx())
        for event in events:
            assert event.producer == "pinpal.translator.instagram"


class TestManualTranslator:
    def test_exactly_two_events(self) -> None:
        payload = ManualObservationPayload(
            person_display_name="Charlie",
            body="Met at conference",
        )
        events = translate_manual_observation(payload, **_ctx())
        assert len(events) == 2

    def test_event_types(self) -> None:
        payload = ManualObservationPayload(
            person_display_name="Charlie",
            body="Some note",
        )
        events = translate_manual_observation(payload, **_ctx())
        assert events[0].event_type == OBSERVATION_RECORDED
        assert events[1].event_type == FACT_RECORDED

    def test_visibility_always_private(self) -> None:
        payload = ManualObservationPayload(
            person_display_name="Charlie",
            body="Note",
            visibility=Visibility.FRIENDS,  # should be overridden
        )
        events = translate_manual_observation(payload, **_ctx())
        for event in events:
            assert event.visibility == Visibility.PRIVATE

    def test_person_id_propagation(self) -> None:
        pid = uuid4()
        payload = ManualObservationPayload(
            person_display_name="Charlie",
            person_id=pid,
            body="Note",
        )
        events = translate_manual_observation(payload, **_ctx())
        for event in events:
            assert event.payload.get("person_id") == str(pid)

    def test_no_person_id(self) -> None:
        payload = ManualObservationPayload(
            person_display_name="Charlie",
            body="Note",
        )
        events = translate_manual_observation(payload, **_ctx())
        assert events[0].payload["person_id"] is None

    def test_producer(self) -> None:
        payload = ManualObservationPayload(
            person_display_name="Charlie",
            body="Note",
        )
        events = translate_manual_observation(payload, **_ctx())
        for event in events:
            assert event.producer == "pinpal.translator.manual"
