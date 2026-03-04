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

## Git & commit workflow
- Use **Conventional Commits** as the project standard:
	- `feat`: new user-visible behavior
	- `fix`: bug fix
	- `refactor`: internal code change without behavior change
	- `test`: tests only
	- `docs`: documentation only
	- `chore`: tooling, build, or maintenance
- Preferred format: `type(scope): short imperative summary`
	- Example: `feat(ingestion): translate whatsapp participant export`
	- Example: `fix(sharing): block linkedin evidence in friend insights`
- Keep commits coherent and reviewable. Granularity is case-by-case, but avoid “everything in one commit” when distinct concerns exist.
- For multi-file features, prefer this order when practical:
	1. foundation (schema/contracts)
	2. behavior (service/router/handler)
	3. tests (unit/integration/contract)
	4. docs (README/WORK_PLAN/ADR)

## Pull request definition of done
- CI green (ruff lint + format check + mypy + pytest).
- Behavior changes include or update tests.
- Postgres schema changes include Alembic migration(s).
- Architecture/policy decisions include doc/ADR update in the same PR.
- Non-trivial async/event flows include structured logs with `correlation_id` and `tenant_id`.
