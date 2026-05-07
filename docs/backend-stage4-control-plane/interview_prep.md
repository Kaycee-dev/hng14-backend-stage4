# Interview Prep — Backend Stage 4 (Insighta Labs+)

**Developer:** Kelechi Uba
**Generated from:** verified implementation in `backend-wizards-stage1-2-3/` + governance in `backend-stage4/`
**Date:** 2026-05-07

---

## Section 1: One-Paragraph Pitch

Insighta Labs+ is a demographic intelligence platform that stores structured profile data (name, gender, age, country) and serves it to analysts via a CLI and a Next.js web portal, both authenticated through GitHub OAuth with JWT-based RBAC. Stage 4A produced a scaling design document: it identified three pressure points — repeated query patterns hammering the database, linear-scan queries without index support, and no mechanism for large-scale data uploads — and proposed a practical response using normalized caching, composite indexes, and streaming batch ingestion, deliberately without microservices, queues, or a search engine. Stage 4B turned that design into working code: `migrations/004_stage4b_optimization.sql` adds three composite B-tree indexes on `(country_id, gender, age)`, `(gender, age)`, and `(country_id, age)`; `src/lib/queryCache.js` adds a 500-entry in-memory LRU/TTL cache whose keys are deterministic JSON serialisations of normalised filter objects, so `"Nigerian females between ages 20 and 45"` and `"Women aged 20–45 living in Nigeria"` produce the same key and share the same cache entry; `src/services/profileImport.js` streams CSV uploads through Busboy and csv-parse in batches of 1,000 rows, inserting each batch with a single `INSERT … ON CONFLICT DO NOTHING`, leaving partial progress intact if a later batch fails.

---

## Section 2: System Architecture Map

```
┌─────────────────────────────────────────────────────────┐
│  CLIENTS                                                  │
│  CLI (Node.js)          Next.js web portal               │
└──────────────────┬──────────────────────────────────────┘
                   │  HTTPS  X-API-Version: 1  Bearer JWT
                   ▼
┌─────────────────────────────────────────────────────────┐
│  EXISTING BACKEND API  (Node.js / Express)               │
│  app.js                                                   │
│   ├─ cors, requestLogger, express.json (10kb limit)      │
│   ├─ requireApiVersion  (X-API-Version header)           │
│   ├─ requireAuth        (JWT validation + user.role)     │
│   ├─ rateLimit          (in-memory token bucket)         │
│   │                                                       │
│   └─ /api/profiles  routes/profiles.js                   │
│       ├─ GET /          validateListQuery → [CACHE PATH] │
│       ├─ GET /search    validateSearchQuery              │
│       │                 parseNaturalLanguageQuery        │
│       │                 → [CACHE PATH]                   │
│       ├─ GET /export    validateExportQuery → DB direct  │
│       ├─ POST /         insertOrGet → cache.clear()      │
│       ├─ POST /import   [CSV INGESTION PATH]             │
│       └─ DELETE /:id    deleteById → cache.clear()       │
└───────────┬─────────────────────────┬───────────────────┘
            │                         │
            ▼  NORMALIZATION          │  (CSV path only)
┌───────────────────────┐             │
│ lib/queryCache.js     │             │
│ normalizeProfileQuery │             │
│ Filters()             │             │
│  • fill defaults      │             │
│  • lowercase gender,  │             │
│    age_group, sort     │             │
│  • uppercase country   │             │
│  • coerce numerics     │             │
│  • dedup+sort          │             │
│    country_ids         │             │
│  • sort any[] clauses  │             │
│  • sort object keys    │             │
│ → stableStringify()    │             │
│   = cache key          │             │
└────────┬──────────────┘             │
         │                            │
         ▼ CACHE LOOKUP               │
┌────────────────────┐                │
│ In-memory LRU/TTL  │                │
│ Map (500 entries,  │                │
│ 30s TTL default)   │                │
│  HIT → return      │                │
│  MISS → continue   │                │
└────────┬───────────┘                │
         │ on MISS                    │ CSV path
         ▼                            ▼
┌────────────────────────────────────────────────────────┐
│  CONNECTION POOL  (db.js — pg.Pool)                     │
│  max=10, idleTimeout=30s, connectionTimeout=5s          │
│  pool.query(text, params)                               │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│  POSTGRESQL  (single primary)                           │
│  profiles table                                         │
│  Single-col: gender, age_group, country_id, age,        │
│              gender_probability, country_probability,   │
│              created_at                                  │
│  Composite (Stage 4B):                                  │
│    (country_id, gender, age)                            │
│    (gender, age)                                        │
│    (country_id, age)                                    │
│  Unique: LOWER(BTRIM(name))                             │
│                                                         │
│  Query path: COUNT(*) OVER() window — one round trip    │
│  CSV path:   INSERT … ON CONFLICT DO NOTHING — bulk     │
└────────────────────────────────────────────────────────┘

Normalization position: BEFORE cache lookup, AFTER validation
CSV ingestion path: diverges at POST /import, bypasses cache lookup,
  writes to DB in 1000-row batches, then clears cache after each batch
Export path (GET /export): bypasses cache entirely, hits DB directly
```

### File-by-File Responsibility Table

| File | Responsibility |
|------|---------------|
| `src/app.js` | Assembles Express app: CORS, logging, rate limiting, auth middleware, route mounting |
| `src/db.js` | Creates and exports the `pg.Pool` with env-backed connection pool settings |
| `src/routes/profiles.js` | HTTP route handlers for all profile endpoints including `/import` |
| `src/lib/queryCache.js` | In-memory LRU/TTL cache, filter normalisation, and canonical cache key generation |
| `src/lib/queryValidation.js` | Validates and type-coerces raw HTTP query parameters before they reach the cache |
| `src/services/queryParser.js` | Maps natural-language search strings to structured filter objects |
| `src/repo/profiles.js` | All database interactions: `queryProfiles`, `insertOrGet`, `insertManyIgnoreDuplicates`, `exportProfiles` |
| `src/services/profileImport.js` | Busboy multipart + csv-parse streaming, row validation, batched bulk insert |
| `src/services/classify.js` | `ageGroup(age)` — maps a numeric age to child/teenager/adult/senior |
| `src/lib/profiles.js` | Pure normalisation helpers: `normalizeName`, `normalizeGender`, `normalizeCountryId`, `VALID_GENDERS` |
| `src/lib/countries.js` | Country registry: `getCountryName(code)`, `findCountries(text)`, `normalizeCountryLookup(text)` |
| `migrations/001_init.sql` | Initial `profiles` table schema |
| `migrations/002_stage2_query_engine.sql` | Schema clean-up and single-column indexes from Stage 2 |
| `migrations/003_stage3_secure_access.sql` | `users`, `refresh_tokens`, `web_auth_codes` tables for GitHub OAuth |
| `migrations/004_stage4b_optimization.sql` | Three composite indexes added by Stage 4B |

