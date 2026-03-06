"""Domain enums for the PinPal core graph."""

import enum


class SourceType(enum.StrEnum):
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    MANUAL = "manual"


class Visibility(enum.StrEnum):
    PRIVATE = "private"
    FRIENDS = "friends"
    SENSITIVE = "sensitive"


class SharingMode(enum.StrEnum):
    PRIVATE = "private"
    FRIENDS = "friends"


class RelationshipType(enum.StrEnum):
    CO_MEMBER = "co_member"
    FOLLOW = "follow"
    MANUAL = "manual"
    INFERRED = "inferred"


class RelationshipStatus(enum.StrEnum):
    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"
    REVOKED = "revoked"


class GroupType(enum.StrEnum):
    WHATSAPP_GROUP = "whatsapp_group"
    INSTAGRAM_CIRCLE = "instagram_circle"
    EVENT = "event"
    COHORT = "cohort"
    CUSTOM = "custom"


class SourceAccountStatus(enum.StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"


class FactType(enum.StrEnum):
    MEMBERSHIP_OBSERVED = "membership_observed"
    FOLLOW_OBSERVED = "follow_observed"
    IDENTITY_LINKED = "identity_linked"
    MANUAL_NOTE = "manual_note"


class FactStatus(enum.StrEnum):
    ACTIVE = "active"
    RETRACTED = "retracted"


class TimelineEventType(enum.StrEnum):
    EVIDENCE_ADDED = "evidence_added"
    FACT_RECORDED = "fact_recorded"
    FACT_RETRACTED = "fact_retracted"
    MEMBERSHIP_OBSERVED = "membership_observed"
    RELATIONSHIP_SUGGESTED = "relationship_suggested"
    RELATIONSHIP_CONFIRMED = "relationship_confirmed"
    IDENTITY_LINKED = "identity_linked"
