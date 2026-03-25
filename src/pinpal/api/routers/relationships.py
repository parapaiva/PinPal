"""Relationship CRUD + 'Why do I know this person?' endpoint."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from pinpal.api.deps import get_db_session
from pinpal.api.schemas import (
    RelationshipCreate,
    RelationshipRead,
    RelationshipUpdate,
    WhyResultSchema,
)
from pinpal.core.services import WhyDoIKnowService
from pinpal.db.models import Person, Relationship, User

router = APIRouter(prefix="/api/v1/users/{user_id}", tags=["relationships"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def _get_user_or_404(session: AsyncSession, user_id: UUID) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ---- Relationship CRUD ----


@router.post("/relationships", response_model=RelationshipRead, status_code=201)
async def create_relationship(
    user_id: UUID, body: RelationshipCreate, session: DbSession
) -> Relationship:
    await _get_user_or_404(session, user_id)
    for pid in (body.person_a_id, body.person_b_id):
        person = await session.get(Person, pid)
        if person is None or person.owner_user_id != user_id:
            raise HTTPException(status_code=404, detail=f"Person {pid} not found")
    a_id, b_id = sorted([body.person_a_id, body.person_b_id])
    rel = Relationship(
        person_a_id=a_id,
        person_b_id=b_id,
        relationship_type=body.relationship_type,
        confidence=body.confidence,
    )
    session.add(rel)
    await session.flush()
    return rel


@router.get("/relationships", response_model=list[RelationshipRead])
async def list_relationships(user_id: UUID, session: DbSession) -> list[Relationship]:
    await _get_user_or_404(session, user_id)
    person_ids_stmt = select(Person.id).where(Person.owner_user_id == user_id)
    person_ids = (await session.execute(person_ids_stmt)).scalars().all()
    if not person_ids:
        return []
    result = await session.execute(
        select(Relationship).where(
            or_(
                Relationship.person_a_id.in_(person_ids),
                Relationship.person_b_id.in_(person_ids),
            )
        )
    )
    return list(result.scalars().all())


@router.patch("/relationships/{relationship_id}", response_model=RelationshipRead)
async def update_relationship(
    user_id: UUID, relationship_id: UUID, body: RelationshipUpdate, session: DbSession
) -> Relationship:
    await _get_user_or_404(session, user_id)
    rel = await session.get(Relationship, relationship_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    person_a = await session.get(Person, rel.person_a_id)
    if person_a is None or person_a.owner_user_id != user_id:
        raise HTTPException(status_code=404, detail="Relationship not found")
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(rel, field, value)
    await session.flush()
    await session.refresh(rel)
    return rel


# ---- Why endpoint ----


@router.get("/persons/{person_id}/why", response_model=WhyResultSchema)
async def why_do_i_know(user_id: UUID, person_id: UUID, session: DbSession) -> WhyResultSchema:
    await _get_user_or_404(session, user_id)
    service = WhyDoIKnowService(session)
    result = await service.why(owner_user_id=user_id, person_id=person_id)
    return WhyResultSchema(
        person_id=result.person_id,
        display_name=result.display_name,
        reasons=[
            {
                "reason_type": r.reason_type,
                "summary": r.summary,
                "confidence": r.confidence,
                "group_id": r.group_id,
                "relationship_id": r.relationship_id,
                "identity_id": r.identity_id,
                "first_seen_at": r.first_seen_at,
                "evidence_ref": r.evidence_ref,
                "fact_id": r.fact_id,
            }
            for r in result.reasons
        ],
    )
