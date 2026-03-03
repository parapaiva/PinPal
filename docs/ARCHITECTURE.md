# Architecture — PinPal

## Goals
- Explainable relationship graph (every edge has receipts)
- Reliability patterns (outbox/inbox, idempotency, retries, DLQ)
- Clear separation between **transactional truth (Postgres)** and **semi-structured evidence (Mongo)**

## Suggested topology (portfolio-friendly)
Two processes in one repo (easy to run locally, still “enterprise”):
1) **API service (FastAPI)** — synchronous commands and queries
2) **Worker service** — background ingestion + event processing pipelines

You can later split into microservices without changing the event contracts.

## Data stores
- **Postgres**: state that must be consistent and queryable with constraints
- **MongoDB**: raw payloads, evidence, timelines, large documents, variable schemas

## Event-driven backbone
Use an **Outbox** table in Postgres:
- API commits business state changes + writes an outbox event atomically
- Worker publishes and processes events
- Consumers write to an **Inbox** (dedupe) before applying side effects

## Pipelines (EIP patterns)
- **Translator**: source-specific input → canonical event(s)
- **Content-based router**: decide which processors run
- **Claim check**: store large payload in Mongo, keep only reference in events
- **Saga/Compensation**: revoke a source → undo derived facts/edges/shares

## Observability
- Structured JSON logs with: `correlation_id`, `causation_id`, `tenant_id`, `user_id`
- OpenTelemetry traces (optional but great for interview)
- Metrics: queue lag, processing times, retries, DLQ count

## Security / privacy
- Strong default: everything is PRIVATE unless explicitly allowed.
- Enforce policy at the API layer *and* inside async processors.
- Never share LinkedIn-derived or manual personal notes.

## Suggested repo layout
- `src/pinpal/api/` — FastAPI app, routers, auth, schemas
- `src/pinpal/core/` — domain model, services, policies
- `src/pinpal/db/` — SQLAlchemy models, Alembic migrations
- `src/pinpal/mongo/` — Mongo models, repositories
- `src/pinpal/events/` — event envelope, contracts, router, outbox/inbox
- `src/pinpal/workers/` — processors, sagas, retries, DLQ
- `tests/` — unit + integration tests
- `docs/` — specs, ADRs, runbooks
