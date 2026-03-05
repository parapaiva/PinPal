"""Pydantic v2 request/response schemas for the PinPal API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from pinpal.db.enums import (
    GroupType,
    RelationshipStatus,
    RelationshipType,
    SharingMode,
    SourceAccountStatus,
    SourceType,
    Visibility,
)

# ---- User ----


class UserCreate(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=200)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=200)


# ---- SourceAccount ----


class SourceAccountCreate(BaseModel):
    source_type: SourceType
    external_account_id: str | None = None
    sharing_mode: SharingMode = SharingMode.PRIVATE


class SourceAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    source_type: SourceType
    external_account_id: str | None
    status: SourceAccountStatus
    sharing_mode: SharingMode
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime


# ---- Person ----


class PersonCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=200)


class PersonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_user_id: UUID
    display_name: str
    created_at: datetime
    updated_at: datetime


class PersonUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)


# ---- Identity ----


class IdentityCreate(BaseModel):
    source_type: SourceType
    external_id: str | None = None
    handle: str | None = None


class IdentityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    person_id: UUID
    source_type: SourceType
    external_id: str | None
    handle: str | None
    created_at: datetime
    updated_at: datetime


# ---- Group ----


class GroupCreate(BaseModel):
    group_type: GroupType
    name: str = Field(min_length=1, max_length=300)
    visibility: Visibility = Visibility.PRIVATE


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_user_id: UUID
    group_type: GroupType
    name: str
    visibility: Visibility
    created_at: datetime
    updated_at: datetime


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    visibility: Visibility | None = None


# ---- Membership ----


class MembershipCreate(BaseModel):
    person_id: UUID


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group_id: UUID
    person_id: UUID
    first_seen_at: datetime
    last_seen_at: datetime
    evidence_ref: str | None
    created_at: datetime
    updated_at: datetime


# ---- Relationship ----


class RelationshipCreate(BaseModel):
    person_a_id: UUID
    person_b_id: UUID
    relationship_type: RelationshipType
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class RelationshipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    person_a_id: UUID
    person_b_id: UUID
    relationship_type: RelationshipType
    status: RelationshipStatus
    confidence: float
    first_seen_at: datetime
    last_seen_at: datetime
    why_ref: str | None
    created_at: datetime
    updated_at: datetime


class RelationshipUpdate(BaseModel):
    status: RelationshipStatus | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


# ---- WhyDoIKnow ----


class WhyReasonSchema(BaseModel):
    reason_type: str
    summary: str
    confidence: float | None = None
    group_id: UUID | None = None
    relationship_id: UUID | None = None
    identity_id: UUID | None = None
    first_seen_at: datetime | None = None
    evidence_ref: str | None = None


class WhyResultSchema(BaseModel):
    person_id: UUID
    display_name: str
    reasons: list[WhyReasonSchema]
