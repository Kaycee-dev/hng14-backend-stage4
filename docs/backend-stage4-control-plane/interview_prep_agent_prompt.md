# Agent Prompt — Backend Stage 4 Interview Prep Pack

## What you are doing and why

You are generating a rigorous, proof-of-work-style interview prep document for a developer
who just submitted the HNG Backend Stage 4 (Insighta Labs+) task. The developer needs to be
able to answer any grader or interviewer question about their implementation with code-level
precision — not just high-level design talk. The output must be grounded entirely in the
actual code and documents in this repository; no invented details.

The working directory is: `C:\Users\Hp\Documents\hng14\backend-stage4`

---

## Step 1 — Read everything before writing a single line of output

Do not begin writing the prep document until you have read all of the following. Read them
in this order.

### Task specifications (what was required)
- `task_details.md` — Stage 4A spec (system design)
- `task_details_4B.md` — Stage 4B spec (implementation: query optimization, normalization,
  CSV ingestion)

### Governance and design documents
- `docs/backend-stage4-control-plane/01_brief_traceability.md`
- `docs/backend-stage4-control-plane/04_decisions_log.md`
- `docs/backend-stage4-control-plane/05_evidence_log.md`
- `docs/backend-stage4-control-plane/08_interview_defense_bank.md`
- `docs/backend-stage4-control-plane/06_validation_strategy.md`
- `docs/backend-stage4-control-plane/07_qa_checklist.md`

### Submitted design documents
- `drafts/insighta-labs-stage4-design.md` (full design)
- `drafts/insighta-labs-stage4-design-compact.md` (compact version)

### Find and read the implementation code
Search the repository for the actual application source files. Look for:
- Database query functions and any indexing setup (migration files, schema files)
- The query normalization logic (canonical key generation)
- The CSV ingestion endpoint and its bulk-insert implementation
- The caching layer (Redis or in-memory) and its key construction
- Any connection pooling configuration
- The query parser that maps natural-language-style inputs to structured filters
- The API route handlers for queries and CSV upload
- SOLUTION.md if it exists

Use Glob and Grep to find source files. Look in subdirectories such as `src/`, `app/`,
`routes/`, `services/`, `db/`, `models/`, `utils/`, or any language-specific structure.
Also check for files named `*.py`, `*.js`, `*.ts`, `*.go` recursively.

If the implementation code lives in a separate repository path, find it. Check
`README.md` and `AGENTS.md` for clues about where the code lives.

Read every implementation file you find that is relevant to the three task areas:
1. Query performance (indexes, caching, connection pooling, query restructuring)
2. Query normalization (canonical form, cache key generation)
3. CSV ingestion (bulk insert, partial failure handling, row skipping logic)

---

## Step 2 — Write the prep document

Write the output to `docs/backend-stage4-control-plane/interview_prep.md`.

The document must have exactly the sections listed below, in this order. Every claim in
the document must be traceable to a specific file and line you actually read.

---

### Section 1: One-paragraph pitch

A single paragraph the developer can say out loud in 30 seconds. What the system does,
what Stage 4A added (design), what Stage 4B added (implementation), and what the three
concrete improvements were. No jargon without definition. No claims without a specific
implementation detail to back them.

---

### Section 2: System architecture map

A text diagram showing: client (CLI + web) → API layer → cache → database. Show where
normalization happens in the request path (before cache lookup? before query execution?).
Show where the CSV ingestion path diverges from the query path. Show where connection
pooling sits.

Follow this with a file-by-file responsibility table: one row per key file with its
single responsibility in plain English.

---

### Section 3: Complete data-flow walkthroughs

Write a step-by-step walkthrough for each of the three task areas, naming exact functions
and files at each step. Model this on how a call stack reads:

**Query path (with caching):**
```
request arrives at <route handler in file:line>
  → query parser: maps input string to structured filter dict
  → normalizer: sorts/canonicalises filter dict → deterministic cache key
  → cache lookup: HIT → return cached result / MISS → continue
  → connection pool: acquires connection
  → query executor: runs SQL with indexes
  → cache write: stores result under canonical key
  → response
```

**CSV ingestion path:**
```
POST /upload arrives at <route handler in file:line>
  → validation: checks Content-Type, file size
  → CSV reader: streams rows
  → row validator: checks each row for required fields, type correctness
  → bulk inserter: batches N rows → single INSERT ... ON CONFLICT / COPY
  → error accumulator: collects skipped-row reasons
  → summary response: {inserted, skipped, reasons}
```

Be specific about what happens on partial failure (mid-batch error). Name the exact
mechanism used to keep already-inserted rows.

---

### Section 4: Query optimization deep dive

Cover exactly:
- What indexes were added, on which columns, and why those columns specifically
- What query restructuring was done (if any) — did any N+1 patterns get fixed?
- How connection pooling is configured: pool size, timeout, what happens when the pool
  is exhausted
- The caching strategy: what is cached, what is the TTL, what is the eviction policy,
  what happens on a cache miss under high concurrency (stampede protection?)
- Before/after latency numbers if they exist in any evidence or SOLUTION.md

---

### Section 5: Query normalization deep dive

