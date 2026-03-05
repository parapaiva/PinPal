"""User CRUD endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from pinpal.api.deps import get_db_session
from pinpal.api.schemas import UserCreate, UserRead, UserUpdate
from pinpal.db.models import User

router = APIRouter(prefix="/api/v1/users", tags=["users"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post("", response_model=UserRead, status_code=201)
async def create_user(body: UserCreate, session: DbSession) -> User:
    user = User(email=body.email, display_name=body.display_name)
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Email already exists") from exc
    return user


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: UUID, session: DbSession) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: UUID, body: UserUpdate, session: DbSession) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)
    await session.flush()
    await session.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: UUID, session: DbSession) -> None:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
