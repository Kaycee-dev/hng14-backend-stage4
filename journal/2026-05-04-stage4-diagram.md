# 2026-05-04 - B4-DIAGRAM-001 Architecture Diagram

## Teach-Back

Concept: a system-design diagram has two roles. It carries the same architectural claims as the prose so a reader who skims the picture sees what the prose says, and it makes spatial relationships (clients above the API tier, cache and pool between the API and the database, ingestion as its own process) easier to read than text. A diagram that adds components the prose does not have is worse than no diagram, because reviewers cannot tell which version of the design is real.

Design decision: I chose Mermaid `flowchart TD` as the source format because it is plain text (so the source link the brief requires is a real source, not a binary), it renders in mermaid.live and via `mmdc`, and Google Docs accepts the exported PNG. Every node on the diagram has a label that matches Section 2 of the draft, and every node references the requirement (FR-/NFR-) or decision (D-) that justifies it.

Expected deliverable: `diagrams/source/architecture.mmd` (Mermaid source), `diagrams/exported/architecture.md` (export-ready reference with the render command and embed checklist), updated diagram READMEs, and Section 7 of the draft linking both files plus an inline Mermaid block so the markdown preview shows the same architecture before any binary export exists.

Likely interview question: "Which components were intentionally left out of the diagram?" Answer: anything not in Section 2.3 of the draft. No queue, no microservices split, no multi-region routing layer, no LLM, no separate search engine. Read replica and materialized aggregates are on the diagram but tagged "conditional" so a reader can see they are levers with triggers, not default infrastructure.

## Failure Modes To Avoid

- Diagram drift: adding a node on the picture that is not in the prose, or vice versa. Prevented by labelling each node with its FR/NFR/D-id and pointing both READMEs at Section 2.3 as the source of truth.
- Decorative diagrams: nothing on the picture is decorative; every node serves a requirement.
- Unsupported export claim: I cannot run `mmdc` from this design-doc-only environment, so the exported PNG is produced by the operator before submission. The export-ready reference documents that exact step.

## Evidence

- `E-006` records the diagram source, exported reference, and draft Section 7 update.

## Next Step

Advance to `B4-SUBMISSION-001` and reconcile the draft, QA, and submission notes for Google Docs handoff.
