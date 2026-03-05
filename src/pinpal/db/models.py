"""SQLAlchemy ORM models for the PinPal core graph."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pinpal.db.base import Base
from pinpal.db.enums import (
    GroupType,
    RelationshipStatus,
    RelationshipType,
    SharingMode,
    SourceAccountStatus,
    SourceType,
    Visibility,
)


class TimestampMixin:
    """Mixin that adds created_at / updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)

    source_accounts: Mapped[list["SourceAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    persons: Mapped[list["Person"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    groups: Mapped[list["Group"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class SourceAccount(TimestampMixin, Base):
    __tablename__ = "source_accounts"
    __table_args__ = (UniqueConstraint("user_id", "source_type", "external_account_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    external_account_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[SourceAccountStatus] = mapped_column(
        Enum(SourceAccountStatus), nullable=False, default=SourceAccountStatus.ACTIVE
    )
    sharing_mode: Mapped[SharingMode] = mapped_column(
        Enum(SharingMode), nullable=False, default=SharingMode.PRIVATE
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="source_accounts")


class Person(TimestampMixin, Base):
    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)

    owner: Mapped["User"] = relationship(back_populates="persons")
    identities: Mapped[list["Identity"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )


class Identity(TimestampMixin, Base):
    __tablename__ = "identities"
    __table_args__ = (
        UniqueConstraint("person_id", "source_type", "external_id"),
        Index(
            "ix_identities_source_external",
            "source_type",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    handle: Mapped[str | None] = mapped_column(String(200), nullable=True)

    person: Mapped["Person"] = relationship(back_populates="identities")


class Group(TimestampMixin, Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    group_type: Mapped[GroupType] = mapped_column(Enum(GroupType), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility), nullable=False, default=Visibility.PRIVATE
    )

    owner: Mapped["User"] = relationship(back_populates="groups")
    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class Membership(TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("group_id", "person_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    evidence_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)

    group: Mapped["Group"] = relationship(back_populates="memberships")
    person: Mapped["Person"] = relationship(back_populates="memberships")


class Relationship(TimestampMixin, Base):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint("person_a_id", "person_b_id", "relationship_type"),
        CheckConstraint("person_a_id < person_b_id", name="ck_relationship_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_a_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    person_b_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType), nullable=False
    )
    status: Mapped[RelationshipStatus] = mapped_column(
        Enum(RelationshipStatus), nullable=False, default=RelationshipStatus.SUGGESTED
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    why_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)

    person_a: Mapped["Person"] = relationship(foreign_keys=[person_a_id])
    person_b: Mapped["Person"] = relationship(foreign_keys=[person_b_id])
