# Interview Defense Bank

This file tracks questions the operator must be able to answer without AI.

## Governance Questions

1. Why did you create a control plane before drafting the design?
   - Because the task is graded on reasoning, trade-offs, and explainability. The control plane keeps requirements, decisions, evidence, and final claims aligned.

2. Why is the scope design-document-only?
   - The official deliverable is a Google Docs system design document. Building code would add unnecessary surface area and could distract from the required architecture explanation.

3. Why are experiments disabled?
   - The task does not require benchmarks or prototypes. Disabling experiments prevents unsupported prototype claims from leaking into the final design.

4. Why keep an evidence log?
   - A completed gate needs proof. Evidence ids show which artifact supports each claim and make the work easier to defend in an interview.

5. Why preserve Stage 3 instead of redesigning it?
   - The brief says Stage 3 stays intact and evaluators will notice if it breaks. Stage 4 is about evolving the system under growth, not replacing working surfaces.

## Requirements Questions (B4-REQ-001)

6. Why is the query model structured rather than true natural language?
   - The brief explicitly defines the query model as structured filters, aggregations, and a small rule-based keyword mapper. There is no LLM in the loop. Adding one would invent a requirement the brief rejects, push P95 past the 2 second target, and add cost the NFRs do not budget for. See decision D-005.

7. Which of the items in your draft are functional requirements?
   - FR-1 through FR-12 in Section 1.1: profile storage, structured filters, aggregations, combined queries, rule-based keyword mapping, paginated results, CSV export, GitHub-OAuth/PKCE auth with JWT and refresh tokens, RBAC, versioned API for CLI and web portal, batch ingestion, and result delivery. They describe behaviour the system must perform.

8. Which of the items in your draft are non-functional requirements?
   - NFR-1 through NFR-11 in Section 1.2: P50 below 500 ms, P95 below 2 s, dataset growth into the tens of millions of rows, query rate of hundreds to low thousands per minute, read-heavy workload, single-region deployment, reliability under sustained growth, the consistency model, maintainability and simplicity, bounded query shapes, and Stage 3 preservation. They describe qualities the system must hold while doing the functional work.

9. How did you size the system?
   - Straight from the brief. P50 under 500 ms, P95 under 2 s, tens of millions of profiles, hundreds to low thousands of queries per minute (roughly tens of QPS at peak). I did not invent harder numbers. See decision D-006.

10. Why did you keep Stage 3 in the requirements list instead of treating it as legacy?
    - The brief says Stage 3 stays intact and the mentor warned that broken Stage 3 surfaces fail the work. Auth, RBAC, CLI, and the web portal are existing client surfaces of the same query engine. Stage 4 evolves the query engine; it does not replace those clients.

## Architecture Questions (B4-ARCH-001)

11. Why does the design start with database indexing and caching before adding more complex infrastructure?
    - Because the workload is read-heavy with repeated query patterns. Targeted B-tree indexes remove the work the database is doing on the hot path; a TTL'd query-result cache removes the database call entirely for repeats. Both are cheap, well understood, and reversible. They are pulled before reaching for a read replica or materialized aggregates because adding a replica or maintaining a materialized view costs ongoing operational effort that has to be justified by a measured trigger. See decisions D-007 and D-009.

12. Which requirement justifies each architecture component?
    - Section 2 of the draft lists each component and its requirement reason. Stage 3 clients and the API exist to preserve auth, RBAC, CLI, web portal, pagination, export, and versioning. Query validation and rule-based mapping support structured filters and bounded query shapes. The query-result cache addresses repeated query patterns and latency. PostgreSQL plus targeted indexes addresses relational profile storage at millions to tens of millions of rows. Batch ingestion matches periodic writes. Observability exists so the optional scale levers are enabled only after measured pressure.

13. Why not microservices?
    - The brief's load is hundreds to low thousands of QPM and the data model is one structured profile table family. Splitting the API into multiple services adds network hops, more deploy artifacts, and cross-service consistency reasoning. None of that buys anything against the stated targets. Keeping one Node.js / Express API boundary is easier to operate and defend. See decision D-007.

14. Why not a message queue or stream broker?
    - Writes are periodic batches of profile data, not real-time events. There is no fan-out and no async event flow. A queue would add a moving part with its own failure modes. The batch ingestion worker writes directly to the database in a transaction and then bumps the cache version tag. See decision D-007.