---

## Section 3: Complete Data-Flow Walkthroughs

### Query Path (with caching)

```
GET /api/profiles?gender=female&country_id=NG&min_age=20&max_age=45
  arrives at routes/profiles.js:85  (router.get '/'))
  │
  ├─ requireApiVersion (middleware/apiVersion.js)
  │   checks X-API-Version: 1 header
  │
  ├─ requireAuth (middleware/auth.js)
  │   validates Bearer JWT → attaches req.user (id, role)
  │
  ├─ rateLimit (app.js:82)
  │   bucket key: req.user.id; 60 req/min window
  │
  ├─ validateListQuery(req.query)  (lib/queryValidation.js:172)
  │   • ensureAllowedKeys: rejects unknown params with 422
  │   • reads and type-coerces: gender→lowercase 'female',
  │     country_id→uppercase 'NG', min_age/max_age→integers,
  │     page→1 (default), limit→10 (default, clamped at 50),
  │     sort_by→'created_at' (default), order→'asc' (default)
  │   • validates age range: min_age ≤ max_age
  │   returns structured filters object
  │
  ├─ queryProfilesWithCache(repo, cache, filters)
  │   (lib/queryCache.js:159)
  │   │
  │   ├─ profileQueryCacheKey(filters)  (lib/queryCache.js:107)
  │   │   → normalizeProfileQueryFilters(filters)  (line 70)
  │   │     fills defaults, lowercases gender/age_group/sort fields,
  │   │     uppercases country_id, coerces numbers,
  │   │     sorts object keys via sortObject()
  │   │   → stableStringify(normalized)  (line 27)
  │   │     = deterministic JSON string = cache key
  │   │
  │   ├─ cache.get(key)  (line 119)
  │   │   HIT (entry exists and not expired):
  │   │   │   LRU refresh (delete+re-insert in Map), hits++
  │   │   │   return clone(entry.value) → skip to response
  │   │   │
  │   │   MISS (no entry or TTL expired):
  │   │       misses++, continue
  │   │
  │   ├─ [MISS path] repo.queryProfiles(filters)
  │   │   (repo/profiles.js:231)
  │   │   │
  │   │   ├─ buildWhere(options) → WHERE clause + params
  │   │   │   appends equality conditions for gender, age_group,
  │   │   │   country_id; range conditions for min_age, max_age;
  │   │   │   IN clause for country_ids; OR block for any[] clauses
  │   │   │
  │   │   ├─ sortClause(options) → ORDER BY country_id ASC, id ASC
  │   │   │
  │   │   ├─ db.query(text, params)  (db.js:40)
  │   │   │   pool.query() acquires connection from pg.Pool
  │   │   │   SQL uses COUNT(*) OVER()::int AS total_count
  │   │   │   → one round trip for rows + total count
  │   │   │   if page has 0 rows: fallback COUNT(*) query
  │   │   │
  │   │   returns { page, limit, total, data: rows.map(serialize) }
  │   │
  │   └─ cache.set(key, result)  (line 136)
  │       stores clone(result) with expiresAt = now + 30000ms
  │       if entries > 500: evicts oldest Map entry
  │
  └─ success(res, 200, shapePagination(req, result))
      withPaginationLinks() adds next/prev links → JSON response
```

### Search Path (natural language)

```
GET /api/profiles/search?q=Nigerian+females+between+ages+20+and+45
  arrives at routes/profiles.js:108  (router.get '/search')
  │
  ├─ [same auth + rate limit middleware]
  │
  ├─ validateSearchQuery(req.query)  (lib/queryValidation.js:188)
  │   enforces allowed keys: q, sort_by, order, page, limit only
  │   returns { q, page, limit, sort_by, order, ... }
  │
  ├─ parseNaturalLanguageQuery(q)  (services/queryParser.js:321)
  │   │
  │   ├─ prepareInput: '65+' → '65 plus'
  │   ├─ normalizeCountryLookup: maps demonyms/names → country_id
  │   │   'Nigerian' → 'NG'
  │   │
  │   ├─ parseSort: checks for 'oldest first', 'newest first', etc.
  │   │
  │   ├─ splitSegments: splits on 'and/or' + segment starters
  │   │   single segment here (no multi-gender OR query)
  │   │
  │   └─ parseClause(normalizedText):
  │       gender: 'females' → 'female'
  │       findAgeRange: 'between ages 20 and 45' → {min_age:20, max_age:45}
  │       country_id: 'Nigerian' → 'NG'
  │       returns { gender:'female', min_age:20, max_age:45, country_id:'NG' }
  │
  ├─ merge parseNaturalLanguageQuery result with validateSearchQuery
  │   result (page, limit, sort_by, order)
  │
  └─ [same queryProfilesWithCache path as GET /]
```

### CSV Ingestion Path

```
POST /api/profiles/import
  Content-Type: multipart/form-data
  Authorization: Bearer <admin-token>
  X-API-Version: 1
  arrives at routes/profiles.js:72  (router.post '/import')
  │
  ├─ adminOnly middleware (requireRole('admin'))
  │   req.user.role !== 'admin' → 403
  │
  ├─ importProfilesFromMultipart(req, { repo, batchSize, onBatchComplete })
  │   (services/profileImport.js:185)
  │   │
  │   ├─ checks Content-Type starts with 'multipart/form-data' → 400 if not
  │   │
  │   ├─ Busboy({ headers: req.headers, limits: { files: 1 } })
  │   │   req.pipe(busboy) — streaming, no full-file buffering
  │   │
  │   ├─ busboy 'file' event (fieldname must be 'file')
  │   │   → importProfilesFromCsvStream(fileStream, options)
  │   │     (services/profileImport.js:136)
  │   │
  │   └─ busboy 'finish' → await importPromise → resolve/reject
  │
  └─ importProfilesFromCsvStream(stream, options):
      │
      ├─ summary = { total_rows:0, inserted:0, reasons:{...5 keys} }
      ├─ seenNames = new Set()   (in-memory dedup within upload)
      ├─ batch = []
      │
      ├─ csv-parse parser config:
      │   bom:true, columns:true (header row), skip_empty_lines:true,
      │   skip_records_with_error:true, trim:true
      │   on_skip callback: total_rows++, malformed_row++
      │
      ├─ stream.pipe(parser)
      │   for await (const row of parser):  ← streaming, 1 row at a time
      │   │
      │   ├─ total_rows++
      │   │
      │   ├─ validateRow(row, seenNames, summary)
      │   │   (services/profileImport.js:75)
      │   │   checks: typeof row !== 'object' → malformed_row
      │   │   checks: hasMissingFields → missing_fields
      │   │   checks: seenNames.has(nameKey) → duplicate_name
      │   │   checks: gender not in VALID_GENDERS → invalid_gender
      │   │   checks: age not non-negative integer → invalid_age
      │   │   checks: country_id not a valid 2-letter ISO → malformed_row
      │   │   checks: probability not in [0,1] → malformed_row
      │   │   passes: seenNames.add(nameKey), returns candidate object
      │   │
      │   ├─ if null candidate: continue (row skipped, reason incremented)
      │   │
      │   ├─ batch.push(candidate)
      │   │
      │   └─ if batch.length >= 1000: flushBatch()
      │
      ├─ flushBatch() (at end of file, final partial batch):
      │   candidates = batch.splice(0, batch.length)
      │   repo.insertManyIgnoreDuplicates(candidates)
      │   (repo/profiles.js:161)
      │   │
      │   └─ single SQL:
      │       INSERT INTO profiles (id, name, gender, ...) VALUES (...),...
      │       ON CONFLICT ((LOWER(BTRIM(name)))) DO NOTHING
      │       RETURNING ...
      │       ← one parameterised statement per batch, no wrapping transaction
      │
      │   inserted = insertedRows.length
      │   summary.inserted += inserted
      │   summary.reasons.duplicate_name += candidates.length - inserted
      │   await onBatchComplete()  → profileQueryCache.clear()
      │
      └─ return finalSummary(summary):
          { total_rows, inserted, skipped: sum(reasons), reasons }
```

