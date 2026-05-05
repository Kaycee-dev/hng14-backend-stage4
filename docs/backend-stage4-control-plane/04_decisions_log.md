# Decisions Log

## D-001 - Use a governed control plane before drafting

- Date: `2026-05-04`
- Decision: Create governance docs, task packets, evidence tracking, QA gates, and a checker before drafting the final design document.
- Rationale: Mentor feedback makes explainability a hard requirement. The task is graded on clarity, practicality, justification, trade-offs, and simplicity.
- Interview defense: "I separated planning and proof from the final document so every design choice has a requirement, a trade-off, and a defense path."

## D-002 - Keep the scope design-document-only

- Date: `2026-05-04`
- Decision: The control plane guards a Google Docs system design deliverable. It does not create application code, benchmark suites, Docker files, or prototypes.
- Rationale: The official task asks for a design document, not implementation. Extra code would increase the defense surface and distract from the 2-7 page deliverable.
- Interview defense: "I focused on the deliverable the brief asked for: a practical scaling design for an existing system, not a new implementation."

## D-003 - Disable experiments by default

- Date: `2026-05-04`
- Decision: `experiments_allowed` is `false` until explicitly changed in `config/runtime_status.json`.
- Rationale: Optional experiments can be useful later, but the deadline and grading criteria favor concise, defensible design work.
- Interview defense: "I blocked experiments so the design document does not quietly depend on unreviewed prototype assumptions."

## D-004 - Evidence ids are required for closed gates

- Date: `2026-05-04`
- Decision: A gate cannot close unless it cites an evidence id present in `05_evidence_log.md`.
- Rationale: Unsupported claims are the exact failure mode the mentor feedback warns about.
- Interview defense: "The evidence log makes it clear which artifact supports each completed stage of the work."

## D-005 - Query model boundary is structured-only

- Date: `2026-05-04`
- Decision: Functional requirements cover structured filters, aggregations, combined queries, and a deterministic rule-based keyword mapper (e.g. `young males in South Africa` -> age 18-35, gender male, country South Africa). The system does not parse arbitrary natural language and does not call any LLM as part of the query path.
- Alternatives considered:
  - LLM-backed natural-language query layer. Rejected: the brief explicitly excludes it, it adds latency and cost the NFRs cannot absorb, and it changes the answer correctness model.
  - Free-text full-text search. Rejected: the data is structured demographic attributes, not unstructured text. Indexed equality and range filters fit the query shapes the brief lists.
- Rationale: Treating the query model as structured keeps the design defensible against the official brief and lets the architecture lean on relational indexes and a query-result cache instead of a model server.
- Interview defense: "The brief defines the query model as structured filters, aggregations, and a small rule-based keyword mapper. Adding an LLM would invent a requirement the brief rejects and would push P95 past the 2-second target."

## D-006 - Non-functional targets are interpreted as the brief states them

- Date: `2026-05-04`
- Decision: The only quantified targets in scope are P50 below 500 ms, P95 below 2 s, dataset growth from millions to tens of millions of profiles, and a query rate of hundreds to low thousands of queries per minute. Throughput, availability, and durability beyond these are treated as "stay healthy under the stated load," not invented SLAs.
- Alternatives considered:
  - Inventing a 99.9% availability SLO and an RPO/RTO target. Rejected: the brief does not list them and pretending they exist would force multi-region or streaming choices the brief explicitly discourages.
  - Designing for tens of thousands of QPS. Rejected: the brief caps the rate at "hundreds to low thousands per minute," which is roughly tens of QPS, not thousands.
- Rationale: Sticking to the brief's numbers prevents over-engineering and keeps every later component justifiable against an actual stated requirement.
- Interview defense: "The latency budget and the QPM range come straight from the brief. I sized indexing, caching, and connection pooling to those numbers; I did not invent harder targets that would have justified more complex infrastructure."

## D-007 - Core component set is existing API + query discipline + cache + PostgreSQL + batch ingestion

