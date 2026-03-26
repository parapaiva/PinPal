"""Fact CRUD endpoints (Postgres)."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pinpal.api.deps import get_db_session
from pinpal.api.schemas import FactCreate, FactRead, FactUpdate
from pinpal.db.enums import FactStatus, FactType, SourceType
from pinpal.db.models import Fact, User

router = APIRouter(prefix="/api/v1/users/{user_id}/facts", tags=["facts"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def _get_user_or_404(session: AsyncSession, user_id: UUID) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=FactRead, status_code=201)
async def create_fact(user_id: UUID, body: FactCreate, session: DbSession) -> Fact:
    await _get_user_or_404(session, user_id)
    fact = Fact(
        owner_user_id=user_id,
        fact_type=body.fact_type,
        source_type=body.source_type,
        payload=body.payload,
        confidence=body.confidence,
        observed_at=body.observed_at,
        visibility=body.visibility,
        evidence_ref=body.evidence_ref,
        person_id=body.person_id,
        group_id=body.group_id,
        relationship_id=body.relationship_id,
    )
    session.add(fact)
    await session.flush()
    return fact


@router.get("", response_model=list[FactRead])
async def list_facts(
    user_id: UUID,
    session: DbSession,
    status: FactStatus | None = None,
    fact_type: FactType | None = None,
    source_type: SourceType | None = None,
    person_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Fact]:
    await _get_user_or_404(session, user_id)
    stmt = select(Fact).where(Fact.owner_user_id == user_id)
    if status is not None:
        stmt = stmt.where(Fact.status == status)
    if fact_type is not None:
        stmt = stmt.where(Fact.fact_type == fact_type)
    if source_type is not None:
        stmt = stmt.where(Fact.source_type == source_type)
    if person_id is not None:
        stmt = stmt.where(Fact.person_id == person_id)
    stmt = stmt.order_by(Fact.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{fact_id}", response_model=FactRead)
async def get_fact(user_id: UUID, fact_id: UUID, session: DbSession) -> Fact:
    await _get_user_or_404(session, user_id)
    fact = await session.get(Fact, fact_id)
    if fact is None or fact.owner_user_id != user_id:
        raise HTTPException(status_code=404, detail="Fact not found")
    return fact


@router.patch("/{fact_id}", response_model=FactRead)
async def update_fact(user_id: UUID, fact_id: UUID, body: FactUpdate, session: DbSession) -> Fact:
    await _get_user_or_404(session, user_id)
    fact = await session.get(Fact, fact_id)
    if fact is None or fact.owner_user_id != user_id:
        raise HTTPException(status_code=404, detail="Fact not found")
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(fact, field, value)
    await session.flush()
    await session.refresh(fact)
    return fact


@router.post("/{fact_id}/retract", response_model=FactRead)
async def retract_fact(user_id: UUID, fact_id: UUID, session: DbSession) -> Fact:
    await _get_user_or_404(session, user_id)
    fact = await session.get(Fact, fact_id)
    if fact is None or fact.owner_user_id != user_id:
        raise HTTPException(status_code=404, detail="Fact not found")
    if fact.status == FactStatus.RETRACTED:
        raise HTTPException(status_code=409, detail="Fact already retracted")
    fact.status = FactStatus.RETRACTED
    fact.retracted_at = datetime.now(UTC)
    await session.flush()
    await session.refresh(fact)
    return fact
