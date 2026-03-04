# Integration patterns (EIP) — PinPal

## Translator (Message Translator)
Normalize all inbound inputs (exports, APIs, manual UI) into canonical events:
- `*_imported` / `*_observed` / `fact_recorded`

## Content-based Router
Route events based on:
- source type (IG vs WhatsApp vs manual)
- visibility (PRIVATE vs FRIENDS)
- event type (membership observed triggers relationship inference)

## Claim Check
Large payloads go to Mongo (`raw_payloads`), events keep only pointers.

## Idempotent Receiver
Every consumer checks Inbox by `message_id` before side effects.

## Retry + DLQ
- Retry transient failures with backoff.
- Send persistent failures to DLQ with human-actionable reason.

## Saga / Compensation
Example: **SourceRevokedSaga**
- input: `source.revoked`
- actions:
  1) mark related facts as revoked
  2) recompute derived relationships (or mark as stale)
  3) revoke any shared insights produced from that source
- each action is idempotent and logged.

## Observability for integrations
For every event processed:
- log `message_id`, `correlation_id`, processor name, outcome
- metric: processing latency, retries, DLQ count