- Date: `2026-05-04`
- Decision: The core architecture is the existing Node.js / Express API, deterministic query parsing and validation, normalized cache keys, short-lived query-result caching, PostgreSQL with targeted indexes, simple batch ingestion, and observability. A read replica, materialized aggregates, and an external connection pooler are conditional levers, not first-rollout components.
- Alternatives considered:
  - Microservices split (auth-service, query-service, ingestion-service). Rejected: hundreds to low thousands of QPM does not require it; the split adds network hops, more deploy artifacts, and cross-service consistency work for no win against the stated targets.
  - Message broker (Kafka / SQS) in front of writes. Rejected: writes are periodic batches, not high-frequency events.
  - Elasticsearch / OpenSearch as the query backend. Rejected: profile attributes are structured columns. Indexed equality and range queries on Postgres cover the listed query shapes; adding a search cluster would double the storage and the operational surface.
  - Keep the result cache off and rely only on the database. Rejected: the brief explicitly mentions repeated query patterns as a pressure source, which is exactly the workload a small TTL'd query-result cache neutralizes.
- Rationale: Match component count to actual stated requirements. Pull the cheap levers first, prove they fall short before reaching for more.
- Interview defense: "The first rollout is not a platform rewrite. I keep the existing API and database, then add bounded queries, normalized caching, targeted indexes, batch ingestion discipline, and observability. Replicas, aggregates, and an external pooler are named only as measured next levers."

## D-008 - Cache TTL plus version-tag invalidation, not write-through

- Date: `2026-05-04`
- Decision: The query-result cache uses a short TTL (default 60-300 seconds) plus a global version tag that the batch ingestion worker bumps at the end of each successful batch. Cache entries embed the version tag in their key, so a version bump invalidates everything served from the previous batch.
- Alternatives considered:
  - Per-query targeted invalidation. Rejected: filter combinations are open-ended and computing the affected key set is more expensive than letting a version bump invalidate them all.
  - Write-through cache. Rejected: writes are batch, so the "write" event is the end of an ingestion run, not per-row updates.
  - No invalidation, only TTL. Rejected: ingestion can move many rows; relying on TTL alone would serve stale aggregates for minutes.
- Rationale: Batch ingestion happens infrequently. A version-tag bump is one Redis SET. It costs nothing on the read path and gives a clean staleness boundary that the consistency NFR (NFR-8) accepts.
- Interview defense: "Caching is the cheapest way to absorb repeated queries (NFR-1, NFR-2). I keep it correct under batch ingestion by tagging keys with a version that the batch worker bumps after a successful load. TTL is the safety net if anything else goes wrong."

## D-009 - Read replica and materialized aggregates are conditional, not default

- Date: `2026-05-04`
- Decision: The architecture starts with one PostgreSQL primary. A read replica is added only when sustained load drives primary CPU or read IO above its target band, at which point heavy aggregation queries are routed to the replica. Materialized aggregates are added only when a specific repeated heavy aggregation keeps breaching P95 even with caching and indexes.
- Alternatives considered:
  - Add a read replica from day one. Rejected: it is operational cost without an observed reason; primary plus indexes plus cache covers the stated load.
  - Maintain materialized aggregates for every common query shape. Rejected: it inflates ingestion time, complicates invalidation, and pre-pays a cost the workload may never demand.
- Rationale: Each scaling lever should have a trigger. Adding levers without triggers is the kind of overengineering the brief penalizes.
- Interview defense: "I listed read replica and materialized aggregates with their triggers, not as default components. If the metrics never show the trigger, the architecture stays simpler."

## D-010 - Ingestion is per-batch transactional with idempotent batch ids

- Date: `2026-05-04`
- Decision: Each ingestion run owns one batch id and commits all of its upserts inside one transaction. Validation failures send rows to a quarantine table without aborting the batch. On commit the worker bumps the cache version tag and refreshes any in-use materialized aggregates. On commit failure the cache version stays where it was and the same batch id is retried on the next scheduled run.
- Alternatives considered:
  - Per-row commit. Rejected: a partial batch leaves the cache half-aware of new data and complicates retry semantics.
  - Streaming ingestion. Rejected: the brief explicitly states writes are batch.
- Rationale: The batch boundary is the consistency boundary. One transaction plus one cache version bump is the simplest correct shape, and the idempotent batch id makes retries safe.
- Interview defense: "Freshness is one ingestion run. After a successful batch, the next request that hits any cache key sees a new version tag, so cached entries from the previous batch fall out without per-key invalidation."

