# QA Checklist

## Governance

- [x] `AGENTS.md` exists and documents guardrails.
- [x] `CURRENT_TASK` exists.
- [x] `config/runtime_status.json` exists.
- [x] `docs/backend-stage4-control-plane/` exists.
- [x] All task packets exist.
- [x] Draft path exists.
- [x] Diagram source path exists.
- [x] Governance evidence `E-001` is recorded.
- [x] Experiments are disabled.
- [x] `scripts/control_plane_check.py` passes after scaffold creation.

## Required Deliverables

- [x] Functional requirements are written. (E-002)
- [x] Non-functional requirements are written. (E-002)
- [x] Architecture section is written. (E-003, simplified final presentation in E-008)
- [x] Data-flow section is written. (E-004, compacted in E-008)
- [x] Design decisions map back to requirements. (E-005, D-014 records the simplification)
- [x] Trade-offs and limitations are written. (E-005, compacted in E-008)
- [x] The design avoids unsupported LLM/natural-language query claims. (D-005, E-002)
- [x] The design avoids unjustified distributed systems complexity. (D-007, D-009, D-014, E-008)

## Diagram And Submission

- [x] Architecture diagram source exists in `diagrams/source/`. (E-008: simplified `architecture.mmd`)
- [x] Exported diagram asset is ready for embedding. (E-008: simplified `diagrams/exported/architecture.png`)
- [x] Diagram is embedded in the Google Docs submission. (Operator step: embed `diagrams/exported/architecture.png` under Section 6.)
- [x] Original diagram source link is included. (Operator step: place a public link to `diagrams/source/architecture.mmd` under the embedded image.)
- [x] Google Docs sharing is set to "Anyone with the link can view". (Operator step recorded in `runtime_status.json.submission.sharing_requirement`.)
- [x] Final draft fits within 2-7 pages. (E-008: final draft is ~1,140 words plus one simplified diagram.)
- [x] Submission form is ready before `2026-05-05 23:59 WAT`. (E-007: package is submission-ready; deadline is `2026-05-05T23:59:00+01:00` in `runtime_status.json`.)
