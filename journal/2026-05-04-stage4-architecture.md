# 2026-05-04 - B4-ARCH-001 Architecture

## Teach-Back

Concept: read-heavy architecture under sustained growth. The cheap scaling levers are: stateless app replicas behind a load balancer (so adding boxes adds capacity), B-tree indexes on the columns that filters actually use (so the database stops scanning), a connection pooler in front of the database (so N replicas do not eat all the connections), and a query-result cache (so repeated query patterns return without hitting the database at all).

Design decision: I picked a small, justified component set: edge LB, stateless Node.js API replicas, Redis result cache, single PostgreSQL primary with indexes, optional read replica when the primary saturates, optional materialized aggregates for the worst slow queries, and a separate batch ingestion worker. Every component maps to at least one requirement.

Expected deliverable: Section 2 of the draft contains the architecture, the deliberately-absent list (no queue, no microservices, no streaming, no LLM, no search engine), and a component-to-requirement table.

Likely interview question: "Why not microservices, or a message queue?" Answer: the brief sizes the system at hundreds to low thousands of QPM and batch ingestion. Splitting the API into services or adding a broker would add network hops, deployment surface, and consistency reasoning that the stated load does not justify. A single Node.js service plus a managed Postgres plus a managed Redis covers the targets at lower complexity.

## Failure Modes To Avoid

- Adding components without a requirement. Caught by the component-to-requirement map.
- Slipping into "we should have Kafka" or "we should microservice this." Caught by D-007 and the "What Is Deliberately Absent" subsection.
- Treating a read replica or materialized views as default. They are conditional levers that need a measured trigger before they appear.

## Evidence

- `E-003` records the architecture section update.

## Next Step

Advance to `B4-DATA-001` and describe ingestion flow, query flow, cache lookup, database access, and response delivery.
