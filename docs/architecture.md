\## Architecture



A detailed architecture diagram is available here:



\[View the architecture diagram](docs/architecture.md)



```mermaid

flowchart TD

&#x20;   U\[User Request] --> FE\[React / TypeScript Frontend]



&#x20;   FE --> API\[FastAPI API Layer]



&#x20;   API --> RET\[Semantic Retrieval]

&#x20;   RET --> EMB\[FastEmbed]

&#x20;   EMB --> VEC\[(PostgreSQL + pgvector)]

&#x20;   VEC --> RET



&#x20;   RET --> PLAN\[Grounded Planner]

&#x20;   PLAN --> SRC\[Source-Attributed Execution Plan]



&#x20;   SRC --> GRAPH\[LangGraph Orchestration]



&#x20;   GRAPH --> GOV{Sensitive WRITE Action?}



&#x20;   GOV -->|Yes| HITL\[Human Approval]

&#x20;   GOV -->|No| EXEC\[Execution Agent]



&#x20;   HITL -->|Approve| EXEC

&#x20;   HITL -->|Reject| REJ\[Workflow REJECTED]



&#x20;   EXEC --> SF\[Salesforce Tool]

&#x20;   EXEC --> SAP\[SAP Tool]

&#x20;   EXEC --> SLACK\[Slack Tool]



&#x20;   SF --> VALID\[Deterministic Validation]

&#x20;   SAP --> VALID

&#x20;   SLACK --> VALID



&#x20;   VALID --> LOGS\[(Execution Logs)]

&#x20;   VALID --> DONE\[Workflow COMPLETED]



&#x20;   GRAPH <--> CP\[(PostgreSQL Checkpoints)]



&#x20;   LOGS --> DB\[(PostgreSQL)]

&#x20;   SRC --> DB



&#x20;   classDef frontend fill:#eef2ff,stroke:#6366f1,color:#111827;

&#x20;   classDef ai fill:#f5f3ff,stroke:#7c3aed,color:#111827;

&#x20;   classDef governance fill:#fffbeb,stroke:#d97706,color:#111827;

&#x20;   classDef tools fill:#ecfdf5,stroke:#059669,color:#111827;

&#x20;   classDef data fill:#f8fafc,stroke:#475569,color:#111827;

&#x20;   classDef failure fill:#fef2f2,stroke:#dc2626,color:#111827;



&#x20;   class FE frontend;

&#x20;   class RET,EMB,PLAN,SRC,GRAPH ai;

&#x20;   class GOV,HITL governance;

&#x20;   class EXEC,SF,SAP,SLACK,VALID,DONE tools;

&#x20;   class VEC,CP,LOGS,DB data;

&#x20;   class REJ failure;

```

