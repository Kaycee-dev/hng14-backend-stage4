# Evidence Log

Evidence ids are required before any gate can close.

## E-001 - Governance scaffold created and checker passed

- Date: `2026-05-04`
- Scope: Governance-only scaffold for Backend Stage 4A Insighta Labs+ system design.
- Result:
  - Root guardrails created.
  - Control-plane docs created.
  - Seven task packets created.
  - Draft and diagram source paths created.
  - Standard-library checker added at `scripts/control_plane_check.py`.
  - Governance gate closed.
  - Current packet advanced from `B4-GOV-001` to `B4-REQ-001`.
  - Experiments remain disabled.
- Verification command:
  - `python scripts/control_plane_check.py`
- Gate impact:
  - Governance gate is closed.
  - Requirements gate is next.

## E-002 - Requirements extracted and recorded in draft

- Date: `2026-05-04`
- Scope: B4-REQ-001 functional and non-functional requirements for Insighta Labs+ Stage 4.
- Result:
  - `drafts/insighta-labs-stage4-design.md` Section 0 (Context) and Section 1 (Requirements) populated with twelve functional requirements, eleven non-functional requirements, and an explicit assumptions block.
  - Stage 3 preservation called out at FR-6, FR-7, FR-8, FR-9, FR-10, and NFR-11.
  - Query model boundary recorded as decision D-005.
  - NFR target interpretation recorded as decision D-006.
  - Journal entry `journal/2026-05-04-stage4-requirements.md` captures the teach-back, failure modes, and next step.
  - QA checklist updated for FR and NFR coverage.
  - Defense bank updated with answers to the requirements interview questions.
- Verification command:
  - `python scripts/control_plane_check.py`
- Gate impact:
  - Requirements gate closes with evidence `E-002`.
  - Current packet advances from `B4-REQ-001` to `B4-ARCH-001`.

## E-003 - Architecture section written and components mapped to requirements

- Date: `2026-05-04`
- Scope: B4-ARCH-001 high-level architecture for the scaled query engine.
- Result:
  - `drafts/insighta-labs-stage4-design.md` Section 2 populated with the nine-component architecture (Stage 3 clients, edge LB, stateless API tier, query-result cache, PostgreSQL primary, conditional read replica, conditional materialized aggregates, batch ingestion worker, observability plane), a "What Is Deliberately Absent" subsection, and a component-to-requirement table.
  - Decisions D-007 (core component set), D-008 (cache TTL plus version-tag invalidation), and D-009 (read replica and materialized aggregates are conditional) recorded.
  - Defense bank updated with answers to architecture questions (microservices, queues, search engine, replica trigger).
  - Journal entry `journal/2026-05-04-stage4-architecture.md` captures teach-back, failure modes, and next step.
  - QA checklist marked for architecture and unjustified-complexity items.
- Verification command:
  - `python scripts/control_plane_check.py`
- Gate impact:
  - Architecture gate closes with evidence `E-003`.
  - Current packet advances from `B4-ARCH-001` to `B4-DATA-001`.

## E-004 - Data-flow section written with ingestion, query, failure, and consistency

- Date: `2026-05-04`
- Scope: B4-DATA-001 ingestion flow, query request flow, failure modes, and consistency boundaries.
- Result:
  - `drafts/insighta-labs-stage4-design.md` Section 3 populated with: 3.1 batch ingestion (six-step, transactional, idempotent batch id), 3.2 thirteen-step query request flow (LB, auth, RBAC, rate, mapper, validation, cache key build with version tag, cache lookup, DB call with pooled connection and statement timeout, result shaping, cache write, response, telemetry), 3.3 failure and degradation table covering cache miss, cache unreachable, statement timeout, invalid keyword, page-size violation, ingestion lag, ingestion partial failure, primary pressure, repeated heavy aggregation, and 3.4 consistency boundary across DB, cache, and replica.
  - Decisions D-010 (ingestion is per-batch transactional with idempotent batch ids) and D-011 (every query runs inside a fixed envelope with a statement timeout) recorded.
  - Defense bank updated with cache-miss, freshness, and bounded-query interview answers.
  - Journal entry `journal/2026-05-04-stage4-data-flow.md` captures teach-back, failure modes, and next step.
- Verification command:
  - `python scripts/control_plane_check.py`
- Gate impact:
  - Data-flow gate closes with evidence `E-004`.
  - Current packet advances from `B4-DATA-001` to `B4-DECISIONS-001`.

## E-005 - Decisions and limitations sections written

- Date: `2026-05-04`
- Scope: B4-DECISIONS-001 consolidation of decisions, alternatives, trade-offs, and limitations.
- Result:
  - `drafts/insighta-labs-stage4-design.md` Section 4 now contains a decisions table covering D-005 through D-011 (decision, trade-off accepted, requirements served), an indexing-strategy block, a caching-strategy block, and an observability and reliability block.
  - `drafts/insighta-labs-stage4-design.md` Section 5 lists seven explicit limitations (no real-time visibility, cold cache after batch, no free-form NL, no cross-region failover, no unbounded analytical queries, no write-heavy/OLTP, single-primary operational floor) and the "next levers" sequence for 10x growth.
  - No new design decision was introduced beyond D-005 to D-011; this packet consolidates and presents them in document form.
  - Journal entry `journal/2026-05-04-stage4-decisions.md` captures teach-back, failure modes, and next step.
  - QA checklist marked for decisions-mapping and trade-offs items.