## D-011 - Every query runs inside a fixed envelope with a statement timeout

- Date: `2026-05-04`
- Decision: The query parser enforces an envelope before the query reaches the database: only allowlisted filter columns and operators, page size capped (default 50, hard max around 500), aggregation cardinality bounded to a known set of group-by columns, and a per-statement timeout (e.g. 2 seconds) set on the connection. Anything outside the envelope is rejected with 400. A query that times out returns 504 and is logged for index review.
- Alternatives considered:
  - Run user queries unbounded and rely on the database to "do its best". Rejected: one bad query starves the rest and blows the P95 budget.
  - Scale the database harder instead of bounding queries. Rejected: it spends money to compensate for missing input validation.
- Rationale: NFR-10 explicitly calls for bounded query shapes, and the latency NFRs cannot survive an unbounded query holding a connection. The envelope plus the timeout is the cheapest way to keep one expensive caller from harming the others.
- Interview defense: "The envelope and the statement timeout protect the latency budget and the database. A query that does not fit the envelope is rejected fast; a query that fits but is still too expensive is killed at the timeout boundary, not at the user's patience boundary."

## D-012 - Diagram source is Mermaid and separates core path from conditional levers

- Date: `2026-05-04`
- Decision: The architecture diagram source is a Mermaid `flowchart TD` file at `diagrams/source/architecture.mmd`. The diagram shows the core path first (clients, existing API, query engine improvements, cache, PostgreSQL, batch ingestion, observability) and places read replica, materialized aggregates, and external connection pooler inside a separate conditional-levers box.
- Alternatives considered:
  - Hand-drawn diagram (Excalidraw / draw.io). Rejected: the source is a binary or a vendor-locked format, which weakens the "link to original" requirement and complicates round-trip edits.
  - ASCII diagram in the markdown only. Rejected: the brief explicitly requires an embedded image plus an original source link.
- Rationale: Mermaid is plain text, so the "link to original" requirement points to a real editable source. Keeping requirement ids out of the node labels makes the diagram readable in Google Docs and avoids making conditional levers look like mandatory infrastructure.
- Interview defense: "The diagram intentionally shows the smallest sound architecture first. The growth levers are visible, but they are separated so the reviewer can see they are conditional responses to measurements, not show-off defaults."

## D-013 - Final submission state: title, sharing, source link

- Date: `2026-05-04`
- Decision: The Google Docs submission uses the title "Insighta Labs+ Stage 4 Scaling Design," with sharing set to "Anyone with the link can view," with the rendered PNG (`diagrams/exported/architecture.png`) embedded under the Architecture Diagram section and a public link to the `.mmd` source (`diagrams/source/architecture.mmd`) placed directly underneath as the "original source" link.
- Alternatives considered:
  - Submit the markdown raw without converting to Google Docs. Rejected: the brief specifically asks for a Google Docs link.
  - Embed only the Mermaid source block (no PNG). Rejected: the brief requires both an embedded image and a link to the original.
- Rationale: Locks the final-state decisions so the operator's upload is a checklist and not a redesign.
- Interview defense: "The brief says embed the image directly and include a link to the original. The submission state encodes both: a PNG export from the Mermaid source goes inline in Section 7, and a link to the Mermaid source itself goes underneath as the original. Sharing is set to 'Anyone with the link can view' before the link is submitted."

## D-014 - Simplify the final presentation to avoid over-engineering signals

- Date: `2026-05-05`
- Decision: Replace the earlier detailed control-plane draft and dense diagram with a compact final submission draft and a simpler core-path diagram. The final submission presents replicas, materialized aggregates, and external pooling as conditional scale levers instead of first-rollout components.
- Rationale: The official brief explicitly rewards simplicity and penalizes unnecessary complexity. The earlier artifact was defensible as an internal traceability view but too visually busy for a 2-7 page Google Docs submission.
- Interview defense: "I revised the final presentation after checking it against the brief. The core design now shows the smallest practical improvement path; advanced levers remain documented, but only as measurement-triggered follow-ups."
