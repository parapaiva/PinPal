# Privacy & sharing — PinPal

## Design principle
Everything is **PRIVATE by default**. Sharing is:
- explicit (user action),
- source-scoped,
- reversible (revocation triggers compensation),
- auditable (who shared what, when, why).

## Data classification
- `PRIVATE`: visible only to the owner user
- `FRIENDS`: may be shared to approved friend users
- `SENSITIVE`: never share (even if user tries) unless a future explicit feature is added with strong consent

## Source sharing policy (baseline)
| Source type | Default visibility | Can share? | Notes |
|---|---:|---:|---|
| Instagram | PRIVATE | Yes (FRIENDS) | Share only redacted insights, not raw payloads |
| WhatsApp group context | PRIVATE | Yes (FRIENDS) | Never store message content; only membership + metadata |
| LinkedIn | SENSITIVE | No | Never share (policy-enforced) |
| Manual personal notes | PRIVATE (or SENSITIVE) | No | Treat as private memory |

## What “sharing” means
Share **insights**, not raw data:
- ✅ “You and Alex were co-members of a group in 2023.”
- ✅ “You discovered Alex via Instagram follow graph.”
- ❌ Raw exports, raw handles if user marked them private
- ❌ Any LinkedIn-derived or manual-note-derived info

## Consent model (simple, interview-friendly)
- Owner user can create a `FriendLink` with another user.
- Sharing requires:
  - friend link exists AND
  - source is share-enabled AND
  - fact/edge is classified as FRIENDS
- Revoking a source triggers a **Saga** to revoke derived shared insights.

## Audit requirements
Every shared insight must record:
- `shared_by_user_id`
- `shared_to_user_id`
- `source_type`
- `created_at`
- `evidence_ref` (for explainability)
