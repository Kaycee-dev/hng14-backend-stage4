# Execution Roadmap

Work proceeds by task packet. A packet is not closed until the relevant documents, evidence, QA items, and defense notes match the packet's `done_when`.

| Packet | Goal | Gate |
|---|---|---|
| `B4-GOV-001` | Create governance scaffold and prove no design or implementation work has started outside the control plane | Governance |
| `B4-REQ-001` | Extract functional and non-functional requirements from the official brief | Requirements |
| `B4-ARCH-001` | Define the high-level architecture for scaling the existing query engine | Architecture |
| `B4-DATA-001` | Define ingestion flow, query flow, result flow, and consistency boundaries | Data flow |
| `B4-DECISIONS-001` | Record key design decisions, alternatives, trade-offs, and requirement mapping | Decisions |
| `B4-DIAGRAM-001` | Create the architecture diagram source and export-ready diagram asset | Diagram |
| `B4-SUBMISSION-001` | Assemble the Google Docs-ready draft, reconcile QA, and prepare final submission | Submission |

## Packet Rules

- Each packet starts with a teach-back explanation before content changes.
- Each packet records evidence in the same cycle.
- Each packet updates the defense bank with questions that match the design just written.
- Experiments remain blocked unless the status file explicitly allows them.
