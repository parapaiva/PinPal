"""Tests for the /healthz endpoint."""

import pytest
from httpx import AsyncClient


async def test_healthz_returns_200(client: AsyncClient) -> None:
    """Endpoint is wired and returns 200 (may be degraded without Docker)."""
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("healthy", "degraded")
    assert "postgres" in body["checks"]
    assert "mongo" in body["checks"]


@pytest.mark.integration
async def test_healthz_all_ok(client: AsyncClient) -> None:
    """With Docker services running, both checks should pass."""
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["checks"]["postgres"] == "ok"
    assert body["checks"]["mongo"] == "ok"
