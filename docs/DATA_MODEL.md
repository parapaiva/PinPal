# Data model (conceptual) — PinPal

This is intentionally **conceptual**. Implement as SQLAlchemy models + Alembic migrations.

## Core entities (Postgres)
### User
- `id`, `email`, `display_name`, `created_at`

### SourceAccount
Represents a user-owned connection or import pipeline.
- `id`, `user_id`, `source_type`, `external_account_id` (nullable), `status`
- `sharing_mode`: `PRIVATE | FRIENDS` (default PRIVATE)
- `created_at`, `revoked_at`

### Person
A real-world person node.
- `id`, `owner_user_id` (who created/claims it), `display_name`, timestamps

### Identity
A platform-specific identity for a Person.
- `id`, `person_id`, `source_type`, `external_id` (nullable), `handle` (nullable)
- unique constraints to prevent duplicates per source

### Group
A context container: WhatsApp group, college cohort, event, etc.
- `id`, `owner_user_id`, `group_type`, `name`, timestamps
- `visibility`: `PRIVATE | FRIENDS` (policy-enforced)

### Membership
Person ↔ Group
- `id`, `group_id`, `person_id`
- `first_seen_at`, `last_seen_at`
- `evidence_ref` (pointer to Mongo evidence)

### Relationship
Person ↔ Person edge
- `id`, `person_a_id`, `person_b_id`, `relationship_type`
- `status`: `SUGGESTED | CONFIRMED | REVOKED`
- `confidence` (0..1), `first_seen_at`, `last_seen_at`
- `why_ref` (pointer to Mongo evidence bundle)

### Fact (structured)
Atomic statement with provenance.
- `id`, `owner_user_id`, `fact_type`, `payload_json`
- `confidence`, `observed_at`
- `visibility`: `PRIVATE | FRIENDS | SENSITIVE`
- `evidence_ref` (Mongo pointer), `revoked_at`

## Reliability tables (Postgres)
### OutboxEvent
- `id`, `event_type`, `event_version`, `payload_json`, `created_at`
- `published_at` (nullable)

### InboxMessage
- `message_id` (unique), `consumer_name`, `processed_at`

### DeadLetter
- `id`, `message_id`, `reason`, `last_error`, `payload_json`, `created_at`

## Evidence store (MongoDB)
Collections:
- `raw_payloads` — original imports + API payloads
- `observations` — manual notes (append-only, versioned)
- `timeline_events` — rich timeline per user/person
- `evidence_bundles` — “why you know them” assembled proofs
