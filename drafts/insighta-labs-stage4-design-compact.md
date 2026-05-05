# Insighta Labs+ Stage 4 Scaling Design

## 1. Requirements

Insighta Labs+ is an existing demographic intelligence platform with GitHub OAuth, RBAC, CLI access, a web portal, API versioning, pagination, and CSV export already working from Stage 3. Stage 4 keeps those surfaces intact and focuses on scaling the query engine under growth.

**Functional requirements.** The system must store structured profile data such as age, gender, and country; support structured filters, aggregations, and filter-plus-aggregation queries; map simple keyword inputs into structured filters using deterministic rules; paginate list results; export CSV results; enforce auth and role checks; and ingest profile data through periodic batch loads.

**Non-functional requirements.** The target is P50 latency below 500 ms and P95 below 2 seconds while the dataset grows from millions to tens of millions of profiles and traffic reaches hundreds to low thousands of queries per minute. The workload is read-heavy, single-region, relational, and batch-ingestion oriented. The design should reduce database load, stay reliable under repeated query patterns, and remain simple enough to operate and defend.

The query model is intentionally not true natural language. A phrase like "young males in South Africa" is converted by a rule-based mapper into filters such as age range, gender, and country. Inputs outside the supported rules should fail clearly rather than being guessed.

## 2. Architecture

The core design uses the smallest set of changes that directly address the brief: bounded query validation, normalized cache keys, short-lived query-result caching, PostgreSQL indexes, simple batch ingestion, and observability. Read replicas, materialized aggregates, and an external connection pooler are not first-rollout requirements; they are measured follow-up levers if P95 latency, database load, or connection pressure remains high after the simpler changes.

The main components are:

- **Existing Stage 3 clients:** the CLI and Next.js web portal continue calling the versioned API. Auth, RBAC, pagination, and CSV export remain intact.
- **Existing backend API:** the Node.js/Express API remains the single application boundary. It preserves auth and RBAC, runs the rule-based keyword mapper, validates query shape, builds normalized cache keys, and returns JSON or CSV responses.
- **Query-result cache:** a managed cache stores repeated query results using a canonical key made from route, role scope, normalized filters, page cursor, and cache version. Short TTLs limit staleness and keep cache failure non-fatal.
- **PostgreSQL:** the relational source of truth. The primary scaling work is targeted indexing for common equality, range, sort, and aggregation paths, plus statement timeouts for bounded latency.
- **Batch ingestion:** periodic ingestion validates incoming rows, writes valid rows to PostgreSQL in batches, and invalidates query cache after successful commit.
- **Observability:** logs and metrics track P50/P95 latency, slow queries, cache hit rate, database load, and ingestion freshness.
- **Conditional scale levers:** add a read replica only for measured read pressure, materialized aggregates only for repeated expensive aggregations, and an external pooler only when database connections saturate.

The design deliberately avoids microservices, queues, a search engine, multi-region routing, and LLM-based query interpretation. Those would add operational cost without being required by the stated workload.

## 3. Data Flow

**Query flow.** A CLI or web request reaches the existing API. The API validates the access token, checks the user role, applies rate limits, and validates the query envelope. If the input is a simple keyword phrase, the rule-based mapper converts it into structured filters. The API builds a canonical cache key and checks the query-result cache. On a hit, the cached response is returned. On a miss, the API queries PostgreSQL using indexed filters, shapes the result as JSON or CSV, writes the result to cache, and returns it to the client.

**Ingestion flow.** The ingestion process runs on a schedule. It reads the next batch, validates rows, skips or reports malformed rows, writes valid rows to PostgreSQL in batches, and invalidates the query-result cache after a successful commit. Ingestion is separate from the request path, so large writes do not run inside user query requests.

**Consistency boundary.** PostgreSQL remains the source of truth. Cache entries are eventually consistent within the TTL and cache-version window. That is acceptable because the system serves analytical reads over batch-loaded demographic data, not real-time transactional updates.

**Failure behavior.** If the cache is unavailable, the API bypasses cache and remains correct, though slower. If a query exceeds the allowed envelope or statement timeout, it is rejected or timed out instead of harming the database. If ingestion fails before commit, cache invalidation does not happen and the next run can retry.

## 4. Design Decisions And Trade-Offs

| Decision | Reason | Trade-off |
|---|---|---|
| Use deterministic structured queries, not LLM interpretation | Keeps latency, correctness, and cache keys predictable | Some free-text inputs return 400 |
| Normalize query filters before caching | Equivalent filters reuse the same cache entry | Requires strict canonicalization rules |
| Add query-result caching | Repeated queries are a stated pressure source; cache reduces DB load | Results can be briefly stale until TTL/version invalidation |
| Keep PostgreSQL as the only database | Data is relational and structured; no new DB system is needed | The primary remains the main capacity constraint |
| Add indexes before heavier infrastructure | Indexes directly improve common filter and sort paths | Extra indexes slow batch writes slightly |
| Keep ingestion simple and batch-based | Matches the brief's data characteristics | Freshness is tied to ingestion cadence |
| Treat replicas, aggregates, and external poolers as conditional levers | Avoids overengineering while preserving a growth path | Requires later operational work if measurements trigger them |
| Enforce query envelopes and statement timeouts | Protects P95 latency and database health | Some broad analytical queries must be narrowed |

The first optimization sequence is: index the real filter shapes, normalize and cache repeated queries, monitor slow queries, then add a read replica, materialized aggregate, or external pooler only for measured bottlenecks. This keeps the system simple while still giving a practical path beyond the initial scale target.

## 5. Trade-Offs And Limitations

This design does not provide real-time analytics; freshness is bounded by ingestion cadence. It does not provide true natural-language querying; unsupported text is rejected unless the rule mapper can convert it deterministically. It does not solve regional outages because the brief specifies single-region deployment. It also does not guarantee every possible analytical query will run; unbounded queries are rejected or moved to materialized aggregates when justified.

For future real-time analytics, add a streaming lane beside the batch ingestion path and query a recent-data partition together with the main table. For true natural-language support, place an LLM only in front of the existing structured-query envelope: the model may propose filters, but the validator still decides what can run. The LLM must not answer directly from text or bypass RBAC, caching, and query limits.

## 6. Architecture Diagram

Embed `diagrams/exported/architecture.png` here.

Original source: `diagrams/source/architecture.mmd`
