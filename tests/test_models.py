"""Unit tests for ORM models and enums."""

from pinpal.db.enums import (
    GroupType,
    RelationshipStatus,
    RelationshipType,
    SharingMode,
    SourceAccountStatus,
    SourceType,
    Visibility,
)
from pinpal.db.models import (
    Group,
    Identity,
    Membership,
    Person,
    Relationship,
    SourceAccount,
    User,
)

# ---- Enum values ----


def test_source_type_values() -> None:
    assert [e.value for e in SourceType] == ["whatsapp", "instagram", "linkedin", "manual"]


def test_visibility_values() -> None:
    assert [e.value for e in Visibility] == ["private", "friends", "sensitive"]


def test_sharing_mode_values() -> None:
    assert [e.value for e in SharingMode] == ["private", "friends"]


def test_relationship_type_values() -> None:
    assert [e.value for e in RelationshipType] == ["co_member", "follow", "manual", "inferred"]


def test_relationship_status_values() -> None:
    assert [e.value for e in RelationshipStatus] == ["suggested", "confirmed", "revoked"]


def test_group_type_values() -> None:
    assert [e.value for e in GroupType] == [
        "whatsapp_group",
        "instagram_circle",
        "event",
        "cohort",
        "custom",
    ]


def test_source_account_status_values() -> None:
    assert [e.value for e in SourceAccountStatus] == ["active", "revoked"]


# ---- Table names ----


def test_user_tablename() -> None:
    assert User.__tablename__ == "users"


def test_source_account_tablename() -> None:
    assert SourceAccount.__tablename__ == "source_accounts"


def test_person_tablename() -> None:
    assert Person.__tablename__ == "persons"


def test_identity_tablename() -> None:
    assert Identity.__tablename__ == "identities"


def test_group_tablename() -> None:
    assert Group.__tablename__ == "groups"


def test_membership_tablename() -> None:
    assert Membership.__tablename__ == "memberships"


def test_relationship_tablename() -> None:
    assert Relationship.__tablename__ == "relationships"


# ---- Column introspection ----


def test_user_columns() -> None:
    cols = {c.name for c in User.__table__.columns}
    assert cols == {"id", "email", "display_name", "created_at", "updated_at"}


def test_person_columns() -> None:
    cols = {c.name for c in Person.__table__.columns}
    assert cols == {"id", "owner_user_id", "display_name", "created_at", "updated_at"}


def test_relationship_columns() -> None:
    cols = {c.name for c in Relationship.__table__.columns}
    assert cols == {
        "id",
        "person_a_id",
        "person_b_id",
        "relationship_type",
        "status",
        "confidence",
        "first_seen_at",
        "last_seen_at",
        "why_ref",
        "created_at",
        "updated_at",
    }


def test_membership_columns() -> None:
    cols = {c.name for c in Membership.__table__.columns}
    assert cols == {
        "id",
        "group_id",
        "person_id",
        "first_seen_at",
        "last_seen_at",
        "evidence_ref",
        "created_at",
        "updated_at",
    }


# ---- Enum serialization ----


def test_enums_serialize_as_strings() -> None:
    """StrEnum members serialize to their string values."""
    assert str(SourceType.WHATSAPP) == "whatsapp"
    assert SourceType.WHATSAPP.value == "whatsapp"
    assert f"{SourceType.WHATSAPP}" == "whatsapp"
