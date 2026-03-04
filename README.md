# PinPal

**A personal relationship graph that helps you remember where you know people from.**

## Overview

PinPal helps you answer two simple questions: "Where do I know this person from?" and "I want to remember them later." It ingests signals from multiple sources (e.g., WhatsApp groups, Instagram activity, and manual notes), normalizes them into canonical events, and builds an explainable network of people, groups, and relationships.

Think of it as an **ERP for connections** — structured enough to be reliable, flexible enough to capture the messy reality of how people actually know each other.

## Key Features

- **Multi-source ingestion** — Import signals from WhatsApp, Instagram, LinkedIn, and manual notes into a single unified graph
- **Dual-database architecture** — Postgres for transactional truth, MongoDB for semi-structured context
- **Event-driven pipeline** — EIP patterns (translation, routing, compensation) with idempotency, retries, and a dead-letter queue for safe reprocessing
- **Privacy-first design** — Every fact is tagged with its source and visibility policy, so you control what's shared and what stays private

## Architecture

PinPal uses a two-database model:

- **PostgreSQL** — Source of truth for transactional state: profiles, identities, memberships, and relationships
- **MongoDB** — Semi-structured context: raw imports, notes, timelines, and audit evidence

Data flows through an **event-driven pipeline** that applies Enterprise Integration Patterns:

1. **Ingestion** — Raw data arrives from a source connector (WhatsApp export, Instagram API, manual entry)
2. **Translation** — Raw signals are normalized into canonical events
3. **Routing** — Events are directed to the appropriate handlers (identity resolution, relationship updates, timeline entries)
4. **Persistence** — Transactional state lands in Postgres; context and evidence land in MongoDB
5. **Compensation** — Failures are retried with idempotency guarantees; unrecoverable events go to a DLQ for manual review

## Privacy Model

Privacy is first-class. Every fact in the system is tagged with:

- **Source** — Where the information came from (WhatsApp, Instagram, LinkedIn, manual note)
- **Visibility policy** — Who can see it and in what context

This means:

- **Public-context data** (e.g., WhatsApp/Instagram group membership) can be shared with friends
- **Private-by-default data** (e.g., LinkedIn connections, personal notes) remains visible only to you unless explicitly approved

## Tech Stack

| Component | Technology | Role |
|-----------|-----------|------|
| API | FastAPI | Async REST API |
| Relational store | PostgreSQL 16 | Profiles, identities, memberships, relationships |
| Document store | MongoDB 7 | Raw imports, notes, timelines, audit evidence |
| Postgres driver | asyncpg + SQLAlchemy 2 | Async ORM and raw queries |
| Mongo driver | Motor | Async MongoDB client |
| Migrations | Alembic (async) | Schema versioning |
| Config | pydantic-settings | Type-safe env var parsing |
| Logging | structlog | JSON structured logging |
| Pipeline | Event-driven with EIP patterns | Ingestion, normalization, routing, compensation |

## Development

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)
- Docker & Docker Compose

### Quickstart

```bash
# Install dependencies
make install

# Start Postgres + MongoDB
make up

# Run the dev server (http://localhost:8000)
make dev

# Verify everything works
curl localhost:8000/healthz
```

### Available commands

```
make help            Show all commands
make install         Install dependencies (dev included)
make up              Start Postgres + MongoDB containers
make down            Stop containers
make dev             Start FastAPI dev server
make lint            Run ruff linter + mypy type checker
make format          Auto-format code with ruff
make typecheck       Run mypy
make test            Run all tests (requires Docker services)
make test-unit       Run unit tests only (no Docker needed)
make test-integration Run integration tests only
make migrate         Run Alembic migrations
make logs            Tail container logs
```

## Commit & PR workflow

PinPal is a portfolio project, so commit history should clearly show engineering decision quality.

- Follow Conventional Commits: `type(scope): summary` (e.g., `feat(router): add content-based route for import events`).
- Keep commits reviewable; split unrelated concerns when useful (code, tests, docs).
- For architecture or behavior changes, include docs/ADR updates in the same PR.
- For schema changes, include Alembic migration files in the same PR.
- Before opening a PR, run:

```bash
make lint
make test
```

## Status & Roadmap

### Planned milestones

- [x] Project scaffold (dev tooling, Docker Compose, health check)
- [ ] Schema design (Postgres + MongoDB models)
- [ ] Ingestion pipeline (first source connector)
- [ ] Identity resolution engine
- [ ] REST API
- [ ] Web UI

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE).
