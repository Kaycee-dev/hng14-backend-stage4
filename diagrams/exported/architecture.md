# architecture.png (export-ready reference)

The Google Docs submission embeds an exported image of the practical Stage 4A architecture. The exported image lives at `diagrams/exported/architecture.png`.

## Source Of Truth

- Source diagram: `diagrams/source/architecture.mmd` (Mermaid `flowchart TD`).
- Submission text it must match: `drafts/insighta-labs-stage4-design.md` Section 2 and Section 6.

## Export Command

Run either:

- Web: paste `diagrams/source/architecture.mmd` into <https://mermaid.live/>, then **Actions > Download PNG**.
- CLI: `mmdc -i diagrams/source/architecture.mmd -o diagrams/exported/architecture.png -b transparent -t default`.

Save the result as `diagrams/exported/architecture.png`.

## Embed Checklist

- [x] PNG saved to `diagrams/exported/architecture.png`.
- [ ] Image inserted in the Google Docs document under "Architecture Diagram".
- [ ] A public link to the original `architecture.mmd` source is placed directly under the embedded image.
- [ ] Image is readable at default Google Docs zoom.

## Components The Image Must Contain

Core path:

1. Stage 3 clients: CLI and Next.js web.
2. Existing backend API with auth/RBAC preserved.
3. Query engine improvements: rule-based mapper, query validator, normalized cache key.
4. Query-result cache with TTL and batch-version invalidation.
5. PostgreSQL source of truth with targeted indexes.
6. Periodic batch ingestion with validation, batch writes, and cache invalidation.
7. Observability: latency, slow queries, cache hit rate, DB load, ingestion freshness.

Conditional levers, clearly separated from the core path:

1. Read replica.
2. Materialized aggregates.
3. External connection pooler.

The diagram should not present these conditional levers as mandatory first-rollout components.
