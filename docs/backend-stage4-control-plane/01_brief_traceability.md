# Brief Traceability

Every requirement from the official brief must have a planned source, design response, verification, and submission artifact before the final Google Docs document is submitted.

| Brief requirement | Planned design response | Verification | Submission artifact |
|---|---|---|---|
| Existing Stage 3 system remains intact | Treat GitHub auth, RBAC, CLI, and web portal as existing clients around the query engine | Requirements checklist confirms no redesign removes Stage 3 surfaces | Requirements and assumptions sections |
| System stores structured profile data | Model profile data as relational, structured, indexed data | Architecture and data-flow review | Architecture and data flow sections |
| Queries are structured filters, aggregations, and rule-based keyword mapping | Keep query parser rule-based; do not introduce LLM behavior | Defense bank question on query model | Query model note in requirements |
| Data grows from millions to tens of millions | Design for read-heavy relational growth with indexes, caching, and query constraints | Decision log maps scale response to requirements | Non-functional requirements and decisions |
| Hundreds to low thousands of queries per minute | Use simple scaling levers: connection pooling, cache, read replicas if needed, and observability | Decisions log contains trade-offs | Architecture section |
| P50 latency below 500ms | Prioritize repeated-query cache, targeted indexes, precomputed aggregates where justified | Acceptance criteria in validation strategy | Non-functional requirements |
| P95 latency below 2 seconds | Include slow-query detection, timeouts, and bounded query shapes | Acceptance criteria in validation strategy | Non-functional requirements |
| Single-region deployment | Avoid multi-region active-active design | Checker and QA review for overengineering language | Architecture assumptions |
| Read-heavy with batch ingestion | Separate ingestion path from read query path; no streaming queue by default | Data-flow review | Data flow section |
| Requirements required | Draft includes functional and non-functional requirements | QA checklist item | Google Docs section |
| Architecture required | Draft includes high-level component design | QA checklist item | Embedded diagram and architecture section |
| Data flow required | Draft describes ingestion, query processing, retrieval, and response | QA checklist item | Data flow section |
| Design decisions required | Each major decision maps to a requirement | Decisions log and draft section | Decisions section |
| Trade-offs and limitations required | Draft states degradation modes and intentional simplifications | QA checklist item | Limitations section |
| Simplicity is graded | Reject unjustified microservices, queues, multi-region, and jargon | Defense bank and decisions log | Whole document |
| Optional real-time analytics | Mention only as future evolution, not core design | QA checklist item | Optional future section |
| Optional true natural-language query system | Mention only as future evolution using explicit LLM boundary | QA checklist item | Optional future section |
| Diagram must be embedded and original linked | Keep diagram source under `diagrams/source/` and exported asset for Google Docs | Diagram gate evidence | Embedded diagram plus source link |
| Submit Google Docs with link sharing | Final packet checks sharing requirement | Submission gate | Google Docs link |

## Initial Governance Decisions

- Governance before design draft: D-001.
- Design-doc-only scope: D-002.
- Experiments disabled by default: D-003.
- Evidence-backed claims: D-004.
