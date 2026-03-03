# Project spec — PinPal

## Elevator pitch
PinPal is a **personal relationship graph** that helps you remember people and understand *how* you know them.
It consolidates signals from multiple sources (WhatsApp groups, Instagram activity, manual notes, etc.) into an **explainable** network of people, groups, and relationships.

## Core questions we must answer
1) **Where do I know this person from?** (ranked reasons + evidence)
2) **Who else is connected via shared contexts?** (groups/events/co-membership)
3) **What changed and when?** (timeline, provenance, audit)
4) **What can be shared with friends, and what must stay private?** (policy + enforcement)

## Users and roles
- **Owner user**: the person using PinPal (the account in the app).
- **Friend user**: another PinPal user that may receive *shared insights*.

## Sources (inputs)
We treat every input as a **SourceAccount**:
- `MANUAL` — user writes a note/observation (always private)
- `WHATSAPP_GROUP_EXPORT` — user imports an export / participant list / group metadata (shareable if user enables it)
- `INSTAGRAM` — user imports or connects IG signals (shareable if user enables it)
- `LINKEDIN` — user imports signals (always private / never shareable)

**Rule:** No scraping. Assume exports or simulated adapters for demo.

## Outputs
- **People graph** (persons + identities + relationships)
- **Explainable facts** (facts + evidence pointers)
- **Timeline** (append-only log of events)
- **Sharing feed** (only allowed, redacted, consented info)

## Non-goals (explicitly out of scope)
- Reading message content from WhatsApp.
- Scraping or automating data extraction from platforms without user consent/official API.
- Building a full social network (this is a memory + graph tool).

## Definition of “impressive for interview”
The project must demonstrate:
- Event-driven design (outbox/inbox, routing, retries, DLQ)
- Postgres + Mongo with correct responsibilities
- Idempotent ingestion and safe reprocessing
- Privacy model with enforcement and audit trail
- Observability: structured logs, correlation IDs, basic metrics