**Partial failure behaviour:** Each `flushBatch()` call runs an independent `INSERT`. If the process crashes after batch 3 of 10, the first 3 batches' rows remain committed in the database (no outer transaction). The fourth batch simply did not run. This satisfies the task requirement: "rows already inserted must remain."

---

## Section 4: Query Optimization Deep Dive

### Indexes added (migration 004)

Three composite B-tree indexes are added in `migrations/004_stage4b_optimization.sql`:

```sql
CREATE INDEX IF NOT EXISTS profiles_country_gender_age_idx
  ON profiles (country_id, gender, age);

CREATE INDEX IF NOT EXISTS profiles_gender_age_idx
  ON profiles (gender, age);

CREATE INDEX IF NOT EXISTS profiles_country_age_idx
  ON profiles (country_id, age);
```

**Why these three columns:** The query parser and `buildWhere` emit equality conditions on `country_id` and `gender`, and range conditions on `age` (`age >= $n`, `age <= $n`). PostgreSQL can use a composite B-tree index where the leading columns are equality predicates and the trailing column is a range — the most selective composite path for demographic queries. The three variants cover the three most common filter combinations: all three fields, gender + age only (no country filter), country + age only (no gender filter).

**Existing single-column indexes** (from migration 002) remain intact: `gender`, `age_group`, `country_id`, `age`, `gender_probability`, `country_probability`, `created_at`. The composite indexes supplement them for multi-column filter queries.

**Trade-off:** Each additional index adds write overhead during `INSERT` and `UPDATE`. The design accepts this because the workload is read-heavy; the brief explicitly states writes are periodic batch operations.

### Query restructuring: COUNT(*) OVER()

Before Stage 4B, `queryProfiles` ran two sequential queries: one for the page rows, one for `SELECT COUNT(*)`. After Stage 4B (`repo/profiles.js:236`), a single query uses the PostgreSQL window function:

```sql
SELECT COUNT(*) OVER()::int AS total_count, id, name, ...
FROM profiles
WHERE ...
ORDER BY ...
LIMIT $n OFFSET $n
```

This eliminates one database round trip per paginated request. The fallback at `repo/profiles.js:259–262` runs the separate count only when the result set has zero rows (the window function returns no rows on an empty page, so `total_count` is unavailable).

**Measured improvement:** Against the Railway database with 2,030 profile rows, the old two-query flow averaged 712.066 ms; the new single-query flow averaged 369.014 ms across five runs — a ~48% reduction in database response time for paginated list queries.

### Connection pooling

