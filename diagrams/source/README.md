# Diagram Source

This folder holds the editable diagram source for the Insighta Labs+ Stage 4 design document.

## Active Source

- `architecture.mmd` - Mermaid `flowchart TD` source for the final submission architecture. It mirrors Section 2 and Section 6 of `drafts/insighta-labs-stage4-design.md`.

## What The Diagram Must Show

- existing Stage 3 clients: Next.js web portal and CLI
- existing backend API with auth/RBAC preserved
- query engine improvements: rule-based mapper, query validator, normalized cache key
- query-result cache with short TTL and batch-version invalidation
- PostgreSQL source of truth with targeted B-tree indexes
- periodic batch ingestion that validates rows, writes batches, and invalidates cache after commit
- observability for latency, slow queries, cache hit rate, DB load, and ingestion freshness
- conditional scale-levers box for read replica, materialized aggregates, and external connection pooler

## Export Workflow

The Google Docs submission requires an embedded image plus a link to the original source.

1. Open `architecture.mmd` in <https://mermaid.live/> or render with the Mermaid CLI:
   `mmdc -i diagrams/source/architecture.mmd -o diagrams/exported/architecture.png -b transparent`
2. Save the rendered PNG (or SVG) to `diagrams/exported/architecture.png`.
3. In Google Docs: Insert > Image > Upload from computer, then paste a link to this `architecture.mmd` file (e.g. the GitHub blob URL) under the embedded image as the "original source" link required by the brief.

## Edit Discipline

- Keep first-rollout components separate from conditional scale levers.
- Do not promote read replicas, materialized aggregates, external poolers, queues, microservices, or streaming systems into the core path without a recorded decision.
- If the draft changes, update `architecture.mmd` in the same packet so the QA gate stays consistent.
