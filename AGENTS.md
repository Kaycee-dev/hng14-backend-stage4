# Backend Stage 4A Agent Notes

## Read Order

1. `task_details.md`
2. `mentor_feedback.md`
3. `docs/backend-stage4-control-plane/README.md`
4. `config/runtime_status.json`
5. `CURRENT_TASK`
6. The task packet named by `CURRENT_TASK`

## Operating Rules

- This repo is in design-document governance mode for the Insighta Labs+ Stage 4 scaling task.
- Do not create backend implementation, benchmark, load-test, Docker, service, or prototype files while `config/runtime_status.json` has `experiments_allowed` set to `false`.
- The final deliverable is a Google Docs system design document, not runnable application code.
- Stage 3 stays intact conceptually: auth, RBAC, CLI, and web portal must not be redesigned away or treated as broken.
- Every design claim must map back to the official brief or to a recorded design decision.
- Do not claim true natural-language or LLM query support. The brief states structured filters, aggregations, and simple rule-based keyword mapping only.
- Avoid unjustified microservices, queues, multi-region architecture, streaming systems, and calculations that do not support a concrete decision.
- Every non-trivial slice must update the active task packet, evidence log, decisions log when a lasting choice changes, QA checklist, defense bank, and same-day journal.
- Do not close a gate unless the gate cites an evidence id present in `docs/backend-stage4-control-plane/05_evidence_log.md`.
- Any user-facing claim in `README.md`, the design draft, diagram notes, or submission notes must match `config/runtime_status.json`.

## Design-With-Me Protocol

- Each slice starts with a short teach-back note: concept, design decision, expected deliverable, and likely interview question.
- Each slice ends with proof: updated document paths, evidence id, and a plain-English explanation of what changed.
- Failures and rejected ideas must be recorded. Debugging and trade-off evidence are part of the defense trail.
- The operator must be able to explain the slice without relying on AI before the next slice closes.
