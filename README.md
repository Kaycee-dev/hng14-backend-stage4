# Insighta Labs+ — Stage 4

HNG14 Backend Stage 4: Scaling Design (4A) and Implementation (4B) for the Insighta Labs+ demographic intelligence platform.

This repository is the Stage 4 submission. It contains the complete Stage 3 backend implementation as its baseline, the Stage 4A system-design artifacts, and the Stage 4B optimisation and ingestion code.

## Repository Topology

This repo is the backend source of truth and also ships repo-ready `cli/` and `web/` packages for the three-repository split required by Stage 3.

| Directory | Purpose |
|-----------|---------|
| `src/` | Node.js/Express backend (Stage 3 base + Stage 4B additions) |
| `migrations/` | PostgreSQL migrations 001–004 (Stage 4B adds 004) |
| `test/` | All automated tests (Stage 3 + Stage 4B suites) |
| `cli/` | Node.js CLI package (`insighta` global binary) |
| `web/` | Next.js web portal (server-side backend calls) |
| `docs/backend-stage4-control-plane/` | Stage 4A design governance, decisions log, evidence |
| `docs/stage4b-control-plane/` | Stage 4B implementation governance |
| `drafts/` | Stage 4A design document drafts |
| `diagrams/` | Architecture diagram source (Mermaid) and exports |
| `scripts/` | Lint checker, docx build script |

## Stage 4A — System Design

Design document: `drafts/insighta-labs-stage4-design.md`  
Compact version: `drafts/insighta-labs-stage4-design-compact.md`  
Architecture diagram source: `diagrams/source/architecture.mmd`  
Decisions log: `docs/backend-stage4-control-plane/04_decisions_log.md`

Key design decisions:
- In-process query-result cache (TTL + LRU, no Redis required at this scale)
- Composite B-tree indexes on the three most common demographic filter combinations
- `COUNT(*) OVER()` window function to eliminate one database round trip per paginated request
- Streaming CSV ingestion (Busboy + csv-parse) with per-batch inserts, no full-file buffer
- Query normalization before cache lookup so equivalent filter expressions share one cache entry
- Query model is structured filters + deterministic rule-based keyword mapping — no AI/LLM

## Stage 4B — Implementation

See `SOLUTION.md` for the full approach, decisions, trade-offs, and measurements.

### What changed

| Area | File(s) |
|------|---------|
| Composite indexes | `migrations/004_stage4b_optimization.sql` |
| Connection pool config | `src/db.js` |
| `COUNT(*) OVER()` query | `src/repo/profiles.js` |
| Query normalization + cache | `src/lib/queryCache.js` |
| CSV import endpoint | `src/services/profileImport.js`, `src/routes/profiles.js` |

### New endpoint

```http
POST /api/profiles/import
Authorization: Bearer <admin-token>
X-API-Version: 1
Content-Type: multipart/form-data
file: <csv-file>
```

Admin-only. Returns:
```json
{
  "status": "success",
  "total_rows": 50000,
  "inserted": 48231,
  "skipped": 1769,
  "reasons": {
    "duplicate_name": 1203,
    "invalid_age": 312,
    "missing_fields": 254,
    "invalid_gender": 0,
    "malformed_row": 0
  }
}
```

## Setup

```bash
cp .env.example .env
# edit .env: set DATABASE_URL, JWT_SECRET, GITHUB_* OAuth credentials
npm install
npm run migrate
npm start
```

## Available Commands

| Command | Purpose |
|---------|---------|
| `npm start` | Start production server |
| `npm run migrate` | Run all pending SQL migrations |
| `npm run seed` | Seed sample profiles |
| `npm run lint` | Syntax-check all JS files |
| `npm test` | Run full test suite (69 tests) |

## Environment Variables

See `.env.example` for the full list. Required:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Secret for signing access tokens |
| `GITHUB_WEB_CLIENT_ID` / `_SECRET` | GitHub OAuth app for web login |
| `GITHUB_CLI_CLIENT_ID` / `_SECRET` | GitHub OAuth app for CLI login |

Optional tuning:

| Variable | Default | Description |
|----------|---------|-------------|
| `PG_POOL_MAX` | `10` | Max pg pool connections |
| `PG_IDLE_TIMEOUT_MS` | `30000` | Idle connection timeout |
| `PG_CONNECTION_TIMEOUT_MS` | `5000` | Connection acquire timeout |
| `PROFILE_QUERY_CACHE_TTL_MS` | `30000` | Cache entry TTL |
| `PROFILE_QUERY_CACHE_MAX_ENTRIES` | `500` | LRU cache capacity |

## Stage 3 Compatibility

Stage 3 behavior is fully preserved:
- All existing `GET /api/profiles`, `GET /api/profiles/search`, `GET /api/profiles/export` response shapes are unchanged
- Auth, RBAC, pagination, CSV export, and API versioning work identically
- All 69 tests (Stage 3 + Stage 4B) pass
