# 2026-05-04 - B4-DATA-001 Data Flow

## Teach-Back

Concept: a read-heavy system has two flows that share only the database and a cache invalidation signal. Writes are batch and idempotent; reads pass through auth, RBAC, rate-limit, parse, validate, cache lookup, optional database call, response shaping, then a cache write-back.

Design decision: I separated the two flows on paper exactly the way they should be separated in code. The write flow ends with a single Redis `INCR` on the cache version tag. The read flow embeds that version tag in the cache key so the next batch's commit makes every cached entry fall out without any per-key invalidation work.

Expected deliverable: Section 3 of the draft contains an ingestion flow, a numbered query flow, a failure-mode table, and a consistency boundary statement.

Likely interview question: "What happens on a cache miss?" Answer: fall through to the database with a pooled connection and a statement timeout matching NFR-2. The database returns rows, the API shapes them, the response is written back to the cache, and telemetry records cache miss and DB time.

## Failure Modes To Avoid

- Per-key cache invalidation. Rejected because filter combinations are open-ended.
- Streaming ingestion. Rejected because the brief says batch.
- Silent fallbacks for unrecognized keyword tokens. The mapper returns 400 with the offending token, so an analyst knows the rule set did not understand them.

## Evidence

- `E-004` records the data-flow section update.

## Next Step

Advance to `B4-DECISIONS-001` and consolidate the design decisions, alternatives, trade-offs, limitations, and the requirement-to-decision map.