Cover exactly:
- The input: what does the raw parsed filter object look like before normalization?
- The normalization steps in order: what gets sorted, what gets lowercased, what gets
  type-coerced, what gets stripped?
- The output: what does the canonical object look like?
- How the cache key is derived from the canonical object (hash? serialisation?)
- A concrete example: show the two equivalent queries from the brief
  (`"Nigerian females between ages 20 and 45"` and `"Women aged 20–45 living in Nigeria"`)
  and trace both through normalization to prove they produce the same cache key
- Edge cases: what if a field is missing? what if age range is expressed as a string
  vs integers? what if country name has different casing?

---

### Section 6: CSV ingestion deep dive

Cover exactly:
- How the file is received: multipart? streaming? size limit?
- How rows are batched: what is the batch size and why that number?
- The bulk insert mechanism: exact SQL or ORM call used
- Duplicate handling: what constitutes a duplicate? what is the database-level
  constraint? what is the application-level behaviour on conflict?
- Row validation: what fields are required? what type checks are performed?
- The partial-failure contract: if a batch fails mid-way, are previous batches committed
  or rolled back? How is this achieved (autocommit per batch? savepoints?)
- The reasons summary: where is the reasons dict built? what are the exact reason keys?
- Memory behaviour: does the implementation load the entire CSV into memory, or stream it?
  Why does this matter for 500,000-row files?

---

### Section 7: Q&A bank

Write at least 20 questions with complete answers. Organise into these groups:

**Group A — Design decisions (5 questions)**
Questions that probe WHY choices were made. Each answer must reference the decisions log
or a specific design rationale. Example format:
> Q: Why did you choose [X] over [Y] for the cache?
> A: [decision ID if logged] + specific reasoning tied to the task constraints.

**Group B — Implementation precision (8 questions)**
Questions that can only be answered correctly by someone who wrote the code. Examples:
- "Walk me through exactly what happens when a CSV row fails validation — trace it from
  the validator to the response body."
- "Your normalization produces a cache key. Show me the exact key for the query
  'young males in South Africa' — what does it look like after normalization?"
- "What happens if the Redis/cache connection drops mid-request? Does the query still
  complete?"
- "You said you use bulk insert. What is the exact batch size? Why that number and not
  larger?"

**Group C — Trade-offs and limitations (4 questions)**
Questions about what the design does NOT handle well. Answers must be honest and specific,
not defensive. Cover: what breaks at 10× the current load, what the normalization
cannot handle (complex boolean queries?), what the ingestion does not handle (nested CSV?
non-UTF-8 encoding?).

**Group D — Stage 4A design questions (3 questions)**
Questions about the design document submitted for Stage 4A. Probe the requirements
section, the architecture diagram, and the data-flow description. Answers must be
consistent with what was actually implemented in Stage 4B (no design-vs-implementation
drift).

---

### Section 8: Known limitations and honest answers

A short section that lists everything the implementation does NOT do well, with a one-line
honest answer for each. This is not a failure list — it is preparation so the developer
is never caught off guard. Examples of what to look for:

- Does normalization handle every possible query variant, or just the common ones?
- Is the cache invalidated on writes, or do stale reads persist?
- What is the maximum CSV file size actually tested vs the 500,000-row spec?
- Does the ingestion endpoint have authentication / authorisation?
- Are indexes covering or non-covering?

---

### Section 9: Proof-of-work evidence map

A table mapping each grading criterion from `task_details_4B.md` to:
- The specific file(s) that implement it
- The mechanism used
- Any evidence or test that proves it works

| Criterion | File(s) | Mechanism | Proof |
|---|---|---|---|

---

### Section 10: Five-minute verbal summary

A narrative the developer can deliver cold in a verbal interview. It must:
- Cover Stage 4A (design) → Stage 4B (implementation) in one arc
- Name the three concrete improvements with one sentence each on the mechanism
- Include one specific number (latency improvement, batch size, index column name, etc.)
  for each improvement — numbers make answers credible
- End with the biggest honest trade-off

---

## Step 3 — Generate the .docx version

After writing `interview_prep.md`, generate `interview_prep.docx` in the same directory
using `python-docx`. Apply the same formatting used for the DevOps stage4 prep doc:
- Cover page with title, subtitle, developer name
- Navy/blue colour scheme (heading colour `#1A1A2E`, accent `#1B6CA8`)
- Code blocks in monospace with grey background shading
- Q&A pairs with the question in accent blue with a left border, answer indented
- Tables with navy header rows and alternating row shading

Write the generation script to
`scripts/build_interview_prep_docx.py` and run it.

---

## Quality bar

The prep document from the parallel DevOps project had these properties — match them:

- Every data-flow walkthrough named exact function names and file paths, not just
  "the handler calls the service."
- Every Q&A answer referenced actual code behaviour, not generic best-practice answers.
- Trade-offs were honest and specific: "the two-scrape window is ~1.1s, not 30s as the
  brief requires" — not "there are some limitations."
- The document was self-contained: a developer who had not touched the code for two weeks
  could read it and answer any question.

If you cannot find the implementation code, say so explicitly in the document and flag
which sections are based on the design documents only versus verified implementation.
Do not invent implementation details.
