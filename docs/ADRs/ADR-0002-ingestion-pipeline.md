# ADR-0002: Ingestion Pipeline Design

**Status:** Accepted
**Date:** 2026-03-25
**Context:** Phase 3 — Ingestion Adapters

## Decision

Implement a synchronous, in-process ingestion pipeline that normalizes source-specific imports into canonical events and processes them within a single HTTP request.

## Architecture

The pipeline applies three Enterprise Integration Patterns:

### 1. Claim Check

Raw payloads are hashed (SHA-256) and stored in MongoDB's `raw_payloads` collection before processing. The content hash serves as a deduplication key — if a payload with the same hash already exists for the user, the import returns early as a duplicate. This avoids reprocessing identical imports.

### 2. Translator (Message Translator)

Each source type has a dedicated translator — a pure function that takes a validated payload and produces a list of `CanonicalEvent` objects. Translators are:

- **WhatsApp**: `WhatsAppGroupPayload` → 1× `group.imported` + N× (`identity.linked`, `membership.observed`, `fact.recorded`)
- **Instagram**: `InstagramFollowsPayload` → N× (`identity.linked`, `fact.recorded`)
- **Manual**: `ManualObservationPayload` → `observation.recorded` + `fact.recorded`

Translators have no side effects (no DB access, no async). This makes them trivially testable and reusable.

### 3. Content-Based Router

The `EventRouter` maintains a registry of handler functions keyed by event type string. Events are dispatched sequentially (ordering matters — e.g., `group.imported` must precede `membership.observed` so the group ID is available). Unknown event types are logged and skipped.

### Handler State: ImportContext

Handlers share an `ImportContext` dataclass that accumulates state across the import:

- `group_id`: Set by the group handler, consumed by membership/fact handlers
- `person_ids`: Dict mapping display_name → UUID, enabling person dedup within a single import
- `entities`: Running count of created entities for the response summary

### Idempotency

- **Cross-import**: Content hash on raw_payloads (unique index per user)
- **Within-import**: `person_ids` dict prevents duplicate Person creation
- **Identity/Membership**: Unique constraints caught via `IntegrityError` → rollback and continue

## Data Flow

```
POST /api/v1/users/{user_id}/imports
  │
  ├─ 1. Hash payload → check raw_payloads for duplicate → store if new
  ├─ 2. Validate + translate via source-specific translator
  ├─ 3. Route: dispatch each event to its handler sequentially
  │     └─ Handlers create entities in Postgres + MongoDB
  └─ 4. Return ImportResultRead with entity summary
```

## Trade-offs

| Aspect | Current (Phase 3) | Future (Phase 5) |
|--------|-------------------|-------------------|
| Execution | Synchronous, in-process | Async via outbox/inbox |
| Retry | None — errors fail the request | Dead letter queue + retry |
| Latency | Acceptable for small imports | Background processing |
| Atomicity | Single DB transaction per request | Eventual consistency |

## Consequences

- Pipeline is simple and debuggable — all processing visible in a single request
- No infrastructure dependencies beyond Postgres + MongoDB
- Translators are pure functions — easy to add new source types
- Sequential handler dispatch means group/identity must be created before membership/fact
- Large imports (1000+ participants) may be slow — acceptable for portfolio demo