15. Why not Elasticsearch or another search engine?
    - The query shapes the brief lists are filters on structured columns (country, age, gender) and aggregations over those filters. B-tree indexes on the relevant columns and composite indexes on the actual filter combinations the parser emits cover those shapes. A search cluster would duplicate storage and add operational surface for a query model that is already structured.

16. How does the architecture reduce database load?
    - Three complementary effects. (1) The query-result cache absorbs repeats, so the same canonicalized query within the TTL or cache-version window does not touch the database. (2) Indexes on the actual filter columns turn broad scans into indexed access paths. (3) The query envelope and statement timeout prevent unbounded queries from consuming the primary. If those are not enough at observed load, the conditional levers are added: read replica for measured read pressure, materialized aggregate for repeated expensive aggregations, or external pooler for connection saturation.

17. When would a read replica become justified?
    - When primary CPU or read IO sits above its target band under steady load, and the slow-query log shows aggregation queries dominating the wait time. Then heavy aggregations are routed to the replica; transactional reads stay on the primary. Bounded staleness on the replica is acceptable for analytical reads under NFR-8.

## Data Flow Questions (B4-DATA-001)

18. What happens on a cache miss?
    - The API runs the parameterised query against PostgreSQL with a per-statement timeout matching the P95 budget. Rows are paginated and shaped, the response is written back to the managed query-result cache under the canonical key, and the response is returned. Telemetry records the miss, database time, row count, and slow-query details. The first request after an ingestion batch misses because the batch invalidated the cache version.

19. How fresh are query results after batch ingestion?
    - Freshness is one ingestion run. The ingestion worker bumps the cache version tag once at commit; every cache key embeds that tag, so prior cached entries fall out immediately. New requests recompute against the new database state and repopulate the cache. There is no per-key invalidation work and no stale read against the new batch. See decision D-010.

20. What happens when a query is too expensive?
    - First, the query envelope rejects shapes that violate the rules (unallowed columns, page size over the cap, group-by outside the allowlist) with 400 before any work hits the database. Second, the database connection has a statement timeout (e.g. 2 seconds) so a query that fits the envelope but still runs too long is killed and returned as 504; the offending shape is logged so it can be added to the index plan or to the rejected-shape list. Third, sustained pressure triggers the rate limiter and, if needed, the read replica route. See decision D-011.

21. How does the design meet P50 below 500ms and P95 below 2 seconds?
    - P50 is dominated by cache hits: a hit returns without touching the database, which fits well inside the 500 ms budget. P95 is protected by the statement timeout (capped at the NFR-2 budget), the query envelope (no unbounded scans), and indexes on the actual filter columns. Heavy aggregations that still drift over P95 are addressed by the conditional levers: read replica for analytical routes, materialized aggregates for the worst repeated shapes.

22. How does batch ingestion affect consistency?
    - Inside the database: strong consistency, one transaction per batch. Between database and cache: eventually consistent within the version-tag and TTL window; a successful batch immediately invalidates everything. Between primary and the optional read replica: bounded staleness from streaming replication, acceptable for analytical reads under NFR-8. Transactional reads stay on the primary.

## Submission Questions (B4-SUBMISSION-001)

S1. Which evidence proves each required section exists?
   - The QA checklist (`07_qa_checklist.md`) ties every required-deliverables row to an evidence id: FR/NFR -> E-002, Architecture -> E-003, Data Flow -> E-004, Decisions and Limitations -> E-005, Diagram source -> E-006, Submission readiness -> E-007, and post-review simplification -> E-008. Each evidence entry in `05_evidence_log.md` lists the exact section that was updated and the verification command. The evidence chain is what lets a reviewer audit the document end-to-end.

S2. What would you improve after submission?
   - Tune the cache TTL band and the index set against measured hit rates and `pg_stat_statements` output once the system has run under real traffic. Re-evaluate the read-replica trigger from D-009: if observed primary CPU and the slow-query log show the trigger has fired, enable the analytical-route replica path. Revisit the 10x next-lever sequence in Section 5 against actual P95 history. None of those need design changes; they need data.

