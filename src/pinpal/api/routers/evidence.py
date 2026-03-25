"""Evidence endpoints: raw payloads, observations, bundles (MongoDB)."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from pinpal.api.deps import get_mongo_db
from pinpal.db.enums import SourceType
from pinpal.mongo.repositories import EvidenceBundleRepo, ObservationRepo, RawPayloadRepo
from pinpal.mongo.schemas import (
    EvidenceBundleCreate,
    EvidenceBundleRead,
    ObservationCreate,
    ObservationRead,
    RawPayloadCreate,
    RawPayloadRead,
)

router = APIRouter(prefix="/api/v1/users/{user_id}/evidence", tags=["evidence"])

MongoDB = Annotated[AsyncIOMotorDatabase[dict[str, Any]], Depends(get_mongo_db)]


# ---- Raw Payloads ----


@router.post("/raw-payloads", response_model=RawPayloadRead, status_code=201)
async def store_raw_payload(user_id: UUID, body: RawPayloadCreate, db: MongoDB) -> RawPayloadRead:
    body.owner_user_id = str(user_id)
    repo = RawPayloadRepo(db)
    return await repo.insert(body)


@router.get("/raw-payloads", response_model=list[RawPayloadRead])
async def list_raw_payloads(
    user_id: UUID,
    db: MongoDB,
    source_type: SourceType | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[RawPayloadRead]:
    repo = RawPayloadRepo(db)
    return await repo.list_for_user(
        str(user_id),
        source_type=source_type.value if source_type else None,
        limit=limit,
        offset=offset,
    )


@router.get("/raw-payloads/{payload_id}", response_model=RawPayloadRead)
async def get_raw_payload(user_id: UUID, payload_id: str, db: MongoDB) -> RawPayloadRead:
    repo = RawPayloadRepo(db)
    result = await repo.get(payload_id)
    if result is None or result.owner_user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Raw payload not found")
    return result


# ---- Observations ----


@router.post("/observations", response_model=ObservationRead, status_code=201)
async def store_observation(
    user_id: UUID, body: ObservationCreate, db: MongoDB
) -> ObservationRead:
    body.owner_user_id = str(user_id)
    repo = ObservationRepo(db)
    return await repo.insert(body)


@router.get("/observations", response_model=list[ObservationRead])
async def list_observations(
    user_id: UUID,
    db: MongoDB,
    person_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ObservationRead]:
    repo = ObservationRepo(db)
    return await repo.list_for_user(
        str(user_id),
        person_id=str(person_id) if person_id else None,
        limit=limit,
        offset=offset,
    )


@router.get("/observations/{observation_id}", response_model=ObservationRead)
async def get_observation(user_id: UUID, observation_id: str, db: MongoDB) -> ObservationRead:
    repo = ObservationRepo(db)
    result = await repo.get(observation_id)
    if result is None or result.owner_user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Observation not found")
    return result


# ---- Evidence Bundles ----


@router.post("/bundles", response_model=EvidenceBundleRead, status_code=201)
async def create_bundle(
    user_id: UUID, body: EvidenceBundleCreate, db: MongoDB
) -> EvidenceBundleRead:
    body.owner_user_id = str(user_id)
    repo = EvidenceBundleRepo(db)
    return await repo.insert(body)


@router.get("/bundles", response_model=list[EvidenceBundleRead])
async def list_bundles(
    user_id: UUID,
    db: MongoDB,
    person_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[EvidenceBundleRead]:
    repo = EvidenceBundleRepo(db)
    return await repo.list_for_user(
        str(user_id),
        person_id=str(person_id) if person_id else None,
        limit=limit,
        offset=offset,
    )


@router.get("/bundles/{bundle_id}", response_model=EvidenceBundleRead)
async def get_bundle(user_id: UUID, bundle_id: str, db: MongoDB) -> EvidenceBundleRead:
    repo = EvidenceBundleRepo(db)
    result = await repo.get(bundle_id)
    if result is None or result.owner_user_id != str(user_id):
        raise HTTPException(status_code=404, detail="Evidence bundle not found")
    return result
