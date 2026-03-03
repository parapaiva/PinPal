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
| Relational store | PostgreSQL | Profiles, identities, memberships, relationships |
| Document store | MongoDB | Raw imports, notes, timelines, audit evidence |
| Pipeline | Event-driven with EIP patterns | Ingestion, normalization, routing, compensation |

## Status & Roadmap

PinPal is in **early design and planning**. There is no runnable code yet.

### Planned milestones

- [ ] Schema design (Postgres + MongoDB models)
- [ ] Ingestion pipeline (first source connector)
- [ ] Identity resolution engine
- [ ] REST API
- [ ] Web UI

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE).
