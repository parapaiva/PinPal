"""Canonical event envelope — the unit of exchange in the ingestion pipeline."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pinpal.db.enums import Visibility


class CanonicalEvent(BaseModel):
    """Immutable event envelope following the CloudEvents-inspired schema.

    Every source translator emits a list of these; every handler consumes one.
    """

    message_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID
    causation_id: UUID
    tenant_id: UUID
    producer: str
    event_type: str
    event_version: int = 1
    occurred_at: datetime
    visibility: Visibility = Visibility.PRIVATE
    payload: dict = Field(default_factory=dict)  # type: ignore[type-arg]
    evidence_ref: str | None = None
