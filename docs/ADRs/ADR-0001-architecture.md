# ADR-0001: Architecture baseline (FastAPI + Postgres + Mongo + event-driven)

## Status
Accepted (initial)

## Context
We want a portfolio project that demonstrates backend/integrations skills:
reliability, idempotency, event-driven workflows, and privacy enforcement.

## Decision
Use:
- FastAPI for the API service
- Postgres as system of record + outbox/inbox
- MongoDB as evidence store for semi-structured payloads
- Background worker to process outbox events, run routers, translators, and sagas

## Consequences
Pros:
- Strong demonstration of enterprise patterns
- Easy local dev with docker compose
- Clear separation of concerns

Cons:
- Extra complexity vs a pure CRUD app
- Requires discipline around event contracts and idempotency