`src/db.js` uses `pg.Pool` (the `pg` package's built-in connection pool). Configuration at `db.js:13–20`:

| Parameter | Env var | Default |
|-----------|---------|---------|
| Max connections | `PG_POOL_MAX` | 10 |
| Idle connection timeout | `PG_IDLE_TIMEOUT_MS` | 30 000 ms |
| Connection acquire timeout | `PG_CONNECTION_TIMEOUT_MS` | 5 000 ms |

When the pool is exhausted (all 10 connections in use), new `pool.query()` calls queue internally. If no connection is available within 5 000 ms, `pg.Pool` rejects with a timeout error, which the Express error handler converts to a 500 response.

### Caching strategy

**What is cached:** Successful results of `GET /api/profiles` (list) and `GET /api/profiles/search` (natural language search). CSV export (`GET /api/profiles/export`) is explicitly not cached — it always hits the database.

**Cache implementation:** `src/lib/queryCache.js` — a pure in-memory `Map`-based store. No Redis, no external infrastructure. The Map is local to the process.

**TTL:** 30 000 ms default (overridable via `PROFILE_QUERY_CACHE_TTL_MS`). Each cache entry stores `{ value, expiresAt }`. Expiry is checked lazily on `cache.get()`.

**LRU eviction:** When `entries.size > maxEntries` (default 500, overridable via `PROFILE_QUERY_CACHE_MAX_ENTRIES`), the Map's insertion-order iteration is used to identify and delete the oldest entry. On a cache hit, the entry is deleted and re-inserted to move it to the end (LRU refresh).

**Eviction policy on writes:** The cache is fully cleared (`cache.clear()`) after any `POST /` (profile create), `DELETE /:id`, or after each successfully flushed CSV import batch via the `onBatchComplete` callback in `routes/profiles.js:77`.

**Stampede protection:** None explicitly implemented. Under high concurrency after a cache clear, multiple requests for the same key will all miss and execute the database query concurrently. Because this is a single-process in-memory cache (no shared state across multiple app instances), the race window is bounded by the time a single query takes.

**Before/after latency numbers:**
- Local (in-memory app, 200 seeded rows): cold 56.928 ms → cached 24.331 ms
- Railway DB (2,030 rows): old two-query 712.066 ms → new single query 369.014 ms (no cache warm-up figure for Railway, but cache would reduce this to ~0 DB round trip on hit)

---

## Section 5: Query Normalization Deep Dive

### The input

The raw filter object before normalization comes from `validateListQuery` or from merging `validateSearchQuery` + `parseNaturalLanguageQuery`. It looks like:

```js
// From GET /api/profiles?gender=Female&country_id=ng&min_age=20&max_age=45
{
  gender: 'female',     // already lowercased by validateListQuery
  country_id: 'NG',     // already uppercased by validateListQuery
  min_age: 20,
  max_age: 45,
  page: 1,
  limit: 10,
  sort_by: 'created_at',
  order: 'asc'
}

// From parseNaturalLanguageQuery('Nigerian females between ages 20 and 45')
{
  gender: 'female',
  min_age: 20,
  max_age: 45,
  country_id: 'NG'
  // no page/limit/sort — those come from validateSearchQuery defaults
}
```

### Normalization steps in order (`lib/queryCache.js:70`)

`normalizeProfileQueryFilters(filters, options)`:

1. **Fill pagination defaults** (when `includeDefaults !== false`):  
   `limit = normalizeNumber(filters.limit) || 10`  
   `page = normalizeNumber(filters.page) || 1`  
   `sort_by = normalizeString(filters.sort_by, v => v.toLowerCase()) || 'created_at'`  
   `order = normalizeString(filters.order, v => v.toLowerCase()) || 'asc'`

2. **Lowercase string filters:**  
   `gender` → `.toLowerCase()`  
   `age_group` → `.toLowerCase()`  

3. **Uppercase country_id:**  
   `country_id` → `.toUpperCase()`

4. **Coerce numeric values:**  
   `min_age`, `max_age`, `min_gender_probability`, `min_country_probability` → `Number(value)`, `undefined` if not finite

5. **Deduplicate and sort `country_ids` array:**  
   Each element uppercased, `undefined`/empty filtered, converted to `Set` then sorted array. If result has exactly 1 element and no `country_id` is set, it collapses to `country_id`.

6. **Normalise `any` OR clauses:**  
   Each clause in the `any` array is itself normalised recursively with `includeDefaults: false`. Clauses that reduce to empty objects are dropped. Remaining clauses are stringified for deduplication, then sorted lexicographically by their stable JSON string — making OR clause order irrelevant.

7. **Sort all object keys:**  
   `sortObject(normalized)` recursively sorts keys of every nested object alphabetically.

### The output

```js
{
  age_group: undefined,  // omitted
  country_id: 'NG',
  gender: 'female',
  limit: 10,
  max_age: 45,
  min_age: 20,
  order: 'asc',
  page: 1,
  sort_by: 'created_at'
}
// keys sorted alphabetically; numerics are numbers not strings
```

### Cache key derivation

`profileQueryCacheKey(filters)` at `lib/queryCache.js:107`:

```js
return stableStringify(normalizeProfileQueryFilters(filters));
// stableStringify = JSON.stringify(sortObject(value))
```

The key is a plain JSON string. No hashing. For the example above:

```
{"country_id":"NG","gender":"female","limit":10,"max_age":45,"min_age":20,"order":"asc","page":1,"sort_by":"created_at"}
```

### Concrete example: two equivalent queries

**Query A:** `"Nigerian females between ages 20 and 45"`

```
parseNaturalLanguageQuery input: 'Nigerian females between ages 20 and 45'
normalizeCountryLookup: 'Nigerian' demonym → 'NG'
parseClause:
  gender: 'females' → 'female'
  findAgeRange: 'between ages 20 and 45' → {min_age:20, max_age:45}
  country: 'NG'
raw parsed filters: { gender:'female', min_age:20, max_age:45, country_id:'NG' }
+ validateSearchQuery defaults: { page:1, limit:10, sort_by:'created_at', order:'asc' }
merged: { gender:'female', min_age:20, max_age:45, country_id:'NG', page:1, limit:10, sort_by:'created_at', order:'asc' }
```

**Query B:** `"Women aged 20–45 living in Nigeria"`

```
parseNaturalLanguageQuery input: 'Women aged 20–45 living in Nigeria'
normalizeCountryLookup: 'Nigeria' (country name) → 'NG'
parseClause:
  gender: 'Women' → 'female'
  findAgeRange: 'aged 20–45' → {min_age:20, max_age:45}   (– is treated as -)
  country: 'NG'
raw parsed filters: { gender:'female', min_age:20, max_age:45, country_id:'NG' }
+ defaults: same as above
merged: same object as Query A
```

**Normalization of both:**

```js
normalizeProfileQueryFilters({
  gender:'female', min_age:20, max_age:45, country_id:'NG',
  page:1, limit:10, sort_by:'created_at', order:'asc'
})
// after sortObject:
{
  country_id:'NG', gender:'female', limit:10, max_age:45,
  min_age:20, order:'asc', page:1, sort_by:'created_at'
}
```

Both produce identical JSON → **identical cache key**:
```
{"country_id":"NG","gender":"female","limit":10,"max_age":45,"min_age":20,"order":"asc","page":1,"sort_by":"created_at"}
```

### Edge cases

**Missing field:** `normalizeString(undefined)` and `normalizeNumber(undefined)` both return `undefined`. `setIfDefined` only writes the key if the value is not undefined. A missing field is simply absent from the canonical object — the cache key for a query without `gender` will not contain the `gender` key at all.

**Age range as string vs integers:** `normalizeNumber` calls `Number(value)` regardless of input type. `'20'` and `20` both produce `20`. The cache key stores the number, not the string.

**Country name casing:** `normalizeCountryLookup` in `lib/countries.js` normalises the input text before the country lookup (lowercases demonyms/names before matching). The `normalizeProfileQueryFilters` step then uppercases `country_id`. So `'nigeria'`, `'Nigeria'`, `'nigerian'`, `'Nigerian'` all resolve to `'NG'`.

**Gender casing:** `normalizeString(filters.gender, v => v.toLowerCase())` — `'Female'`, `'FEMALE'`, `'female'` all produce `'female'`.

---

## Section 6: CSV Ingestion Deep Dive

### How the file is received

`importProfilesFromMultipart` (`services/profileImport.js:185`) uses **Busboy** for multipart parsing. Busboy wraps the raw request stream; `req.pipe(busboy)` starts streaming immediately without buffering the file body into memory. The `limits: { files: 1 }` option means Busboy reads at most one file field. The `file` field name is hardcoded (`fieldname !== 'file'` skips other fields).

**Size limit:** No explicit byte size limit in the Busboy configuration. The limit is implicitly the Express JSON body parser's `10kb` limit for `Content-Type: application/json` — but multipart requests bypass `express.json()`. For a 500,000-row file this means the server will stream the entire file. A production deployment could add a Busboy `fileSize` limit.

### Row batching

`DEFAULT_BATCH_SIZE = 1000` (`services/profileImport.js:24`). The batch is a plain array. When `batch.length >= 1000`, `flushBatch()` is called synchronously within the async `for await` loop (line 176–179), which `await`s the database insert before continuing to accumulate the next batch. This creates natural backpressure: the CSV stream is not read faster than the database can accept batches.

**Why 1 000:** Not explicitly justified in the code beyond being `DEFAULT_BATCH_SIZE`. It balances parameterised query size (9 parameters × 1000 rows = 9000 params, well within PostgreSQL's 65535-param limit) against memory usage. The importer keeps only one batch worth of candidates in memory at a time — approximately 9 fields × 1000 rows = bounded to a few hundred KB.

### Bulk insert mechanism

`repo.insertManyIgnoreDuplicates(profiles)` (`repo/profiles.js:161`):

```sql
INSERT INTO profiles
  (id, name, gender, gender_probability, age, age_group,
   country_id, country_name, country_probability)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9), ($10,...), ...
ON CONFLICT ((LOWER(BTRIM(name)))) DO NOTHING
RETURNING id, name, gender, ...
```

The `VALUES` clause is dynamically constructed — one tuple per candidate, with incrementing `$n` placeholders. The `RETURNING` clause returns only rows that were actually inserted (conflicting rows are silently skipped).

### Duplicate handling

**What constitutes a duplicate:** The `profiles_name_normalized_uidx` unique index (from migration 002) enforces `UNIQUE ON (LOWER(BTRIM(name)))`. Two profiles with the same name after trimming and lowercasing are considered duplicates.

**Database-level constraint:** `ON CONFLICT ((LOWER(BTRIM(name)))) DO NOTHING` — conflicts are silently skipped at the database level.

**Application-level behaviour:**  
1. `seenNames` Set (`services/profileImport.js:144`) deduplicates within the same upload: if two rows in the CSV have the same normalised name, only the first is added to the batch; subsequent duplicates increment `summary.reasons.duplicate_name` before the row even reaches the database.  
2. After `insertManyIgnoreDuplicates` returns, `candidates.length - insertedRows.length` gives the count of rows that conflicted at the database level (duplicates of existing rows or race-condition conflicts from concurrent uploads). These are added to `summary.reasons.duplicate_name` at `profileImport.js:152`.

### Row validation (`validateRow`, services/profileImport.js:75)

| Check | Reason key |
|-------|-----------|
| `typeof row !== 'object'` | `malformed_row` |
| Any `REQUIRED_COLUMNS` field empty or missing | `missing_fields` |
| `seenNames.has(nameKey)` (within-upload duplicate) | `duplicate_name` |
| `gender` not in `VALID_GENDERS` (`{'male','female'}`) | `invalid_gender` |
| `age` fails `/^\d+$/` or is negative | `invalid_age` |
| `country_id` not a valid 2-letter ISO code in registry | `malformed_row` |
| `gender_probability` or `country_probability` outside [0, 1] | `malformed_row` |

Required columns: `name`, `gender`, `age`, `country_id`, `gender_probability`, `country_probability` (defined at `profileImport.js:15`).

### Partial-failure contract

The upload is **not** wrapped in one transaction. Each `flushBatch()` call is an independent `INSERT`. If the process throws or the connection drops after batch 3 of 10 has committed, those 3 000 rows remain. Rows from batches 4–10 were never sent. The task specification explicitly requires this: "if processing fails midway, rows already inserted must remain. The upload does not roll back."

There are no savepoints. The autocommit model of `pg.Pool.query()` means each INSERT runs in its own implicit transaction. Failure of a later batch does not roll back earlier batches.

### Reasons summary

The `summary` object is created at `createSummary()` (`profileImport.js:26`) at the start of the import. It is passed by reference to `validateRow` which mutates `summary.reasons.*`. The final `finalSummary(summary)` call (`profileImport.js:44`) computes `skipped = sum of all reason counts` and returns the final response shape.

**Exact reason keys:** `duplicate_name`, `invalid_age`, `missing_fields`, `invalid_gender`, `malformed_row`.

Note: `malformed_row` is also incremented by csv-parse's `on_skip` callback for rows the CSV parser itself cannot tokenise (wrong column count, broken encoding, etc.) — before `validateRow` is even called.

### Memory behaviour

Busboy streams the multipart body; it never holds more than a chunk in memory. csv-parse is used in async-iterator mode (`for await`), emitting one parsed row at a time. The `batch` array holds at most `DEFAULT_BATCH_SIZE` (1000) validated candidate objects. The `seenNames` Set holds one string (the lowercase name key) per valid unique name seen so far — for a 500,000-row file with all unique names this would be ~500,000 strings, typically a few tens of MB. This is the one in-memory structure that grows with file size, but it stores only normalised name keys, not full row payloads.

For a 500,000-row file with many duplicates, `seenNames` would be smaller (bounded by unique valid names). For 500,000 fully unique rows, it would hold 500,000 short strings — acceptable for a server with typical RAM but worth knowing.

---

## Section 7: Q&A Bank

### Group A — Design Decisions (5 questions)

**Q1: Why did you use an in-memory cache instead of Redis?**

> The brief constrains: "no new database systems," "no unnecessary infrastructure," "limited compute resources." An in-memory `Map` satisfies the brief's repeated-query cache requirement without adding a Redis deployment, network hop, or serialisation cost. The trade-off is that the cache is process-local — multiple app instances would not share entries. In the current single-process Railway deployment, that trade-off is acceptable. Decision D-007 records this explicitly: Redis is a conditional scale lever, not a first-rollout requirement.

**Q2: Why three composite indexes instead of one covering all common query shapes?**

> PostgreSQL can only use one index per table scan per query. The three composites — `(country_id, gender, age)`, `(gender, age)`, `(country_id, age)` — cover the three most common filter combinations the `buildWhere` function emits. A single index with all columns would not help queries that filter on only two of the three. Each index adds write overhead, so speculative indexes for uncommon combinations were excluded. Decision D-009 and the SOLUTION.md table explain the justification for each index.

**Q3: Why is the cache invalidated fully (`cache.clear()`) instead of per-key?**

> Filter combinations are open-ended. A write (create, delete, or import) can affect any cached query whose result set includes the changed row. Computing the affected key set would require intersecting the write's attributes against all cached filter objects — more expensive than a single `clear()`. Decision D-008 records this: per-query targeted invalidation was rejected because the filter space is open-ended; write-through was rejected because writes are batch; the decision is full eviction on write.

**Q4: Why does the CSV import not use a database-level transaction for the entire upload?**

> The task specification is explicit: "if processing fails midway, rows already inserted must remain. The upload does not roll back." A single wrapping transaction would roll back everything on any batch failure. Independent per-batch inserts satisfy the spec. The cost is that a partial upload leaves the database in an intermediate state, but that is the required behaviour.

**Q5: Why does `COUNT(*) OVER()` replace two separate queries?**

> The original code ran `SELECT ... LIMIT OFFSET` followed by `SELECT COUNT(*)` — two round trips to the database for every paginated list request. `COUNT(*) OVER()` is a PostgreSQL window function that computes the total count over the full filtered result set while retrieving the page rows in a single query. The SOLUTION.md measurements show this halved response time on the Railway database (712 ms → 369 ms) without any change to the API contract.

---

### Group B — Implementation Precision (8 questions)

**Q6: Walk me through exactly what happens when a CSV row fails age validation — trace it from the validator to the response body.**

> In `importProfilesFromCsvStream` (`profileImport.js:136`), the `for await` loop calls `summary.total_rows += 1` then `validateRow(row, seenNames, summary)`. Inside `validateRow` (line 75), after the missing-fields check passes, `parseAge(row.age)` is called (line 61). `parseAge` runs `/^\d+$/.test(String(value).trim())` — any non-digit character including a minus sign fails the regex and returns `null`. If the age is a non-negative integer string but `Number.isInteger(age)` is false (shouldn't happen, but guarded), it also returns `null`. On `null`, `validateRow` increments `summary.reasons.invalid_age` and returns `null`. Back in the loop, `if (!candidate) continue` skips the row without adding it to the batch. At the end of the import, `finalSummary(summary)` includes `reasons.invalid_age` in the response. The response body's `reasons.invalid_age` is the cumulative count of all rows that failed this check.

**Q7: Show the exact cache key for the query "young males in South Africa."**

> 1. `parseNaturalLanguageQuery('young males in South Africa')` runs `normalizeCountryLookup` which maps 'South Africa' → `'ZA'`. `parseClause` finds 'males' → `gender:'male'`; 'young' → `min_age:16, max_age:24` (line 241 of queryParser.js: `young` → `{min_age:16, max_age:24}`); 'South Africa' → `country_id:'ZA'`.
> 2. Merged with defaults `{page:1, limit:10, sort_by:'created_at', order:'asc'}`.
> 3. `normalizeProfileQueryFilters` fills remaining defaults, lowercases, uppercases country_id, coerces numbers, sorts object keys.
> 4. `stableStringify` produces:
> ```
> {"country_id":"ZA","gender":"male","limit":10,"max_age":24,"min_age":16,"order":"asc","page":1,"sort_by":"created_at"}
> ```
> That is the exact string stored as the cache key.

**Q8: What happens if the in-memory cache connection (the Map itself) is somehow unavailable mid-request?**

> The cache is a plain JavaScript `Map` held in the application's heap — it cannot become "unavailable" independently of the process. There is no network dependency. If the process runs out of memory and throws an OOM error, the entire Node.js process crashes, not just the cache. The design deliberately avoids Redis to eliminate the "cache unreachable" failure mode. The `queryProfilesWithCache` function at `queryCache.js:159` does not have a try/catch around `cache.get()` — if the Map throws (which it cannot under normal conditions), the error propagates to the route's `catch(err) { next(err) }` and becomes a 500 response.

**Q9: What is the exact batch size used by the CSV importer? Why not larger?**

> `DEFAULT_BATCH_SIZE = 1000` at `services/profileImport.js:24`. Overridable via `options.batchSize` (the route passes `options.importBatchSize` from app configuration). The batch constructs one parameterised query with 9 columns × up to 1000 rows = up to 9000 `$n` parameters. PostgreSQL supports up to 65535 parameters per statement, so 9000 is well within the limit. A larger batch would increase the query compile time and the risk of a full-batch failure losing more rows' processing. A smaller batch would increase the number of round trips. 1000 is a practical midpoint that fits in a single statement comfortably and keeps memory per batch bounded to a few hundred KB.

**Q10: What happens to a profile created via `POST /api/profiles` while a CSV import is in progress — is there a race condition?**

> Yes, there can be a race. If `POST /api/profiles` inserts a profile whose name key matches a row in a batch currently being processed by `importProfilesFromCsvStream`, the `ON CONFLICT DO NOTHING` in `insertManyIgnoreDuplicates` silently skips that row at the database level. `candidates.length - insertedRows.length` is then non-zero, and that difference is added to `summary.reasons.duplicate_name`. The row is not double-inserted (the unique index prevents it), and the `POST /api/profiles` response succeeds normally. The cache is cleared independently by both operations — `POST /` calls `profileQueryCache.clear()` at `routes/profiles.js:62`, and each batch's `onBatchComplete` callback also calls `profileQueryCache.clear()` at `routes/profiles.js:77`. The order of clears is not coordinated, but since every write clears the whole cache, the cache will never serve a result that omits any committed row.

**Q11: Two concurrent CSV uploads arrive simultaneously — what prevents both from inserting the same row twice?**

> The `ON CONFLICT ((LOWER(BTRIM(name)))) DO NOTHING` clause on the unique index `profiles_name_normalized_uidx` is the database-level guard. PostgreSQL serialises concurrent inserts against the same unique key at the row lock level; only one succeeds and the other receives a conflict response (silently skipped by `DO NOTHING`). The `seenNames` Set is process-local and only prevents duplicates within a single upload request, not across concurrent uploads. The database constraint is the authoritative deduplication mechanism.

**Q12: Walk me through how `sortObject` ensures cache key stability regardless of property insertion order.**

> `sortObject` is defined at `queryCache.js:13`. For plain objects it takes `Object.keys(value).sort()` — the alphabetically sorted key array — and reconstructs a new object `sorted` by iterating those sorted keys, recursively calling `sortObject` on each value. Arrays are handled by mapping `sortObject` over elements. Primitives are returned unchanged. The result is an object whose key order is deterministic (alphabetical at every nesting level), so `JSON.stringify` produces the same string regardless of the order in which properties were added to the original object. This is what `stableStringify` calls (`stableStringify = JSON.stringify(sortObject(value))`).

**Q13: What does the route handler do between `importProfilesFromMultipart` returning and sending the response?**

> The route handler at `routes/profiles.js:72–82` is:
> ```js
> router.post('/import', adminOnly, async (req, res, next) => {
>   try {
>     const result = await importProfilesFromMultipart(req, { repo, batchSize, onBatchComplete });
>     return success(res, 200, result);
>   } catch (err) {
>     next(err);
>   }
> });
> ```
> It awaits the entire import, then calls `success(res, 200, result)` which sends the JSON summary. There is no intermediate streaming of progress. The HTTP connection is held open for the entire upload duration. On error (e.g., missing `file` field, Content-Type mismatch), `next(err)` passes the error to the global error handler, which converts `HttpError` instances to their status code or returns 500.

---

### Group C — Trade-offs and Limitations (4 questions)

**Q14: What breaks at 10× the current load (tens of thousands of queries per minute)?**

> Three things become bottlenecks. First, the in-memory cache is per-process and not shared — 10 Node.js instances each maintain their own 500-entry cache, so the effective cache hit rate drops by a factor of the instance count. Second, the connection pool is capped at 10 connections per process. At high concurrency the queue of waiting `pool.query()` calls grows, and eventually the 5-second `PG_CONNECTION_TIMEOUT_MS` triggers 500 responses. Third, the rate limiter uses an in-memory `memoryStore` (in `middleware/rateLimit.js`) which is also per-process — concurrent instances would not share rate limit state, so the effective per-user rate limit is multiplied by the number of instances. The design document (Stage 4A) names an external Redis-backed cache and PgBouncer as the measured next levers for exactly this scenario.

**Q15: What does query normalization fail to handle?**

> The normalizer handles the filter shapes the `queryValidation.js` and `queryParser.js` produce. It does not handle: (1) boolean NOT queries (no `exclude` or `not` operator is supported); (2) queries with open-ended `any` OR clauses that contain probability thresholds combined with demographic filters in complex ways (the `any` normalisation handles simple demographic OR clauses); (3) queries that mix `country_ids` (array) and `country_id` (single) — the normalizer collapses a one-element `country_ids` to `country_id`, but an explicit `country_id` alongside a `country_ids` array is not a documented input shape. If the rule parser ever emits a filter shape the normalizer doesn't know about (e.g., a new filter field added in a future stage), that field would appear in the cache key only if `setIfDefined` processes it — meaning unknown fields are simply passed through but not normalised.

**Q16: What does the ingestion endpoint not handle?**

> The brief specifies CSV delimiter as comma — no TSV or configurable delimiter support. The file must be UTF-8 (csv-parse's `bom:true` strips a UTF-8 BOM if present, but non-UTF-8 encodings like Latin-1 will produce garbled or skipped rows counted as `malformed_row`). There is no explicit file size limit on the Busboy configuration — a very large file will stream indefinitely, holding an HTTP connection for minutes. There is no progress endpoint; the client receives no feedback until the entire file is processed. Nested or multi-value CSV fields (e.g., arrays encoded as JSON strings) are not supported — the schema expects flat row values. The `name` field is the only uniqueness key; two profiles with the same name but different ages or countries are considered duplicates.

**Q17: What is the cache's staleness window in the worst case?**

> The worst case is a fresh profile insert followed immediately by a list query. If the insert clears the cache (`profileQueryCache.clear()`) and then the list query executes and caches the result, and then another insert arrives within the same millisecond before the first query's cache write completes — in a single-threaded Node.js process this race cannot actually occur (one event loop tick runs to completion before the next). However, across the TTL window: if a row is inserted, the cache is cleared, a query runs and caches the result, then within `PROFILE_QUERY_CACHE_TTL_MS` (30 seconds default) another insert happens, the second insert will clear the cache again. So the maximum staleness for any cached entry is 30 seconds — the TTL. After a `cache.clear()`, the next request always re-queries the database.

---

### Group D — Stage 4A Design Questions (3 questions)

**Q18: In your Stage 4A design, you described normalized cache keys with a version tag that the ingestion worker bumps. The Stage 4B implementation does not use a version tag — it uses `cache.clear()`. Is this design drift?**

> The Stage 4A design described Redis-backed cache with version-tag invalidation (decision D-008) as the first-rollout model. The Stage 4B implementation uses an in-memory cache with full clear on write. The outcome is the same: after any write, all cached entries become invalid before the next read can return them. The difference is that `cache.clear()` is simpler than bumping a version tag because there is no shared state — the process-local Map has no cross-process invalidation concern. If the design were scaled to Redis, the version-tag approach would become necessary; `cache.clear()` does not work across processes. The Stage 4B implementation is the correct simplification for a single-process deployment. This is not drift; it is the implementation applying D-014 (simplify final presentation to avoid over-engineering signals) to the code.

**Q19: Your Stage 4A design required P50 below 500ms and P95 below 2 seconds. What evidence do you have that Stage 4B meets these targets?**

> The SOLUTION.md records two measurements. Local (in-memory app, 200 seeded rows): cold query 56.928ms, cached query 24.331ms — both well under P50 target. Railway database (2,030 rows): new single-query flow average 369.014ms across five runs — within the P50 budget. A cached hit on Railway would approach the local cached figure (~24ms). The P95 target requires a statement timeout (designed in D-011 as a 2-second limit). The Stage 4B code does not implement an explicit statement timeout on the connection — this is a known gap between the Stage 4A design and Stage 4B implementation. The composite indexes and the `COUNT(*) OVER()` optimisation reduce query time for the measured dataset; a statement timeout would be the additional production safeguard.

**Q20: Your Stage 4A design describes a "query envelope" that rejects unknown columns and bounds page size. Stage 4B's `validateListQuery` caps `limit` at 50. Is 50 the right cap?**

> The `readInteger` call for `limit` at `queryValidation.js:113` sets `max: 50, clampMax: true`. Values above 50 are silently clamped to 50 (not rejected). This is a practical safeguard against unbounded result sets. The Stage 4A design (D-011) described the hard page-size cap as "default 50, hard max around 500" — the implementation uses 50 as both default and maximum for list queries. Export (`GET /api/profiles/export`) has no pagination and returns all matching rows, which is the intended bulk-export path. The 50-row cap aligns with interactive use (CLI and web portal pagination) and prevents any single list query from transferring more rows than a single page of results.

---

## Section 8: Known Limitations and Honest Answers

| Limitation | Honest answer |
|------------|--------------|
| Cache is process-local, not shared | Multiple app instances each maintain independent 500-entry caches. A second instance will not benefit from the first instance's cache hits. Effective hit rate drops with scale-out. Redis would fix this but was excluded as an initial requirement. |
| No statement timeout on database connections | Stage 4A design (D-011) specified a per-statement timeout. Stage 4B's `db.js` does not set `statement_timeout` on the pool. Runaway queries are not killed at the database level. |
| No file size limit on CSV uploads | Busboy has no `fileSize` limit configured. A 500,000-row upload will hold the HTTP connection open for the duration. A misconfigured client sending a multi-GB file would tie up a connection indefinitely. |
| Cache stampede possible after `cache.clear()` | Under high concurrency, a `cache.clear()` event causes all concurrent requests for the same key to miss simultaneously and execute the database query in parallel. No mutex, promise deduplication, or stampede protection is implemented. |
| `seenNames` Set grows with upload size | For 500,000 rows with all unique names, the Set holds 500,000 strings in memory for the duration of the upload. This is bounded by unique name count, not row count, but is still the one data structure that scales with file size. |
| Normalization only covers documented filter shapes | Fields not processed by `normalizeProfileQueryFilters` pass through `sortObject` untouched but not canonicalized. A future filter field without an explicit normalisation step would produce different keys for different input formats. |
| Cache TTL is not tunable per query shape | All cached queries share the same 30-second TTL. High-frequency stable queries (country aggregates) and low-frequency volatile queries (latest profiles) age out at the same rate. |
| CSV accepts comma delimiter only | No TSV, semicolon, or configurable delimiter. Non-UTF-8 encoded files produce garbled or skipped rows counted as `malformed_row` with no specific encoding error message. |
| No progress reporting during large uploads | The HTTP connection is held open for the entire import. The client receives no feedback until the upload completes. A 500,000-row file at 369ms per 1000-row batch would take approximately 3 minutes, with no intermediate status. |
| No authentication on export endpoint | `GET /api/profiles/export` is guarded by `requireAuth` (any authenticated user), not `adminOnly`. Any analyst role can export the full profile dataset. This is inherited from Stage 3. |

---

## Section 9: Proof-of-Work Evidence Map

| Stage 4B Criterion | File(s) | Mechanism | Proof |
|---|---|---|---|
| Reduce query latency via indexing | `migrations/004_stage4b_optimization.sql` | Three composite B-tree indexes on `(country_id, gender, age)`, `(gender, age)`, `(country_id, age)` | SOLUTION.md table: index justification per combination; Railway timing 712ms → 369ms |
| Reduce database round trips | `src/repo/profiles.js:236–257` | `COUNT(*) OVER()` window function replaces two-query pattern | SOLUTION.md: "old two-query flow avg 712.066ms; new single query avg 369.014ms" |
| Connection pooling | `src/db.js:13–20` | `pg.Pool` with env-backed `PG_POOL_MAX=10`, `PG_IDLE_TIMEOUT_MS=30000`, `PG_CONNECTION_TIMEOUT_MS=5000` | Code + SOLUTION.md pool defaults table |
| Query result caching | `src/lib/queryCache.js:111–157` | In-memory LRU/TTL Map, 500 entries, 30s TTL | Local timing: cold 56.928ms → cached 24.331ms |
| Query normalization (deterministic cache keys) | `src/lib/queryCache.js:70–108` | `normalizeProfileQueryFilters` + `stableStringify` | Code trace; identical key for both example queries proven in Section 5 |
| Equivalent queries share cache entries | `src/routes/profiles.js:88, 112` | Both `GET /` and `/search` pass through `queryProfilesWithCache` using the same normalizer | Test suite: 69/69 tests pass; demonstrated by cache key trace in Section 5 |
| Cache invalidation on writes | `src/routes/profiles.js:62, 78, 138` | `profileQueryCache.clear()` after `POST /`, `DELETE /:id`, and after each import batch | Code: `onBatchComplete: () => profileQueryCache.clear()` |
| CSV streaming (no full-file memory load) | `src/services/profileImport.js:185–227` | Busboy streams multipart; csv-parse async iterator processes 1 row at a time | Code: `req.pipe(busboy)`, `for await (const row of parser)` |
| Batch insert (not row-by-row) | `src/repo/profiles.js:161–201` | Single `INSERT … VALUES (…),(…),…` with 1000-row batches | Code: `DEFAULT_BATCH_SIZE = 1000`; dynamic VALUES construction |
| `ON CONFLICT DO NOTHING` for duplicate names | `src/repo/profiles.js:182–195` | `ON CONFLICT ((LOWER(BTRIM(name)))) DO NOTHING` | Code + SOLUTION.md edge cases section |
| Partial failure: already-inserted rows remain | `src/services/profileImport.js:147–154` | Each `flushBatch()` is independent — no wrapping transaction | SOLUTION.md: "The upload is not wrapped in one transaction. Each chunk inserts independently." |
| Summary response with exact reason keys | `src/services/profileImport.js:26–50` | `createSummary()` → `finalSummary()` with five reason keys | SOLUTION.md: `duplicate_name`, `invalid_age`, `missing_fields`, `invalid_gender`, `malformed_row` |
| Admin-only import endpoint | `src/routes/profiles.js:72`, `src/middleware/auth.js` | `requireRole('admin')` middleware | Test suite: import returns 403 for analyst role |
| Stage 3 surfaces intact | `src/routes/profiles.js`, `src/routes/auth.js`, `src/routes/users.js` | No changes to existing route shapes or auth flow | SOLUTION.md: "existing Stage 3 backend suite remains in npm test and still passes"; 69/69 tests |

---

## Section 10: Five-Minute Verbal Summary

Insighta Labs+ is a demographic query platform I have been building across Stages 1 through 4. Stage 1 set up profile storage. Stage 2 added the query engine — structured filters, aggregations, a rule-based natural-language parser. Stage 3 added GitHub OAuth, JWT-based RBAC, and a Next.js web portal. For Stage 4A I produced a scaling design: I identified that repeated queries were hitting the database unnecessarily, that multi-column demographic filters were doing full table scans, and that there was no path for large-scale data ingestion. The design proposed three targeted improvements: composite indexes, a normalised query cache, and streaming batch ingestion. Critically, I kept the design practical — no microservices, no message queues, no search engine, no Redis until it was measured to be needed.

Stage 4B implemented that design in the existing Node.js and Express codebase. Let me walk you through each improvement with a specific number.

**Query optimization:** I replaced the two-query pattern in `repo/profiles.js` — one query for the page, one for the count — with a single SQL query using `COUNT(*) OVER()`, PostgreSQL's window function. Measured on the Railway database with 2,030 rows, this dropped average response time from 712 ms to 369 ms — roughly a 48% reduction. I also added three composite B-tree indexes: `(country_id, gender, age)` for the most common three-column demographic filter, `(gender, age)` for gender-only age range queries, and `(country_id, age)` for country-only age range queries. These directly support the equality-plus-range filter patterns the query builder emits.

**Query normalization:** Two queries that express the same intent — `"Nigerian females between ages 20 and 45"` and `"Women aged 20–45 living in Nigeria"` — previously produced different URL parameters and thus different cache keys, meaning both hit the database. The normalizer in `queryCache.js` canonicalises filter objects: lowercases gender and sort fields, uppercases country codes, coerces string numbers to actual numbers, deduplicates and sorts country arrays, sorts all OR clauses, and sorts all object keys — then serialises to a deterministic JSON string. Both queries above produce the exact same key: `{"country_id":"NG","gender":"female","limit":10,"max_age":45,"min_age":20,"order":"asc","page":1,"sort_by":"created_at"}`. Locally, a cold query takes 57 ms and a cached hit takes 24 ms.

**CSV ingestion:** The `POST /api/profiles/import` endpoint uses Busboy to stream the multipart body without buffering the whole file. csv-parse provides an async iterator that emits one parsed row at a time. Rows are validated (missing fields, invalid age, invalid gender, bad country, bad probabilities) and accumulated into batches of 1,000. Each batch is flushed with a single `INSERT … VALUES (…) … ON CONFLICT DO NOTHING`, which also handles duplicates. After each batch, the query cache is cleared. There is no outer transaction — if something fails after batch 3 of 10, those 3,000 rows stay committed. The response summarises inserted, skipped, and each skip reason.

The honest trade-off is that the cache is process-local. That is fine for a single-process deployment but breaks down if you scale horizontally — the design document explicitly identifies Redis as the next lever once that happens. The statement timeout from the Stage 4A design is also not yet implemented in code, which means a badly-shaped query could hold a connection longer than the 2-second P95 budget. Those are the two gaps I would close first.
