# Validation Strategy

## Governance Checks

- `python scripts/control_plane_check.py` must pass.
- `CURRENT_TASK` must match `config/runtime_status.json.current_packet`.
- Closed gates must cite evidence ids present in `05_evidence_log.md`.
- No implementation, benchmark, load-test, Docker, service, or prototype paths may exist while `experiments_allowed` is `false`.

## Requirements Checks

- Functional requirements cover profile storage, structured filters, aggregations, rule-based keyword mapping, existing clients, and result delivery.
- Non-functional requirements cover latency, scalability, reliability, consistency, maintainability, and single-region assumptions.
- Requirements explicitly preserve Stage 3 auth, RBAC, CLI, and web portal.

## Architecture Checks

- Every component has a clear reason tied to a requirement.
- The design stays simple and maintainable.
- The core design does not introduce microservices, queues, multi-region deployment, streaming, or LLMs unless the decision log justifies a future-only boundary.

## Data Flow Checks

- Ingestion flow is separate from read query flow.
- Query flow covers parsing, validation, cache lookup, database access, aggregation, and response.
- Failure modes cover cache miss, slow query, invalid query, ingestion lag, and database pressure.

## Submission Checks

- Draft is 2-7 Google Docs pages when pasted or converted.
- Diagram is embedded in the document.
- Original diagram source link is available.
- Google Docs sharing is set to "Anyone with the link can view".
- Trade-offs and limitations are explicit.
