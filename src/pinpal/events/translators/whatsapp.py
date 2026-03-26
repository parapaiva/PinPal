"""Translator: WhatsApp group export → canonical events."""

from datetime import datetime
from uuid import UUID, uuid4

from pinpal.api.schemas import WhatsAppGroupPayload
from pinpal.db.enums import Visibility
from pinpal.events.envelope import CanonicalEvent
from pinpal.events.types import FACT_RECORDED, GROUP_IMPORTED, IDENTITY_LINKED, MEMBERSHIP_OBSERVED

PRODUCER = "pinpal.translator.whatsapp"


def translate_whatsapp_group(
    payload: WhatsAppGroupPayload,
    *,
    tenant_id: UUID,
    correlation_id: UUID,
    evidence_ref: str | None = None,
    occurred_at: datetime,
    visibility: Visibility = Visibility.PRIVATE,
) -> list[CanonicalEvent]:
    """Convert a WhatsApp group payload into ordered canonical events.

    Order: 1x group.imported, then per participant: identity.linked,
    membership.observed, fact.recorded.
    """
    events: list[CanonicalEvent] = []
    group_message_id = uuid4()

    # 1. Group imported event
    events.append(
        CanonicalEvent(
            message_id=group_message_id,
            correlation_id=correlation_id,
            causation_id=correlation_id,
            tenant_id=tenant_id,
            producer=PRODUCER,
            event_type=GROUP_IMPORTED,
            occurred_at=occurred_at,
            visibility=visibility,
            payload={
                "group_name": payload.group_name,
                "group_type": "whatsapp_group",
                "participant_count": len(payload.participants),
            },
            evidence_ref=evidence_ref,
        )
    )

    # 2. Per-participant events
    for participant in payload.participants:
        events.append(
            CanonicalEvent(
                correlation_id=correlation_id,
                causation_id=group_message_id,
                tenant_id=tenant_id,
                producer=PRODUCER,
                event_type=IDENTITY_LINKED,
                occurred_at=occurred_at,
                visibility=visibility,
                payload={
                    "display_name": participant.display_name,
                    "source_type": "whatsapp",
                    "handle": participant.handle,
                    "phone_number": participant.phone_number,
                    "external_id": participant.phone_number or participant.handle,
                },
                evidence_ref=evidence_ref,
            )
        )
        events.append(
            CanonicalEvent(
                correlation_id=correlation_id,
                causation_id=group_message_id,
                tenant_id=tenant_id,
                producer=PRODUCER,
                event_type=MEMBERSHIP_OBSERVED,
                occurred_at=occurred_at,
                visibility=visibility,
                payload={
                    "display_name": participant.display_name,
                    "group_name": payload.group_name,
                },
                evidence_ref=evidence_ref,
            )
        )
        events.append(
            CanonicalEvent(
                correlation_id=correlation_id,
                causation_id=group_message_id,
                tenant_id=tenant_id,
                producer=PRODUCER,
                event_type=FACT_RECORDED,
                occurred_at=occurred_at,
                visibility=visibility,
                payload={
                    "fact_type": "membership_observed",
                    "display_name": participant.display_name,
                    "group_name": payload.group_name,
                    "source_type": "whatsapp",
                },
                evidence_ref=evidence_ref,
            )
        )

    return events
