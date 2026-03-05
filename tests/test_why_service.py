"""Integration tests for WhyDoIKnowService."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from pinpal.core.services import WhyDoIKnowService
from pinpal.db.enums import GroupType, RelationshipType, SourceType
from tests.conftest import (
    create_test_group,
    create_test_identity,
    create_test_membership,
    create_test_person,
    create_test_relationship,
    create_test_user,
)


@pytest.mark.integration
async def test_why_returns_empty_for_unknown_person(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = WhyDoIKnowService(db_session)
    result = await service.why(user.id, uuid.uuid4())
    assert result.display_name == "Unknown"
    assert result.reasons == []


@pytest.mark.integration
async def test_why_returns_shared_group(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    person = await create_test_person(db_session, user, "Alice")
    group = await create_test_group(db_session, user, "College Friends", GroupType.WHATSAPP_GROUP)
    await create_test_membership(db_session, group, person)
    await db_session.commit()

    service = WhyDoIKnowService(db_session)
    result = await service.why(user.id, person.id)
    assert result.display_name == "Alice"
    assert len(result.reasons) == 1
    reason = result.reasons[0]
    assert reason.reason_type == "shared_group"
    assert "College Friends" in reason.summary
    assert reason.group_id == group.id


@pytest.mark.integration
async def test_why_returns_direct_relationship(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    person_a = await create_test_person(db_session, user, "Bob")
    person_b = await create_test_person(db_session, user, "Carol")
    rel = await create_test_relationship(
        db_session, person_a, person_b, RelationshipType.MANUAL, 0.9
    )
    await db_session.commit()

    service = WhyDoIKnowService(db_session)
    result = await service.why(user.id, person_a.id)
    assert any(r.reason_type == "direct_relationship" for r in result.reasons)
    rel_reason = next(r for r in result.reasons if r.reason_type == "direct_relationship")
    assert rel_reason.confidence == 0.9
    assert rel_reason.relationship_id == rel.id


@pytest.mark.integration
async def test_why_returns_identity_source(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    person = await create_test_person(db_session, user, "Dave")
    identity = await create_test_identity(db_session, person, SourceType.INSTAGRAM, "@dave")
    await db_session.commit()

    service = WhyDoIKnowService(db_session)
    result = await service.why(user.id, person.id)
    assert any(r.reason_type == "identity_source" for r in result.reasons)
    id_reason = next(r for r in result.reasons if r.reason_type == "identity_source")
    assert "instagram" in id_reason.summary
    assert "@dave" in id_reason.summary
    assert id_reason.identity_id == identity.id


@pytest.mark.integration
async def test_why_sorts_by_confidence_then_first_seen(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    person = await create_test_person(db_session, user, "Eve")
    other = await create_test_person(db_session, user, "Frank")

    # Create a relationship (has confidence)
    await create_test_relationship(db_session, person, other, confidence=0.7)
    # Create a group membership (no confidence)
    group = await create_test_group(db_session, user, "Work")
    await create_test_membership(db_session, group, person)
    # Create an identity (no confidence)
    await create_test_identity(db_session, person, SourceType.LINKEDIN)
    await db_session.commit()

    service = WhyDoIKnowService(db_session)
    result = await service.why(user.id, person.id)
    assert len(result.reasons) == 3
    # Relationship (confidence 0.7) should be first
    assert result.reasons[0].reason_type == "direct_relationship"


@pytest.mark.integration
async def test_why_excludes_other_users_data(db_session: AsyncSession) -> None:
    user1 = await create_test_user(db_session)
    user2 = await create_test_user(db_session)
    person = await create_test_person(db_session, user1, "Grace")
    # Group owned by user2 should not appear
    group = await create_test_group(db_session, user2, "Not Mine")
    await db_session.commit()

    service = WhyDoIKnowService(db_session)
    result = await service.why(user1.id, person.id)
    assert all(r.group_id != group.id for r in result.reasons)
