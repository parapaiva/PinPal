# Work plan — PinPal (milestones)

## Phase 0 — Scaffold
- Repo layout, tooling, docker compose (Postgres + Mongo)
- Lint/format/test commands
- Minimal CI (optional)

## Phase 1 — Core graph (Postgres)
- Users, persons, identities, groups, memberships, relationships
- Query: “why do I know this person?” (initial stub)

## Phase 2 — Evidence + facts (Mongo + Postgres)
- Evidence storage in Mongo
- Fact recording with provenance and visibility
- Timeline events

## Phase 3 — Ingestion adapters (simulated)
- WhatsApp group import (participants list)
- Instagram follow signals import (simulated)
- Manual observations
- Translator + router pipelines

## Phase 4 — Sharing (privacy-first)
- Friend links
- Share insights for IG + WhatsApp only
- Block LinkedIn + personal notes by policy

## Phase 5 — Reliability polish
- Outbox/inbox
- Retries + DLQ
- Observability (logs + metrics)
- Revocation Saga
