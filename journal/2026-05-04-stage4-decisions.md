# 2026-05-04 - B4-DECISIONS-001 Decisions And Limitations

## Teach-Back

Concept: a design decision is a documented choice with at least one rejected alternative, a stated trade-off, and a requirement it serves. A limitation is the part of the design that is intentionally not handled, recorded so reviewers can see the boundary instead of being surprised by it.

Design decision: I rolled all seven design decisions (D-005 through D-011) into a single summary table in Section 4 of the draft so a reader can see decision, trade-off, and requirement on one row. Section 5 lists the limitations as plain prose so they cannot be skimmed past.

Expected deliverable: Section 4 has a decisions table, an indexing-strategy block, a caching-strategy block, and an observability and reliability block. Section 5 has a numbered limitations list and a "next levers" sequence for 10x growth.

Likely interview question: "What trade-off does caching introduce?" Answer: bounded staleness. The cache keys embed a version tag that the ingestion worker bumps at commit, so after a batch every cached entry effectively expires at once. That gives correctness at the cost of a brief miss spike right after each batch.

## Failure Modes To Avoid

- Listing decisions without trade-offs. Caught by the table, every row has a "Trade-off accepted" cell.
- Inventing a 99.9% availability SLO under "limitations" pressure. Stayed inside D-006: only the brief's targets are committed to.
- Adding limitations that are actually unfinished work. Each limitation is intentional and traceable to a decision or to NFR-6 / NFR-9.

## Evidence

- `E-005` records the decisions and limitations section update.

## Next Step

Advance to `B4-DIAGRAM-001` and produce a diagram source plus an export-ready artifact.
