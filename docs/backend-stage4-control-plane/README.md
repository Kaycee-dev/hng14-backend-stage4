# Backend Stage 4A Control Plane

This directory is the operating system for the Insighta Labs+ Stage 4 system design task. It exists to prevent shallow architecture claims, stale proof, and interview answers that cannot be defended.

## How To Resume

1. Read `config/runtime_status.json`.
2. Confirm `CURRENT_TASK` matches `current_packet`.
3. Open the matching file in `docs/backend-stage4-control-plane/task-packets/`.
4. Run `python scripts/control_plane_check.py`.
5. Continue only within the scope of the active packet.

## Documents

- `01_brief_traceability.md`: maps the official task to final design-document proof.
- `02_execution_roadmap.md`: ordered work packets.
- `03_design_with_me_protocol.md`: teach-back and explainability rules.
- `04_decisions_log.md`: decisions, alternatives, rationale, and defense notes.
- `05_evidence_log.md`: document updates, artifacts, failures, and proof.
- `06_validation_strategy.md`: design validation gates.
- `07_qa_checklist.md`: final submission checklist.
- `08_interview_defense_bank.md`: questions to rehearse without AI.
- `09_submission_and_diagram_plan.md`: Google Docs and diagram workflow.

## Current Rule

Experiments and implementation are not allowed in this repo. Stage 4A is submission-ready; use the compact final draft and simplified diagram recorded in `config/runtime_status.json` and E-008.
