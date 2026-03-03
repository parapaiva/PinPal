# Event contracts — PinPal

## Canonical event envelope (JSON)
All events must include:
- `message_id` (dedupe key; UUID/ULID)
- `correlation_id` (end-to-end trace)
- `causation_id` (what triggered this)
- `tenant_id` (or `owner_user_id` if single-tenant)
- `producer`, `event_type`, `event_version`
- `occurred_at` (ISO8601)
- `visibility` (PRIVATE/FRIENDS/SENSITIVE)
- `payload` (small, structured)
- optional `evidence_ref` (Mongo pointer to large/raw content)

## Versioning rules
- Backward-compatible additions: bump MINOR only if your tooling supports it; otherwise bump `event_version`.
- Breaking changes: new `event_type` or new major `event_version`.
- Never repurpose semantics of an existing field.

## Example event types (initial set)
- `pinpal.source.connected.v1`
- `pinpal.source.revoked.v1`
- `pinpal.person.created.v1`
- `pinpal.identity.linked.v1`
- `pinpal.group.imported.v1`
- `pinpal.membership.observed.v1`
- `pinpal.fact.recorded.v1`
- `pinpal.relationship.suggested.v1`
- `pinpal.relationship.confirmed.v1`
- `pinpal.share.insight.published.v1`
- `pinpal.share.insight.revoked.v1`

## Idempotency expectations
- Consumers must be idempotent by `message_id`.
- Side effects must be safe to retry (use upserts + unique keys).
- All processors must either complete successfully or land the message in DLQ with a reason.
