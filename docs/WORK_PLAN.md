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

## Commit slicing examples (portfolio quality)

- **Ingestion feature**
	1. `feat(contracts): add canonical import event envelope`
	2. `feat(ingestion): translate whatsapp export to canonical event`
	3. `test(ingestion): cover translator idempotency and malformed payload`
	4. `docs(architecture): document translator routing decisions`

- **Schema + API feature**
	1. `feat(db): add person_identity table and constraints`
	2. `feat(api): expose person identity endpoints`
	3. `test(api): add integration coverage for identity CRUD`
	4. `docs(data-model): update identity mapping and examples`

- **Privacy fix**
	1. `fix(sharing): prevent linkedin-derived facts from share payloads`
	2. `test(sharing): add policy regression tests for restricted sources`
	3. `docs(privacy): clarify blocked-source behavior`
