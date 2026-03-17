"""Domain services for the PinPal core graph."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from pinpal.db.enums import FactStatus, RelationshipStatus
from pinpal.db.models import Fact, Group, Identity, Membership, Person, Relationship


@dataclass
class WhyReason:
    reason_type: str
    summary: str
    confidence: float | None = None
    group_id: UUID | None = None
    relationship_id: UUID | None = None
    identity_id: UUID | None = None
    first_seen_at: datetime | None = None
    evidence_ref: str | None = None
    fact_id: UUID | None = None


@dataclass
class WhyResult:
    person_id: UUID
    display_name: str
    reasons: list[WhyReason]


class WhyDoIKnowService:
    """Walks the core graph to produce ranked 'why do I know this person?' reasons."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def why(self, owner_user_id: UUID, person_id: UUID) -> WhyResult:
        person = await self._session.get(Person, person_id)
        if person is None or person.owner_user_id != owner_user_id:
            return WhyResult(person_id=person_id, display_name="Unknown", reasons=[])

        reasons: list[WhyReason] = []

        # 1. Shared groups
        stmt = (
            select(Membership, Group)
            .join(Group, Membership.group_id == Group.id)
            .where(
                Membership.person_id == person_id,
                Group.owner_user_id == owner_user_id,
            )
        )
        result = await self._session.execute(stmt)
        for membership, group in result.all():
            reasons.append(
                WhyReason(
                    reason_type="shared_group",
                    summary=f"Member of '{group.name}' {group.group_type.value.replace('_', ' ')}",
                    confidence=None,
                    group_id=group.id,
                    first_seen_at=membership.first_seen_at,
                    evidence_ref=membership.evidence_ref,
                )
            )

        # 2. Direct relationships (non-REVOKED)
        stmt_rel = select(Relationship).where(
            or_(
                Relationship.person_a_id == person_id,
                Relationship.person_b_id == person_id,
            ),
            Relationship.status != RelationshipStatus.REVOKED,
        )
        result_rel = await self._session.execute(stmt_rel)
        for rel in result_rel.scalars().all():
            # Verify the other person is also owned by this user
            other_id = rel.person_b_id if rel.person_a_id == person_id else rel.person_a_id
            other = await self._session.get(Person, other_id)
            if other is None or other.owner_user_id != owner_user_id:
                continue
            reasons.append(
                WhyReason(
                    reason_type="direct_relationship",
                    summary=(
                        f"{rel.relationship_type.value.replace('_', ' ').title()} "
                        f"relationship with {other.display_name}"
                    ),
                    confidence=rel.confidence,
                    relationship_id=rel.id,
                    first_seen_at=rel.first_seen_at,
                    evidence_ref=None,
                )
            )

        # 3. Identity sources
        stmt_id = select(Identity).where(Identity.person_id == person_id)
        result_id = await self._session.execute(stmt_id)
        for identity in result_id.scalars().all():
            handle_part = f" ({identity.handle})" if identity.handle else ""
            reasons.append(
                WhyReason(
                    reason_type="identity_source",
                    summary=f"Known on {identity.source_type.value}{handle_part}",
                    confidence=None,
                    identity_id=identity.id,
                    first_seen_at=identity.created_at,
                    evidence_ref=None,
                )
            )

        # 4. Active facts linked to this person
        stmt_facts = select(Fact).where(
            Fact.owner_user_id == owner_user_id,
            Fact.person_id == person_id,
            Fact.status == FactStatus.ACTIVE,
        )
        result_facts = await self._session.execute(stmt_facts)
        for fact in result_facts.scalars().all():
            reasons.append(
                WhyReason(
                    reason_type="recorded_fact",
                    summary=(
                        f"{fact.fact_type.value.replace('_', ' ').title()} "
                        f"from {fact.source_type.value}"
                    ),
                    confidence=fact.confidence,
                    first_seen_at=fact.observed_at,
                    evidence_ref=fact.evidence_ref,
                    fact_id=fact.id,
                )
            )

        # Sort: confidence desc (None last), then first_seen_at asc (None last)
        reasons.sort(
            key=lambda r: (
                -(r.confidence if r.confidence is not None else -1),
                r.first_seen_at or datetime.max,
            )
        )

        return WhyResult(
            person_id=person_id,
            display_name=person.display_name,
            reasons=reasons,
        )
