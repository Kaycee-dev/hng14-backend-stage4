@channel
Backend Engineers — Stage 4B Task
Scale Insighta Labs+ Further: System Optimization & Data Ingestion

Stage 4A was design. Stage 4B is proof. Now you build it.

Stage 3 stays intact. Auth, RBAC, CLI, web portal — all of it. We will notice if it breaks.

Stage 4B – System Optimization & Data Ingestion: Scaling Insighta Labs+ Further

Overview
Insighta Labs+ is no longer just growing. It is under pressure. The system is actively used across teams, with increasing query volume, a growing dataset, and new operational demands. What worked at smaller scale is now showing real limitations.

Stage 4A asked you to design a system that could scale. Stage 4B asks you to make it perform. This stage is implementation-focused. You will optimize an existing system, not design a new one.

Context
The system currently operates under these conditions:

• The dataset has grown to over 1 million records and continues to increase
• The system handles hundreds to thousands of queries per minute
• Users interact via both CLI and web clients concurrently
• The database is hosted remotely, every query incurs network latency
• Read traffic dominates, but write pressure is increasing

As usage increases, query response times are slowing down, database load is rising, and repeated queries are causing redundant computation. Users now need to upload large CSV files containing up to 500,000 rows, introducing heavy write operations into an already read-pressured system.

Your Task
Improve the system in three areas:

• Query performance and database efficiency
• Query normalization and cache efficiency
• Large-scale CSV data ingestion

This is an implementation task. Build and demonstrate working solutions.

What to Deliver

1. Query Performance
Improve how queries are executed to reduce latency and database load.

Constraints:
• The API must remain unchanged
• Results must remain correct and consistent
• No new database systems
• No horizontal scaling

Target: responses in the low hundreds of milliseconds.

You may use:

• Indexing
• Caching
• Query restructuring
• Connection pooling
• Any other practical technique you can justify

Every optimization must be justified. Do not add complexity without a clear reason.

2. Query Normalization
Users express the same query in different ways.

_"Nigerian females between ages 20 and 45"_ and _"Women aged 20–45 living in Nigeria"_ represent the same intent. Without normalization, they produce different cache keys, bypass cached results, and cause redundant database calls.

Before executing a query or checking the cache, normalize the parsed filter object into a canonical form. Two queries that produce the same filters must produce the same cache key, regardless of how they were expressed.

Constraints:
• The approach must remain deterministic
• It must not introduce incorrect interpretations of user intent
• No AI or LLMs

3. CSV Data Ingestion
Implement a system that allows users to upload CSV files containing profile data.

File spec:
• Up to 500,000 rows per file
• Delimiter: ,

Hard requirements:

• Do not insert rows one by one
• Do not load the entire file into memory
• Use streaming or chunked processing
• Uploads must not block or degrade query performance
• The system must support concurrent uploads

File validation, rows must be skipped when:

• Required fields are missing
• Field values are invalid (e.g. negative age, unrecognised gender)
• The name already exists in the database (same idempotency rule as POST /api/profiles)
• The row is malformed (wrong column count, broken encoding)

A single bad row must never fail the entire upload. Process what you can, skip what you cannot, and report a summary at the end.

On partial failures: if processing fails midway, rows already inserted must remain. The upload does not roll back.

Expected response:

{
  "status": "success",
  "total_rows": 50000,
  "inserted": 48231,
  "skipped": 1769,
  "reasons": {
    "duplicate_name": 1203,
    "invalid_age": 312,
    "missing_fields": 254
  }
}

Constraints

• No unnecessary infrastructure or overengineering
• Assume limited compute resources
• Assume concurrent read and write workloads throughout
• Solutions must be practical, efficient, and justifiable

Evaluation Criteria

• Query optimization approach and results
• Correctness of normalization logic
• Ingestion efficiency and resilience
• How well you handle edge cases and failures
• Justification of every decision
• Simplicity, unnecessary complexity will count against you

Guidelines

• No components without clear justification
• No overengineering
• Keep solutions clear, practical, and implementable
• Show your reasoning, not just your code

Final Note

This stage evaluates your ability to move from design to real-world engineering. We are looking for your ability to identify bottlenecks, improve performance under constraints, handle concurrency and failure, and make sound engineering decisions. There is no perfect solution. What matters is how your system performs and how you think about it.

Submission
Submit your repository link.
Your repository must contain:
 • Working implementation of all three parts
 • A SOLUTION.md file covering: 
               ◦ Your optimization approach for each part
               ◦ Design decisions and trade-offs
               ◦ A simple before/after comparison for query performance (a table with a few measurements is      sufficient)
               ◦ How you handle ingestion failures and edge cases

SUBMISSION FORM : [link](https://docs.google.com/forms/d/1OoTV2L4_WmKah2IxYdQqAUOnZSvfk8WQrBeJf2lXkP8/preview)

Deadline: May 5, 2026, 11:59pm.

4A you designed a Ferrari on paper. 4B we're taking it for a drive. Pray it starts. :naza-rofl: