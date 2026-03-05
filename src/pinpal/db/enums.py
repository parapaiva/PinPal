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
