## Summary
- What changed and why?

## Commit quality
- [ ] Commit messages follow Conventional Commits (`type(scope): summary`)
- [ ] Commits are coherent and reviewable (unrelated concerns split when useful)

## Validation
- [ ] `make lint` passes locally
- [ ] `make test` passes locally or in CI
- [ ] Changed behavior has test coverage (unit/integration/contract as relevant)

## Data and contracts
- [ ] Postgres schema changes include Alembic migration(s)
- [ ] Event contract changes include updated docs/tests
- [ ] Mongo query-path changes include index considerations

## Reliability and observability
- [ ] Async/event handling remains idempotent and retry-safe
- [ ] DLQ/error paths are handled for persistent failures
- [ ] Structured logs include `correlation_id` and `tenant_id` where applicable

## Privacy and policy
- [ ] Sharing rules are respected (LinkedIn + personal notes remain private by default)
- [ ] No scraping/ToS-bypass behavior introduced

## Documentation
- [ ] Architecture/behavior decisions are documented (docs and/or ADR) in this PR
