# Insighta Labs+ Stage 4B Solution

## Repository context

Stage 4 builds on Stage 3. This repository contains the complete Stage 3
backend (Node.js/Express, PostgreSQL, GitHub OAuth, RBAC, CLI, web portal)
as its baseline and adds the Stage 4A system-design artifacts and Stage 4B
implementation described below.

Stage 4A design document: `drafts/insighta-labs-stage4-design.md`
Stage 4A decisions log: `docs/backend-stage4-control-plane/04_decisions_log.md`

The only new API surface added by Stage 4B is:

```http
POST /api/profiles/import
Authorization: Bearer <token>
X-API-Version: 1
Content-Type: multipart/form-data
file field: file
```

---

## 1. Query Performance

### Composite indexes (`migrations/004_stage4b_optimization.sql`)

| Index | Justification |
|---|---|
| `(country_id, gender, age)` | Covers the most selective demographic path: country + gender equality with age range. PostgreSQL uses leading equality columns to narrow the scan, then range-filters on `age`. |
| `(gender, age)` | Covers gender-filtered age range queries when country is absent. |
| `(country_id, age)` | Covers country-filtered age range queries when gender is absent. |

Existing single-column indexes from Stage 2 (`gender`, `age`, `country_id`, `age_group`, `gender_probability`, `country_probability`, `created_at`) are preserved unchanged. No speculative indexes were added — every composite index maps to a real filter combination emitted by `buildWhere`.

**Trade-off:** Each additional index adds write overhead during `INSERT`. Accepted because the workload is read-heavy and writes are periodic batch operations.

### `COUNT(*) OVER()` query restructuring (`src/repo/profiles.js`)

The original `queryProfiles` ran two sequential queries: one for the page rows, one for `SELECT COUNT(*)`. Stage 4B replaces this with:

```sql
SELECT COUNT(*) OVER()::int AS total_count, id, name, ...
FROM profiles
WHERE ...
ORDER BY ...
LIMIT $n OFFSET $n
```

PostgreSQL computes the window function over the full filtered set while retrieving the page in one round trip. When a requested page returns no rows (the window function emits no rows), a separate `SELECT COUNT(*)` fallback runs to preserve correct `total` and pagination metadata.

**Before/after measurements:**

| Scenario | Query time |
|---|---|
| Local app (200 seeded rows), cold request | 56.928 ms |
| Local app (200 seeded rows), cached hit | 24.331 ms |
| Remote DB (2,030 profiles), old two-query flow — average of 5 runs | 712.066 ms |
| Remote DB (2,030 profiles), new `COUNT(*) OVER()` — average of 5 runs | 369.014 ms |

The remote DB timing is a real before/after measurement against the same database and dataset. To reproduce:

```powershell
$env:DATABASE_URL = "<postgres-url>"
npm run migrate

$headers = @{
  Authorization  = "Bearer $env:INSIGHTA_TOKEN"
  "X-API-Version" = "1"
}
1..10 | ForEach-Object {
  Measure-Command {
    Invoke-RestMethod `
      -Headers $headers `
      "$env:INSIGHTA_API_URL/api/profiles?gender=female&country_id=NG&min_age=20&max_age=45&page=1&limit=10" `
      | Out-Null
  } | Select-Object TotalMilliseconds
}
```

### Connection pool (`src/db.js`)

`pg.Pool` with environment-backed defaults:

| Env var | Default | Purpose |
|---|---|---|
| `PG_POOL_MAX` | `10` | Max concurrent connections |
| `PG_IDLE_TIMEOUT_MS` | `30000` | Close idle connections after 30 s |
| `PG_CONNECTION_TIMEOUT_MS` | `5000` | Reject acquire after 5 s |

---

## 2. Query Normalization and Cache

### Normalization (`src/lib/queryCache.js`)

Before a cache key is computed, `normalizeProfileQueryFilters` canonicalises the parsed filter object:

1. Fill pagination defaults (`page=1`, `limit=10`, `sort_by='created_at'`, `order='asc'`)
2. Lowercase `gender`, `age_group`, `sort_by`, `order`
3. Uppercase `country_id`
4. Coerce `min_age`, `max_age`, `min_gender_probability`, `min_country_probability` to numbers
5. Deduplicate and sort `country_ids` array; collapse a single-element array to `country_id`
6. Normalise each `any` OR clause recursively; deduplicate and sort clauses lexicographically
7. Sort all object keys alphabetically via `sortObject`

The cache key is `JSON.stringify(sortObject(normalized))` — a deterministic string with no hashing. Two queries that express the same intent produce the same key regardless of phrasing or property insertion order.

**Example:** `"Nigerian females between ages 20 and 45"` and `"Women aged 20-45 living in Nigeria"` both resolve to:

```
{"country_id":"NG","gender":"female","limit":10,"max_age":45,"min_age":20,"order":"asc","page":1,"sort_by":"created_at"}
```

### In-memory cache (`src/lib/queryCache.js`)

| Env var | Default | Purpose |
|---|---|---|
| `PROFILE_QUERY_CACHE_TTL_MS` | `30000` | Entry TTL (30 s) |
| `PROFILE_QUERY_CACHE_MAX_ENTRIES` | `500` | LRU capacity |

Implementation: a plain `Map` (insertion-order iteration provides LRU semantics). On get, the entry is deleted and re-inserted to move it to the tail. When `size > maxEntries`, the oldest entry is evicted.

**What is cached:** Successful results of `GET /api/profiles` and `GET /api/profiles/search`. CSV export (`GET /api/profiles/export`) is never cached.

**Invalidation:** The cache is fully cleared after:
- `POST /api/profiles` (create)
- `DELETE /api/profiles/:id` (delete)
- Each successfully flushed CSV import batch (via `onBatchComplete` callback)

The cache is process-local. Multiple app instances would not share entries — Redis is the documented next lever (Stage 4A decision D-007).

---

## 3. CSV Data Ingestion

### Endpoint

```http
POST /api/profiles/import
Authorization: Bearer <admin-token>
X-API-Version: 1
Content-Type: multipart/form-data
```

Admin-only via `requireRole('admin')`.

### Streaming and batching

`importProfilesFromMultipart` (`src/services/profileImport.js`) uses **Busboy** to stream the multipart body and **csv-parse** in async-iterator mode for row-by-row processing. The file is never fully buffered. Valid rows are accumulated in a `batch` array (default 1000 rows). When `batch.length >= 1000`, `flushBatch()` executes one `INSERT ... VALUES (...),... ON CONFLICT DO NOTHING` statement.

Batch size 1000: 9 columns * 1000 rows = 9000 parameters, well within PostgreSQL's 65535-param limit.

### Duplicate handling

Duplicates are counted from three sources:
1. **Within the upload** — `seenNames` Set detects repeated names before any DB call
2. **Existing database rows** — `ON CONFLICT DO NOTHING` skips conflicting rows; `candidates.length - insertedRows.length` gives this count per batch
3. **Race-condition conflicts** — concurrent uploads resolved by the same unique index; losing INSERTs are silently skipped and counted

### Partial failure

No wrapping transaction. Each `flushBatch()` is an independent INSERT. Rows inserted before a failure remain committed. This satisfies the task requirement: "rows already inserted must remain. The upload does not roll back."

### Row validation

| Failure | Reason key |
|---|---|
| Any required column missing or empty | `missing_fields` |
| Duplicate name in same file | `duplicate_name` |
| Gender not `male` or `female` | `invalid_gender` |
| Age not a non-negative integer | `invalid_age` |
| Country code not in registry | `malformed_row` |
| Probability outside [0, 1] | `malformed_row` |
| csv-parse tokenisation failure | `malformed_row` |

Required columns: `name`, `gender`, `age`, `country_id`, `gender_probability`, `country_probability`

### Response shape

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

### Smoke test

```powershell
@"
name,gender,age,country_id,gender_probability,country_probability
Smoke User,female,29,NG,0.91,0.84
"@ | Set-Content -Encoding UTF8 smoke_profiles.csv

