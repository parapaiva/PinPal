"""001 core graph

Revision ID: 001_core_graph
Revises:
Create Date: 2026-03-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_core_graph"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Enum types
sourcetype = postgresql.ENUM(
    "whatsapp", "instagram", "linkedin", "manual", name="sourcetype", create_type=False
)
visibility = postgresql.ENUM(
    "private", "friends", "sensitive", name="visibility", create_type=False
)
sharingmode = postgresql.ENUM("private", "friends", name="sharingmode", create_type=False)
relationshiptype = postgresql.ENUM(
    "co_member", "follow", "manual", "inferred", name="relationshiptype", create_type=False
)
relationshipstatus = postgresql.ENUM(
    "suggested", "confirmed", "revoked", name="relationshipstatus", create_type=False
)
grouptype = postgresql.ENUM(
    "whatsapp_group",
    "instagram_circle",
    "event",
    "cohort",
    "custom",
    name="grouptype",
    create_type=False,
)
sourceaccountstatus = postgresql.ENUM(
    "active", "revoked", name="sourceaccountstatus", create_type=False
)


def upgrade() -> None:
    # Create enum types
    sourcetype.create(op.get_bind(), checkfirst=True)
    visibility.create(op.get_bind(), checkfirst=True)
    sharingmode.create(op.get_bind(), checkfirst=True)
    relationshiptype.create(op.get_bind(), checkfirst=True)
    relationshipstatus.create(op.get_bind(), checkfirst=True)
    grouptype.create(op.get_bind(), checkfirst=True)
    sourceaccountstatus.create(op.get_bind(), checkfirst=True)

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- source_accounts ---
    op.create_table(
        "source_accounts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("source_type", sourcetype, nullable=False),
        sa.Column("external_account_id", sa.String(500), nullable=True),
        sa.Column("status", sourceaccountstatus, nullable=False),
        sa.Column("sharing_mode", sharingmode, nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "source_type", "external_account_id"),
    )

    # --- persons ---
    op.create_table(
        "persons",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "owner_user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- identities ---
    op.create_table(
        "identities",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "person_id",
            sa.UUID(),
            sa.ForeignKey("persons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sourcetype, nullable=False),
        sa.Column("external_id", sa.String(500), nullable=True),
        sa.Column("handle", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("person_id", "source_type", "external_id"),
    )
    op.create_index(
        "ix_identities_source_external",
        "identities",
        ["source_type", "external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
    )

    # --- groups ---
    op.create_table(
        "groups",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "owner_user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("group_type", grouptype, nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("visibility", visibility, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- memberships ---
    op.create_table(
        "memberships",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "group_id",
            sa.UUID(),
            sa.ForeignKey("groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "person_id",
            sa.UUID(),
            sa.ForeignKey("persons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("evidence_ref", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("group_id", "person_id"),
    )

    # --- relationships ---
    op.create_table(
        "relationships",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "person_a_id",
            sa.UUID(),
            sa.ForeignKey("persons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "person_b_id",
            sa.UUID(),
            sa.ForeignKey("persons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relationship_type", relationshiptype, nullable=False),
        sa.Column("status", relationshipstatus, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("why_ref", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("person_a_id", "person_b_id", "relationship_type"),
        sa.CheckConstraint("person_a_id < person_b_id", name="ck_relationship_order"),
    )


def downgrade() -> None:
    op.drop_table("relationships")
    op.drop_table("memberships")
    op.drop_table("groups")
    op.drop_index("ix_identities_source_external", table_name="identities")
    op.drop_table("identities")
    op.drop_table("persons")
    op.drop_table("source_accounts")
    op.drop_table("users")

    # Drop enum types
    sourceaccountstatus.drop(op.get_bind(), checkfirst=True)
    grouptype.drop(op.get_bind(), checkfirst=True)
    relationshipstatus.drop(op.get_bind(), checkfirst=True)
    relationshiptype.drop(op.get_bind(), checkfirst=True)
    sharingmode.drop(op.get_bind(), checkfirst=True)
    visibility.drop(op.get_bind(), checkfirst=True)
    sourcetype.drop(op.get_bind(), checkfirst=True)
