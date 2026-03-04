"""Health-check endpoint."""

from typing import Any

from fastapi import APIRouter, Request
from sqlalchemy import text

router = APIRouter()


@router.get("/healthz")
async def healthz(request: Request) -> dict[str, Any]:
    """Check connectivity to Postgres and MongoDB."""
    checks: dict[str, str] = {}

    # Postgres
    try:
        async with request.app.state.session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error: {exc}"

    # MongoDB
    try:
        mongo_db = request.app.state.mongo_db
        await mongo_db.command("ping")
        checks["mongo"] = "ok"
    except Exception as exc:
        checks["mongo"] = f"error: {exc}"

    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
