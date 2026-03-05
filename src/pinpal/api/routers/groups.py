"""Group + Membership CRUD endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pinpal.api.deps import get_db_session
from pinpal.api.schemas import (
    GroupCreate,
    GroupRead,
    GroupUpdate,
    MembershipCreate,
    MembershipRead,
)
from pinpal.db.models import Group, Membership, Person, User

router = APIRouter(prefix="/api/v1/users/{user_id}/groups", tags=["groups"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def _get_user_or_404(session: AsyncSession, user_id: UUID) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def _get_group_or_404(session: AsyncSession, user_id: UUID, group_id: UUID) -> Group:
    group = await session.get(Group, group_id)
    if group is None or group.owner_user_id != user_id:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


# ---- Group CRUD ----


@router.post("", response_model=GroupRead, status_code=201)
async def create_group(user_id: UUID, body: GroupCreate, session: DbSession) -> Group:
    await _get_user_or_404(session, user_id)
    group = Group(
        owner_user_id=user_id,
        group_type=body.group_type,
        name=body.name,
        visibility=body.visibility,
    )
    session.add(group)
    await session.flush()
    return group


@router.get("", response_model=list[GroupRead])
async def list_groups(user_id: UUID, session: DbSession) -> list[Group]:
    await _get_user_or_404(session, user_id)
    result = await session.execute(select(Group).where(Group.owner_user_id == user_id))
    return list(result.scalars().all())


@router.get("/{group_id}", response_model=GroupRead)
async def get_group(user_id: UUID, group_id: UUID, session: DbSession) -> Group:
    return await _get_group_or_404(session, user_id, group_id)


@router.patch("/{group_id}", response_model=GroupRead)
async def update_group(
    user_id: UUID, group_id: UUID, body: GroupUpdate, session: DbSession
) -> Group:
    group = await _get_group_or_404(session, user_id, group_id)
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(group, field, value)
    await session.flush()
    await session.refresh(group)
    return group


@router.delete("/{group_id}", status_code=204)
async def delete_group(user_id: UUID, group_id: UUID, session: DbSession) -> None:
    group = await _get_group_or_404(session, user_id, group_id)
    await session.delete(group)


# ---- Membership sub-resource ----


@router.post("/{group_id}/members", response_model=MembershipRead, status_code=201)
async def add_member(
    user_id: UUID, group_id: UUID, body: MembershipCreate, session: DbSession
) -> Membership:
    await _get_group_or_404(session, user_id, group_id)
    person = await session.get(Person, body.person_id)
    if person is None or person.owner_user_id != user_id:
        raise HTTPException(status_code=404, detail="Person not found")
    membership = Membership(group_id=group_id, person_id=body.person_id)
    session.add(membership)
    await session.flush()
    return membership


@router.get("/{group_id}/members", response_model=list[MembershipRead])
async def list_members(user_id: UUID, group_id: UUID, session: DbSession) -> list[Membership]:
    await _get_group_or_404(session, user_id, group_id)
    result = await session.execute(select(Membership).where(Membership.group_id == group_id))
    return list(result.scalars().all())


@router.delete("/{group_id}/members/{membership_id}", status_code=204)
async def remove_member(
    user_id: UUID, group_id: UUID, membership_id: UUID, session: DbSession
) -> None:
    await _get_group_or_404(session, user_id, group_id)
    membership = await session.get(Membership, membership_id)
    if membership is None or membership.group_id != group_id:
        raise HTTPException(status_code=404, detail="Membership not found")
    await session.delete(membership)
