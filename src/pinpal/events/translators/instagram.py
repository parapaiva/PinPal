"""Translator: Instagram follows export → canonical events."""

from datetime import datetime
from uuid import UUID

from pinpal.api.schemas import InstagramFollowsPayload
from pinpal.db.enums import Visibility
from pinpal.events.envelope import CanonicalEvent
from pinpal.events.types import FACT_RECORDED, IDENTITY_LINKED

PRODUCER = "pinpal.translator.instagram"


def translate_instagram_follows(
    payload: InstagramFollowsPayload,
    *,
    tenant_id: UUID,
    correlation_id: UUID,
    evidence_ref: str | None = None,
    occurred_at: datetime,
    visibility: Visibility = Visibility.PRIVATE,
) -> list[CanonicalEvent]:
    """Convert Instagram follows into canonical events.

    Per follow entry: identity.linked + fact.recorded (follow_observed).
    """
    events: list[CanonicalEvent] = []

    for entry in payload.follows:
        display_name = entry.display_name or entry.username

        events.append(
            CanonicalEvent(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                tenant_id=tenant_id,
                producer=PRODUCER,
                event_type=IDENTITY_LINKED,
                occurred_at=occurred_at,
                visibility=visibility,
                payload={
                    "display_name": display_name,
                    "source_type": "instagram",
                    "handle": entry.username,
                    "external_id": entry.username,
                },
                evidence_ref=evidence_ref,
            )
        )
        events.append(
            CanonicalEvent(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                tenant_id=tenant_id,
                producer=PRODUCER,
                event_type=FACT_RECORDED,
                occurred_at=occurred_at,
                visibility=visibility,
                payload={
                    "fact_type": "follow_observed",
                    "display_name": display_name,
                    "username": entry.username,
                    "source_type": "instagram",
                },
                evidence_ref=evidence_ref,
            )
        )

    return events
