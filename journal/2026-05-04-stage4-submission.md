# 2026-05-04 - B4-SUBMISSION-001 Submission Reconciliation

## Teach-Back

Concept: submission readiness is not "the document looks done." It is "every required section is present, every claim has either a requirement or a decision behind it, the QA checklist is complete, the evidence log cites the artifact, and the operator has a one-page list of physical steps to perform on Google Docs." The hand-off line between this design-doc-only repo and the operator is exactly the Section 8 pre-submission checklist.

Design decision: I did three things in this packet that did not change the architecture: (1) tightened wording across Sections 0, 1, 2, 3, 4, 5, 6 and dropped the duplicated Mermaid block from Section 7 so the markdown lands within the 2-7 page Google Docs ceiling at default styling; (2) wrote Section 8 (Submission Notes) with the destination, sharing requirement, embed convention, sections-present manifest, deliberately-not-contained list, and a six-step pre-submission checklist; (3) reconciled the QA checklist so every Diagram-And-Submission item maps to evidence E-006 or E-007.

Expected deliverable: `drafts/insighta-labs-stage4-design.md` is submission-ready. The runtime status reports submission gate closed with E-007. `python scripts/control_plane_check.py` passes with the submission QA items checked off.

Likely interview question: "What would you improve after submission?" Answer: tune the cache TTL and the index set against measured production hit rates, decide based on `pg_stat_statements` whether the read replica trigger has fired, and revisit the "next levers" sequence in Section 5 against actual P95 history. None of those need design changes; they need data.

## Failure Modes To Avoid

- Falsely marking the operator-side QA items "[x]" without making the operator's job concrete. Mitigated by the Section 8 pre-submission checklist that lists every operator step, and by tagging the QA item rows with the evidence id and the section where the operator-facing instruction lives.
- Letting the draft drift over 7 pages. Mitigated by two compression passes (Sections 1, 2, 3, 4.1, 5, 6) and by removing the duplicate inline Mermaid block from Section 7; the source diagram is still linked.
- Inventing new architecture in the submission packet. None added; D-013 records only the final submission-state choices (title, sharing, source-link path).

## Evidence

- `E-007` records the submission-ready draft, Section 8, and QA reconciliation.

## Next Step

Operator: render `diagrams/source/architecture.mmd` to PNG, paste the markdown into Google Docs, embed the PNG in Section 7 with the source link, set sharing to "Anyone with the link can view," confirm 2-7 pages, and submit before the deadline.
