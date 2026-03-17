"""002 facts

Revision ID: 002_facts
Revises: 001_core_graph
Create Date: 2026-03-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_facts"
down_revision: str | None = "001_core_graph"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# New enum types
facttype = postgresql.ENUM(
    "membership_observed",
    "follow_observed",
    "identity_linked",
    "manual_note",
    name="facttype",
    create_type=False,
)
factstatus = postgresql.ENUM(
    "active",
    "retracted",
    name="factstatus",
    create_type=False,
)

# Reuse existing enum types from 001
sourcetype = postgresql.ENUM(name="sourcetype", create_type=False)
visibility = postgresql.ENUM(name="visibility", create_type=False)


def upgrade() -> None:
    # Create new enum types
    facttype.create(op.get_bind(), checkfirst=True)
    factstatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "facts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "owner_user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fact_type", facttype, nullable=False),
        sa.Column("source_type", sourcetype, nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("visibility", visibility, nullable=False),
        sa.Column("evidence_ref", sa.String(500), nullable=True),
        sa.Column(
            "person_id",
            sa.UUID(),
            sa.ForeignKey("persons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "group_id",
            sa.UUID(),
            sa.ForeignKey("groups.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "relationship_id",
            sa.UUID(),
            sa.ForeignKey("relationships.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", factstatus, nullable=False),
        sa.Column("retracted_at", sa.DateTime(timezone=True), nullable=True),
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

    op.create_index("ix_facts_owner_status", "facts", ["owner_user_id", "status"])
    op.create_index("ix_facts_owner_fact_type", "facts", ["owner_user_id", "fact_type"])
    op.create_index("ix_facts_person_id", "facts", ["person_id"])
    op.create_index("ix_facts_evidence_ref", "facts", ["evidence_ref"])


def downgrade() -> None:
    op.drop_index("ix_facts_evidence_ref", table_name="facts")
    op.drop_index("ix_facts_person_id", table_name="facts")
    op.drop_index("ix_facts_owner_fact_type", table_name="facts")
    op.drop_index("ix_facts_owner_status", table_name="facts")
    op.drop_table("facts")

    factstatus.drop(op.get_bind(), checkfirst=True)
    facttype.drop(op.get_bind(), checkfirst=True)