S3. Which design choices are intentionally simple?
   - Single PostgreSQL source of truth plus a managed query-result cache; one Node.js / Express API boundary; rule-based keyword mapping; batch ingestion; normalized cache keys; a query envelope plus a per-statement timeout. Read replica, materialized aggregates, and external pooler are listed but conditional. Each simplicity is paired with a stated condition under which it would change (decisions D-007, D-008, D-009, D-010, D-011, D-014), so the design is not just simple - it is simple with a documented growth path.

## Diagram Questions (B4-DIAGRAM-001)

D1. How does the diagram match the design?
   - It shows the same core path as the final draft: Stage 3 clients call the existing authenticated API, the API uses a rule-based mapper and bounded query validator, repeated canonical queries hit a short-TTL cache, cache misses use indexed PostgreSQL, periodic ingestion writes batches and invalidates cache, and observability measures latency, slow queries, cache hit rate, DB load, and freshness. The optional scale levers are visually separated so they are not mistaken for first-rollout requirements.

D2. Why are these components included?
   - Each component either preserves Stage 3 or directly answers the Stage 4 pressure points. Stage 3 clients and auth/RBAC remain because the brief preserves them. Query validation, normalized cache keys, and targeted indexes address structured filters, aggregation, repeated patterns, and latency. Batch ingestion addresses periodic growth without inventing real-time streaming. Observability is included because the conditional levers should be enabled only when measured latency, slow-query, cache, or database-load signals prove they are needed.

D3. Which components were intentionally left out?
   - No message queue, streaming pipeline, microservices split, separate search engine, LLM query path, or multi-region routing layer. The brief asks for a simple, maintainable, single-region design around structured profile queries and periodic batch writes. The document also avoids making a read replica, materialized aggregates, or an external pooler part of the default plan; they remain measured next steps.

D4. Why was the diagram simplified after the first submission draft?
   - The first diagram was useful for internal traceability but over-signalled infrastructure complexity. The final diagram was simplified to match the task's grading signal: sound, maintainable scaling of the existing Stage 3 system. The simplification did not remove the design; it separated the core plan from conditional growth levers, which is easier to defend in an interview.

D5. Does simplifying the diagram under-report the design?
   - No. The final draft still records the decisions, trade-offs, limits, and measured triggers. The diagram intentionally shows the first defendable architecture path, not every future option. Conditional read replicas, materialized aggregates, and external poolers are still present as scale levers, but only after observability shows the trigger.

## Decisions And Limitations Questions (B4-DECISIONS-001)

23. What trade-off does caching introduce?
    - Bounded staleness, plus a cold-cache spike. Cache keys embed a global version tag that the ingestion worker bumps at the end of each successful batch, so after a batch every cached entry effectively expires at once. That keeps reads correct against the new batch but causes a brief miss spike where the database, the connection pooler, and the rate limiter must all hold. Tuning the TTL trades off slightly more staleness for a smaller miss spike. See decision D-008.

24. Why not real-time streaming in the core design?
    - Writes are periodic batches, not events. Adding a stream broker (Kafka / Kinesis) and a streaming consumer would introduce a moving part with its own failure modes, ordering and duplicate-handling reasoning, and operational cost, all to satisfy a requirement the brief does not list. Real-time analytics is mentioned only as an optional future evolution. See decision D-007.

25. What does the design intentionally not handle well?
    - Section 5 of the draft. Sub-minute freshness, free-form natural language, cross-region failover, unbounded ad-hoc analytical scans, write-heavy or OLTP workloads, and single-primary as a single failure domain. Each of these is an explicit boundary, not an oversight, and each is traceable to a requirement or a stated assumption.

26. How would real-time analytics be added later without complicating the core design?
    - As a parallel ingestion path. The batch worker stays. An additional consumer reads from a stream and writes to a separate "fresh" table or partition. Read APIs that need real-time results query the fresh table; everything else keeps using the batch-loaded table. The two paths share schema, not transactional semantics. The core scaling story (LB, stateless API, cache, primary, indexes, batch) does not change.

27. How would true natural-language query support be added later without misrepresenting the current task?
    - As an explicit, opt-in layer in front of the rule-based mapper, called only for inputs the rule mapper cannot resolve. The LLM would output a structured query (the same envelope D-011 enforces today) which the existing pipeline would then validate, cache, and execute. That keeps the correctness model and the query envelope intact, and it does not require rewriting the rest of the system.
