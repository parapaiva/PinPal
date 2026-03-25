"""API routers for the PinPal v1 endpoints."""

from pinpal.api.routers.evidence import router as evidence_router
from pinpal.api.routers.facts import router as facts_router
from pinpal.api.routers.groups import router as groups_router
from pinpal.api.routers.imports import router as imports_router
from pinpal.api.routers.persons import router as persons_router
from pinpal.api.routers.relationships import router as relationships_router
from pinpal.api.routers.timeline import router as timeline_router
from pinpal.api.routers.users import router as users_router

__all__ = [
    "evidence_router",
    "facts_router",
    "groups_router",
    "imports_router",
    "persons_router",
    "relationships_router",
    "timeline_router",
    "users_router",
]
