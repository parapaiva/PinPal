"""Person + Identity CRUD endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pinpal.api.deps import get_db_session
from pinpal.api.schemas import (
    IdentityCreate,
    IdentityRead,
    PersonCreate,
    PersonRead,
    PersonUpdate,
)
from pinpal.db.models import Identity, Person, User

router = APIRouter(prefix="/api/v1/users/{user_id}/persons", tags=["persons"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def _get_user_or_404(session: AsyncSession, user_id: UUID) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def _get_person_or_404(session: AsyncSession, user_id: UUID, person_id: UUID) -> Person:
    person = await session.get(Person, person_id)
    if person is None or person.owner_user_id != user_id:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


# ---- Person CRUD ----


@router.post("", response_model=PersonRead, status_code=201)
async def create_person(user_id: UUID, body: PersonCreate, session: DbSession) -> Person:
    await _get_user_or_404(session, user_id)
    person = Person(owner_user_id=user_id, display_name=body.display_name)
    session.add(person)
    await session.flush()
    return person


@router.get("", response_model=list[PersonRead])
async def list_persons(user_id: UUID, session: DbSession) -> list[Person]:
    await _get_user_or_404(session, user_id)
    result = await session.execute(select(Person).where(Person.owner_user_id == user_id))
    return list(result.scalars().all())


@router.get("/{person_id}", response_model=PersonRead)
async def get_person(user_id: UUID, person_id: UUID, session: DbSession) -> Person:
    return await _get_person_or_404(session, user_id, person_id)


@router.patch("/{person_id}", response_model=PersonRead)
async def update_person(
    user_id: UUID, person_id: UUID, body: PersonUpdate, session: DbSession
) -> Person:
    person = await _get_person_or_404(session, user_id, person_id)
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(person, field, value)
    await session.flush()
    await session.refresh(person)
    return person


@router.delete("/{person_id}", status_code=204)
async def delete_person(user_id: UUID, person_id: UUID, session: DbSession) -> None:
    person = await _get_person_or_404(session, user_id, person_id)
    await session.delete(person)


# ---- Identity sub-resource ----


@router.post("/{person_id}/identities", response_model=IdentityRead, status_code=201)
async def add_identity(
    user_id: UUID, person_id: UUID, body: IdentityCreate, session: DbSession
) -> Identity:
    await _get_person_or_404(session, user_id, person_id)
    identity = Identity(
        person_id=person_id,
        source_type=body.source_type,
        external_id=body.external_id,
        handle=body.handle,
    )
    session.add(identity)
    await session.flush()
    return identity


@router.get("/{person_id}/identities", response_model=list[IdentityRead])
async def list_identities(user_id: UUID, person_id: UUID, session: DbSession) -> list[Identity]:
    await _get_person_or_404(session, user_id, person_id)
    result = await session.execute(select(Identity).where(Identity.person_id == person_id))
    return list(result.scalars().all())


@router.delete("/{person_id}/identities/{identity_id}", status_code=204)
async def delete_identity(
    user_id: UUID, person_id: UUID, identity_id: UUID, session: DbSession
) -> None:
    await _get_person_or_404(session, user_id, person_id)
    identity = await session.get(Identity, identity_id)
    if identity is None or identity.person_id != person_id:
        raise HTTPException(status_code=404, detail="Identity not found")
    await session.delete(identity)
