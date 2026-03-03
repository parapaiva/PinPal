# Engineering standards — PinPal

## Code quality
- Prefer simple, boring solutions.
- Keep modules cohesive; avoid “god services”.
- Add type hints for public interfaces.

## Testing
- Unit tests for domain services (policy, matching, routing).
- Integration tests with Postgres + Mongo (docker compose).
- Contract tests for event envelopes (schema validation).

## Reliability checklist (for every async processor)
- Idempotent by `message_id`
- Safe retry (no duplicate side effects)
- DLQ on persistent failure with actionable reason
- Structured logs + correlation IDs

## Security basics
- Secrets via env vars (never committed)
- Least privilege for sharing
- Log redaction (avoid PII in logs)