curl.exe -X POST "$env:INSIGHTA_API_URL/api/profiles/import" `
  -H "Authorization: Bearer $env:INSIGHTA_TOKEN" `
  -H "X-API-Version: 1" `
  -F "file=@smoke_profiles.csv;type=text/csv"
```

---

## 4. Edge Cases

- Missing `file` field in multipart -> 400 "CSV file is required"
- Non-multipart Content-Type -> 400
- Analyst role on import -> 403
- Wrong column count -> `malformed_row`
- Empty required field value -> `missing_fields`
- Negative or non-integer age -> `invalid_age`
- Unknown country code -> `malformed_row`
- Probability out of [0, 1] -> `malformed_row`
- One bad row never fails the whole upload
- Concurrent uploads: unique index + `ON CONFLICT DO NOTHING` prevents duplicate inserts

---

## 5. Trade-offs and Limitations

- Cache is process-local. Multiple app instances each maintain independent caches. Redis is the documented next lever.
- No explicit statement timeout on database connections (Stage 4A design D-011 specified one; not implemented in code).
- No file size limit on CSV uploads. Busboy streams without a `fileSize` cap.
- Cache stampede is possible after `cache.clear()` under high concurrency. No mutex or promise deduplication.
- `seenNames` Set grows with unique valid names in an upload. For 500,000 all-unique rows this is ~500,000 short strings in memory.
- Composite indexes add write overhead (accepted; writes are periodic batch operations).

---

## 6. Stage 3 Compatibility Confirmation

Stage 3 behavior is fully preserved:
- `GET /api/profiles`, `GET /api/profiles/search`, `GET /api/profiles/export` response shapes are unchanged
- Auth, RBAC, pagination, CSV export, API versioning, rate limiting, CORS all unchanged
- Test-login / grader-compatibility paths preserved
- All 69 tests pass

---

## 7. Verification Commands

```bash
npm install        # 0 vulnerabilities
npm run lint       # syntax-check all JS
npm test           # 69/69 pass
npm run migrate    # requires DATABASE_URL; applies 001-004
```

| Command | Result |
|---|---|
| `npm install` | Passed, 0 vulnerabilities |
| `npm run lint` | Passed |
| `npm test` | Passed, 69/69 |
| Remote DB (2,030 rows) old flow | avg 712.066 ms |
| Remote DB (2,030 rows) new flow | avg 369.014 ms |
| Local cache cold | 56.928 ms |
| Local cache hit | 24.331 ms |

---

## 8. Stage 4A and Stage 4B Deliverables in This Repository

| Deliverable | Location |
|---|---|
| Stage 4A design document | `drafts/insighta-labs-stage4-design.md` |
| Stage 4A compact version | `drafts/insighta-labs-stage4-design-compact.md` |
| Stage 4A decisions log | `docs/backend-stage4-control-plane/04_decisions_log.md` |
| Stage 4A architecture diagram source | `diagrams/source/architecture.mmd` |
| Stage 4A governance | `docs/backend-stage4-control-plane/` |
| Stage 4B implementation | `src/`, `migrations/004_stage4b_optimization.sql` |
| Stage 4B tests | `test/queryCache.test.js`, `test/queryRepo.test.js`, `test/stage4b.test.js` |
| Stage 4B control plane | `docs/stage4b-control-plane/` |
