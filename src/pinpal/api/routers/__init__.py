"""API routers for the PinPal v1 endpoints."""

from pinpal.api.routers.groups import router as groups_router
from pinpal.api.routers.persons import router as persons_router
from pinpal.api.routers.relationships import router as relationships_router
from pinpal.api.routers.users import router as users_router

__all__ = ["groups_router", "persons_router", "relationships_router", "users_router"]
