"""Translator: Manual observation → canonical events."""

from datetime import datetime
from uuid import UUID

from pinpal.api.schemas import ManualObservationPayload
from pinpal.db.enums import Visibility
from pinpal.events.envelope import CanonicalEvent
from pinpal.events.types import FACT_RECORDED, OBSERVATION_RECORDED

PRODUCER = "pinpal.translator.manual"


def translate_manual_observation(
    payload: ManualObservationPayload,
    *,
    tenant_id: UUID,
    correlation_id: UUID,
    evidence_ref: str | None = None,
    occurred_at: datetime,
) -> list[CanonicalEvent]:
    """Convert a manual observation into canonical events.

    Always emits: observation.recorded + fact.recorded (manual_note).
    Visibility is always PRIVATE.
    """
    person_id_str = str(payload.person_id) if payload.person_id else None

    observation_event = CanonicalEvent(
        correlation_id=correlation_id,
        causation_id=correlation_id,
        tenant_id=tenant_id,
        producer=PRODUCER,
        event_type=OBSERVATION_RECORDED,
        occurred_at=occurred_at,
        visibility=Visibility.PRIVATE,
        payload={
            "person_display_name": payload.person_display_name,
            "person_id": person_id_str,
            "body": payload.body,
            "source_type": "manual",
        },
        evidence_ref=evidence_ref,
    )

    fact_event = CanonicalEvent(
        correlation_id=correlation_id,
        causation_id=correlation_id,
        tenant_id=tenant_id,
        producer=PRODUCER,
        event_type=FACT_RECORDED,
        occurred_at=occurred_at,
        visibility=Visibility.PRIVATE,
        payload={
            "fact_type": "manual_note",
            "display_name": payload.person_display_name,
            "person_id": person_id_str,
            "body": payload.body,
            "source_type": "manual",
        },
        evidence_ref=evidence_ref,
    )

    return [observation_event, fact_event]
