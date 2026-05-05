Backend Engineers — Stage 4a Task
Scale Insighta Labs+: System Design Under Growth

Congratulations. The system works. Now make it work for everyone, all the time, fast. Stage 4 is not about building new features. It is about proving you understand what happens when the thing you built actually gets used.

Stage 3 stays intact. Auth, RBAC, CLI, web portal — all of it. We will notice if it breaks.

Stage 4 – System Design: Scaling Insighta Labs+

Overview
Insighta Labs+ is a demographic intelligence platform that stores structured profile data (e.g., age, gender, country) and allows users to query and analyze this data. The platform is used by analysts exploring patterns and trends, engineers interacting via a CLI, and internal teams using a web interface. At a high level: Users submit queries → the system processes them → retrieves relevant data → returns results. This system is not just a data store — it is a query engine.

Query Model (Clarification)
Insighta Labs+ does not support true natural language queries. Queries are structured filters and aggregations, or simple keyword-based inputs mapped using rule-based parsing — not AI/LLMs.

Example: `young males in South Africa` → age range: 18–35, gender: male, country: South Africa

Supported: filtering, aggregations, combined filter + aggregation queries.

Context
You have already built a working system — GitHub auth, RBAC, CLI, web client. It is live. The problem is no longer "Can it work?" It is now "Will it continue to work under sustained growth?"

The Situation
More concurrent users, heavier queries, a growing dataset, and repeated query patterns are putting pressure on query performance, response latency, database load, and system reliability.

Scale Assumptions
* Data grows from millions → tens of millions of profiles
* Hundreds to low thousands of queries per minute
* Multiple teams, daily usage, near-interactive response times expected

Performance Targets
* P50 latency: < 500ms
* P95 latency: < 2 seconds

Constraints
Prefer simple, maintainable solutions. Avoid distributed systems jargon. Use managed services where appropriate. Single-region deployment.

Data Characteristics
Structured, relational, read-heavy. Writes happen via periodic or batch ingestion. Not a real-time streaming system.

Estimation & Calculations
Not required. If included, they must support a specific design decision — no math for math's sake. Example: "If ~40% of queries are repeated, caching can significantly reduce database load." If a calculation doesn't influence a decision, leave it out.

Your Task
Design how the system should evolve to handle growth. You are improving an existing system, not building from scratch. Focus on scaling query performance, reducing database load, and maintaining reliability.

What to Deliver
1. Requirements — Functional (what the system must do) and Non-Functional (latency, scalability, reliability, consistency)
2. Architecture — High-level design showing core components and how they interact. A simple diagram is sufficient.
3. Data Flow — How data is ingested, how queries move through the system, how results are returned
4. Design Decisions — Key choices and their trade-offs. Every decision must map back to a requirement.
5. Trade-offs and Limitations — What your design doesn't handle well, where it degrades, what was intentionally simplified

Evaluation Criteria
 Clarity of requirements
 Soundness and practicality of design
 Justification of decisions
 Handling of scale and performance
 Awareness of trade-offs
 Simplicity — unnecessary complexity counts against you

Guidelines
 No components without justification
 No overengineering (e.g., microservices, queues without need)
 Keep it clear, practical, and implementable
 Use concise explanations and structured reasoning

Optional (Bonus)
How would you support real-time analytics in the future? How would you evolve this into a true natural language query system?

Final Note
This is not about designing the most complex system. A simple, well-reasoned design beats a complex one you cannot justify.

RESOURCE: [link](https://medium.com/@shivambhadani_/system-design-for-beginners-everything-you-need-in-one-article-c74eb702540b)
SUBMISSION FORM — [link](https://forms.gle/K1W57xKfE74G5QL79)
Submit a design document in Google Docs
Set sharing to "Anyone with the link can view" before submitting
Length: 2–7 pages
Diagram: Embed the image directly in the doc AND include a link to the original

Deadline: May 5, 2026, 11:59pm @channel 

---