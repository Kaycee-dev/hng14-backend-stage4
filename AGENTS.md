# Backend Stage 4 Agent Notes

## Repository Role

This is the Stage 4 submission repository for Insighta Labs+. It contains:
- The Stage 3 backend implementation (baseline)
- Stage 4A system design artifacts (`docs/backend-stage4-control-plane/`, `drafts/`, `diagrams/`)
- Stage 4B implementation code (`src/`, `migrations/004_stage4b_optimization.sql`, tests)
- Repo-ready `cli/` and `web/` packages

## Read Order (for a new agent)

1. `task_details.md` — Stage 4A spec
2. `task_details_4B.md` — Stage 4B spec
3. `SOLUTION.md` — Stage 4B implementation summary
4. `docs/backend-stage4-control-plane/04_decisions_log.md` — design decisions
5. `src/app.js` — Express app entry
6. `src/lib/queryCache.js` — normalization and cache
7. `src/services/profileImport.js` — CSV ingestion
8. `src/repo/profiles.js` — database layer
9. `migrations/` — schema history

## Operating Rules

- This repo is the Stage 4 implementation AND design repo. It is not governance-only.
- Preserve Stage 3 behavior: auth, RBAC, existing response shapes, API versioning, pagination, CSV export.
- The only new API surface is `POST /api/profiles/import` (admin-only, multipart).
- Do not add Redis, external queues, LLM/AI query behavior, or horizontal scaling infra.
- Query model is structured filters + deterministic rule-based keyword mapping only (no LLM).
- Do not commit `.env` files or secrets.
- Run `npm test` and `npm run lint` before committing implementation changes.
- Keep `SOLUTION.md` and evidence logs current.
