"""Pydantic v2 schemas for MongoDB collections."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from pinpal.db.enums import SourceType, TimelineEventType, Visibility

# ---- raw_payloads ----


class RawPayloadCreate(BaseModel):
    owner_user_id: str
    source_type: SourceType
    payload: dict[str, Any]
    content_hash: str


class RawPayloadRead(BaseModel):
    id: str
    owner_user_id: str
    source_type: SourceType
    payload: dict[str, Any]
    content_hash: str
    created_at: datetime


# ---- observations ----


class ObservationCreate(BaseModel):
    owner_user_id: str
    source_type: SourceType
    subject_person_id: str | None = None
    body: str
    visibility: Visibility = Visibility.PRIVATE
    version: int = 1
    supersedes: str | None = None


class ObservationRead(BaseModel):
    id: str
    owner_user_id: str
    source_type: SourceType
    subject_person_id: str | None
    body: str
    visibility: Visibility
    version: int
    supersedes: str | None
    created_at: datetime


# ---- evidence_bundles ----


class EvidenceBundleCreate(BaseModel):
    owner_user_id: str
    person_id: str
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    fact_ids: list[str] = Field(default_factory=list)


class EvidenceBundleRead(BaseModel):
    id: str
    owner_user_id: str
    person_id: str
    summary: str
    evidence_ids: list[str]
    fact_ids: list[str]
    assembled_at: datetime
    created_at: datetime


# ---- timeline_events ----


class TimelineEventRefsCreate(BaseModel):
    evidence_id: str | None = None
    fact_id: str | None = None
    person_id: str | None = None
    group_id: str | None = None
    relationship_id: str | None = None


class TimelineEventRefsRead(BaseModel):
    evidence_id: str | None = None
    fact_id: str | None = None
    person_id: str | None = None
    group_id: str | None = None
    relationship_id: str | None = None


class TimelineEventCreate(BaseModel):
    owner_user_id: str
    event_type: TimelineEventType
    summary: str
    occurred_at: datetime
    refs: TimelineEventRefsCreate = Field(default_factory=TimelineEventRefsCreate)


class TimelineEventRead(BaseModel):
    id: str
    owner_user_id: str
    event_type: TimelineEventType
    summary: str
    occurred_at: datetime
    refs: TimelineEventRefsRead
    created_at: datetime
