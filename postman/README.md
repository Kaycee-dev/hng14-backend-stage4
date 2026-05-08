# Stage 4B Demo – Postman Pack

This directory contains the Postman collection and environment for demoing and
verifying the HNG14 Stage 4B backend implementation.

## Files

| File | Purpose |
|------|---------|
| `Stage4B-Demo.postman_collection.json` | Full request collection (folders A–G) |
| `Stage4B-Local.postman_environment.json` | Environment with `baseUrl`, `apiVersion`, blank token placeholders |
| `samples/valid-import.csv` | 10-row CSV with all valid profiles |
| `samples/mixed-import.csv` | 9-row CSV with missing fields, invalid age, duplicate-in-file |
| `samples/duplicate-import.csv` | Same rows as valid-import.csv – triggers duplicate_name on re-upload |

## Quick Start

1. **Install the collection and environment** in Postman (or Newman).
2. **Start the server**: `npm start` in the repo root (port 3000 by default).
3. **Run folder A – Setup / Auth** first to get tokens.
   - Tokens expire in **180 s** – re-run folder A if you get a `401`.
4. Run folders B → G in order for full demo coverage.

## Collection Folder Map

| Folder | What it covers |
|--------|----------------|
| A – Setup/Auth | Admin + analyst token acquisition, all token shape variants |
| B – Preconditions | Missing API version (400), missing auth (401), RBAC read |
| C – Profiles List/Search/Export | Pagination shape, NLS search, OR clauses, CSV export headers |
| D – Cache/Performance | Cold → warm → canonical-equiv timing demo |
| E – Import Demo | Valid upload, mixed upload (bad rows skipped), analyst 403, duplicate upload |
| F – Cache Invalidation | Prime cache → import → query again (fresh data) |
| G – Create/Delete | Admin-only create + delete, analyst 403, cache clear |

## Running with Newman

```powershell
# Install newman globally
npm install -g newman

# Run the full collection
newman run postman/Stage4B-Demo.postman_collection.json \
  -e postman/Stage4B-Local.postman_environment.json \
  --folder "A – Setup / Auth" \
  --folder "B – Preconditions" \
  --folder "C – Profiles List / Search / Export" \
  --folder "D – Cache / Performance Demo" \
  --folder "E – Import Demo" \
  --folder "F – Cache Invalidation Demo"
```

## Notes on Timing (Folder D)

Cache timing is environment-dependent:
- **Cold** query hits the remote PostgreSQL database (Railway or equivalent).
- **Warm** query returns from the in-process LRU cache (no DB round-trip).
- **Canonical-equiv** query has params in a different URL order but normalizes
  to the same cache key, so it also returns from cache.

Typical observed values on Railway remote DB:
- Cold: ~400–600 ms
- Warm: ~1–5 ms (in-process)
- Canonical-equiv: ~1–5 ms

Do not treat these numbers as performance benchmarks – they depend on network
latency to the database.

## Import File Usage (Folder E)

When running inside Postman Desktop, update the `file` field in each import
request to point to the local path of the CSV files in `postman/samples/`.

The file field name **must be `file`** (the server rejects other names).

## Security Reminder

- The environment file contains **blank** token fields.
- Never commit real tokens, DATABASE_URL, or passwords to Git history.
- `.env` is gitignored – keep it that way.
