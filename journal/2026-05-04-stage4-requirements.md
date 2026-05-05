# 2026-05-04 - B4-REQ-001 Requirements Extraction

## Teach-Back

Concept: requirements extraction. A functional requirement names a behaviour the system must perform (store data, accept a filter query, run an aggregation). A non-functional requirement names a quality the system must hold while performing that behaviour (latency budget, scale ceiling, single-region, simplicity).

Design decision: I read the official brief literally and split it into two lists. I did not invent requirements. I kept Stage 3 surfaces (GitHub OAuth/PKCE, RBAC, JWT and refresh tokens, CLI, Next.js web portal, versioned API, pagination, CSV export) as functional preservation requirements because the brief says Stage 3 stays intact and evaluators will notice if it breaks.

Expected deliverable: the requirements section of the draft contains a numbered functional list, a numbered non-functional list, and an assumptions block. Each item is short, testable, and mapped from the brief.

Likely interview question: "Why is this not a true natural-language system?" Answer: the brief explicitly states queries are structured filters, aggregations, and rule-based keyword mapping. Treating it as an LLM problem would invent a requirement the brief rejects and add cost and failure modes the design does not need.

## Failure Modes To Avoid

- Adding "real-time analytics" or "vector search" as a functional requirement. The brief lists those as optional future evolution only.
- Inventing a write-throughput NFR. Writes are batch, not high-frequency.
- Dropping Stage 3 surfaces. The mentor warned that broken Stage 3 surfaces fail the work.

## Evidence

- `E-002` records the requirements draft update and gate closure.

## Next Step

Advance to `B4-ARCH-001` and design the high-level scaling architecture that satisfies these requirements without unjustified complexity.