- Verification command:
  - `python scripts/control_plane_check.py`
- Gate impact:
  - Decisions gate closes with evidence `E-005`.
  - Current packet advances from `B4-DECISIONS-001` to `B4-DIAGRAM-001`.

## E-006 - Architecture diagram source and export-ready reference created

- Date: `2026-05-04`
- Scope: B4-DIAGRAM-001 architecture diagram source, exported artifact reference, and draft linkage.
- Result:
  - `diagrams/source/architecture.mmd` created. Mermaid `flowchart TD` source covering Stage 3 clients (Web, CLI), edge LB, stateless API tier (auth+RBAC+rate limit, rule-based keyword mapper, query parser+envelope validator, response shaper), Redis query-result cache with TTL plus version tag, PgBouncer connection pool, PostgreSQL primary with B-tree indexes, conditional read replica, conditional materialized aggregates, batch ingestion worker with quarantine table, observability plane. Every node label carries the FR-/NFR-/D-id it serves.
  - `diagrams/exported/architecture.md` created as the export-ready reference: render commands (mermaid.live and `mmdc`), embed checklist, and the component list the rendered image must contain.
  - `diagrams/source/README.md` and `diagrams/exported/README.md` updated to point at the active source and the export reference.
  - `drafts/insighta-labs-stage4-design.md` Section 7 (Architecture Diagram) replaces the previous placeholder. Section 7 links the source, links the export reference, embeds the Mermaid block inline for paste-fidelity, and states the Google Docs embed convention (image + link to original source).
  - Decision D-012 records the diagram format and labelling rule.
  - Journal entry `journal/2026-05-04-stage4-diagram.md` captures teach-back, failure modes, and next step.
  - Draft status banner updated to reflect that requirements, architecture, data flow, decisions, limitations, and diagram are complete.
- Verification command:
  - `python scripts/control_plane_check.py`
- Gate impact:
  - Diagram gate closes with evidence `E-006`.
  - Current packet advances from `B4-DIAGRAM-001` to `B4-SUBMISSION-001`.

## E-007 - Draft is submission-ready and QA reconciled

- Date: `2026-05-04`
- Scope: B4-SUBMISSION-001 final pass on `drafts/insighta-labs-stage4-design.md` and reconciliation of the QA checklist for Google Docs handoff.
- Result:
  - Section 0 (Context) tightened to one paragraph; Section 1 FR/NFR descriptions compressed without losing requirement ids; Section 2 component bullets condensed; Section 2.2 "What Is Deliberately Absent" tightened; Section 3 ingestion and query flows compressed (six-step ingestion, eight-step query path); Section 3.4 consistency boundary trimmed; Section 4.1 collapsed three sub-blocks into one for indexing/caching/observability; Section 5 limitations reduced to seven concise items plus the 10x next-lever sequence; Section 6.1 (real-time analytics) and Section 6.2 (true natural-language queries) tightened; the duplicated Mermaid code block removed from Section 7 (source link retained).
  - Section 8 (Submission Notes) added: final destination Google Docs, sharing requirement "Anyone with the link can view," length target 2-7 pages, diagram embed convention, sections-present manifest, deliberately-not-contained list, and a six-step pre-submission checklist for the operator.
  - Draft status banner updated to "submission-ready."
  - Decision D-013 records the final submission state: title, sharing, embedded PNG, original `.mmd` source link.
  - QA checklist diagram-and-submission items marked complete with evidence ids E-006 / E-007 and pointers to Section 8 and to `runtime_status.json`.
  - Defense bank updated with submission-readiness, post-submission improvement, and intentional-simplicity answers.
  - Journal entry `journal/2026-05-04-stage4-submission.md` captures teach-back, failure modes avoided, and the operator next step.
  - Estimated draft length: ~3,400 words / ~7-8 pages of source markdown; tables and bullets render more compactly in Google Docs at default styling, so the operator should land within the 2-7 page bound.
- Verification command:
  - `python scripts/control_plane_check.py`
- Gate impact:
  - Submission gate closes with evidence `E-007`.
  - Stage 4A is submission-ready; Google Docs upload remains an operator step per the Section 8 pre-submission checklist.

## E-008 - Final presentation simplified for 4A green path

- Date: `2026-05-05`
- Scope: Post-review simplification of the final Stage 4A submission package after the first Google Docs paste exceeded the page limit and the diagram over-signalled infrastructure complexity.
- Result:
  - `drafts/insighta-labs-stage4-design.md` replaced with the compact final submission draft (~1,140 words) containing only required sections: requirements, architecture, data flow, decisions/trade-offs, limitations/future evolution, and diagram placeholder.
  - `drafts/insighta-labs-stage4-design-compact.md` aligned to the same final submission text so there is no split-brain between canonical and compact drafts.
  - `diagrams/source/architecture.mmd` simplified to the core practical path: Stage 3 clients, existing backend API, query engine improvements, query-result cache, PostgreSQL, batch ingestion, observability, and a separate conditional scale-levers box.
  - `diagrams/exported/architecture.png` regenerated from the simplified design as a readable submission image.
  - `diagrams/exported/architecture.md`, diagram READMEs, decisions log, QA checklist, and `runtime_status.json` updated so governance no longer claims the older dense diagram is the final presentation.
- Verification command:
  - `python scripts/control_plane_check.py`
- Gate impact:
  - Stage 4A remains submission-ready.
  - Submission gate evidence is extended with `E-008`.
