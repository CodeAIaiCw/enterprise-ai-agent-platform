\# Enterprise AI Agent Platform



> A governed multi-agent orchestration platform for planning, approving, executing, and auditing enterprise workflows.



The Enterprise AI Agent Platform converts natural-language business requests into grounded, source-attributed execution plans across enterprise systems.



Instead of allowing an AI agent to execute arbitrary actions, the platform retrieves approved capabilities from an enterprise knowledge base, constructs a grounded workflow, pauses sensitive operations for human approval, executes approved tools through a durable LangGraph workflow, and records auditable execution results.



\---



\## Highlights



\- Semantic capability retrieval with FastEmbed and pgvector

\- Retrieval-grounded workflow planning

\- Source attribution and similarity evidence

\- Multi-system enterprise orchestration

\- Durable LangGraph execution and checkpoints

\- Human-in-the-loop approval for sensitive operations

\- Deterministic execution validation

\- PostgreSQL audit logging

\- REST API built with FastAPI

\- React/TypeScript showcase interface

\- Full-stack Docker deployment

\- Automated API and workflow integration tests



\---



\## Demo Workflow



A user submits a business request such as:



> Onboard a new customer, verify the customer record, and notify the team.



The platform retrieves relevant enterprise capabilities and produces a grounded plan:



```text

Business Request

&#x20;      │

&#x20;      ▼

Semantic Retrieval

&#x20;      │

&#x20;      ├── Salesforce.create\_customer

&#x20;      ├── SAP.verify\_customer

&#x20;      └── Slack.send\_notification

&#x20;      │

&#x20;      ▼

Grounded Planner

&#x20;      │

&#x20;      ▼

LangGraph Workflow

&#x20;      │

&#x20;      ▼

Human Approval

&#x20;      │

&#x20;      ▼

Enterprise Tool Execution

&#x20;      │

&#x20;      ▼

Validation + Audit Logs

&#x20;      │

&#x20;      ▼

COMPLETED

```



Example plan:



| Step | System | Action | Type | Approval |

|---|---|---|---|---|

| 1 | Salesforce | `create\_customer` | WRITE | Required |

| 2 | SAP | `verify\_customer` | VALIDATE | Automatic |

| 3 | Slack | `send\_notification` | NOTIFY | Automatic |



Sensitive `WRITE` operations are prevented from executing until explicit human approval is received.



\---



\## Architecture



```text

┌──────────────────────────────────────────────────────────────┐

│                     React / TypeScript                       │

│                        Frontend                              │

└──────────────────────────────┬───────────────────────────────┘

&#x20;                              │

&#x20;                              │ REST API

&#x20;                              ▼

┌──────────────────────────────────────────────────────────────┐

│                         FastAPI                              │

│                                                              │

│   ┌───────────────────┐       ┌──────────────────────────┐   │

│   │ Grounded Planner  │◄──────│ Semantic Retriever       │   │

│   └─────────┬─────────┘       │ FastEmbed + pgvector     │   │

│             │                 └────────────┬─────────────┘   │

│             ▼                              │                 │

│   ┌───────────────────┐                    │                 │

│   │     LangGraph     │                    │                 │

│   │   Orchestration   │                    │                 │

│   └─────────┬─────────┘                    │                 │

│             │                              │                 │

│             ▼                              │                 │

│   ┌───────────────────┐                    │                 │

│   │ Human Approval    │                    │                 │

│   │      HITL         │                    │                 │

│   └─────────┬─────────┘                    │                 │

│             │                              │                 │

│             ▼                              │                 │

│   ┌─────────────────────────────────────┐  │                 │

│   │ Enterprise Tool Execution           │  │                 │

│   │ Salesforce → SAP → Slack            │  │                 │

│   └─────────────────┬───────────────────┘  │                 │

│                     │                      │                 │

│                     ▼                      │                 │

│             Audit + Validation             │                 │

└─────────────────────┬──────────────────────┴─────────────────┘

&#x20;                     │

&#x20;                     ▼

┌──────────────────────────────────────────────────────────────┐

│                 PostgreSQL + pgvector                        │

│                                                              │

│  Workflows • Knowledge • Embeddings • Checkpoints • Logs    │

└──────────────────────────────────────────────────────────────┘

```



A polished architecture graphic will also be included in `docs/`.



\---



\## Retrieval-Grounded Planning



The planner does not rely only on model knowledge.



Enterprise capabilities are stored as knowledge documents with metadata describing:



\- system

\- action

\- tool name

\- action type

\- approval requirements



Each document receives a 384-dimensional embedding.



When a user submits a request, the platform performs semantic similarity search through PostgreSQL using pgvector.



Example retrieval:



```text

0.6164  Salesforce  Create Customer in Salesforce

0.6143  Slack       Send Workflow Notification to Slack

0.5394  SAP         Verify Customer in SAP

```



The retrieved capabilities become the evidence used to construct the execution plan.



Every planned step exposes its source document and similarity score in the UI.



\---



\## Human-in-the-Loop Governance



Enterprise agents should not perform sensitive operations without controls.



Actions are classified by operation type.



For example:



```text

WRITE       → approval required

VALIDATE    → automatic

NOTIFY      → automatic

```



When LangGraph encounters an approval-required operation, workflow execution pauses and persists its state.



```text

PENDING

&#x20;  │

&#x20;  ▼

RUN

&#x20;  │

&#x20;  ▼

AWAITING\_APPROVAL

&#x20;  │

&#x20;  ├──────── REJECT ───────► REJECTED

&#x20;  │

&#x20;  └──────── APPROVE

&#x20;               │

&#x20;               ▼

&#x20;            EXECUTE

&#x20;               │

&#x20;               ▼

&#x20;            VALIDATE

&#x20;               │

&#x20;               ▼

&#x20;            COMPLETED

```



Rejected workflows do not execute the protected enterprise tools.



\---



\## Durable Workflow Orchestration



LangGraph manages workflow state and resumable execution.



PostgreSQL checkpoint persistence allows workflows to stop at governance boundaries and resume after an approval decision.



The platform therefore separates:



```text

Planning

&#x20;   ↓

Governance

&#x20;   ↓

Execution

```



rather than treating an AI response as permission to immediately modify enterprise systems.



\---



\## Auditable Execution



Every executed tool call produces an execution log containing information such as:



\- workflow identifier

\- execution step

\- enterprise system

\- tool name

\- execution status

\- execution duration

\- returned result

\- errors



Example:



```text

Salesforce  salesforce.create\_customer   SUCCESS

SAP         sap.verify\_customer          SUCCESS

Slack       slack.send\_notification      SUCCESS

```



The showcase UI exposes these logs through the execution timeline and agent trace.



\---



\## Validation



Successful tool execution alone does not automatically imply a successful workflow.



After execution, the platform performs deterministic validation of the results.



A successful workflow reaches:



```text

Workflow status: COMPLETED

Executed steps:  3

Validation:      PASSED

```



This separates execution from outcome verification.



\---



\## Agent Trace



The frontend exposes the major decision stages involved in a workflow:



```text

RETRIEVAL

&#x20;   ↓

PLANNER

&#x20;   ↓

GOVERNANCE

&#x20;   ↓

EXECUTION

&#x20;   ↓

VALIDATION

```



This makes the agent's behavior inspectable rather than presenting only a final AI-generated answer.



\---



\## Technology Stack



\### Frontend



\- React

\- TypeScript

\- Vite

\- nginx



\### Backend



\- Python

\- FastAPI

\- Pydantic

\- SQLAlchemy

\- Structlog



\### Agent Orchestration



\- LangGraph

\- PostgreSQL checkpoint persistence



\### Retrieval



\- FastEmbed

\- pgvector

\- 384-dimensional embeddings

\- semantic similarity search



\### Data



\- PostgreSQL 16

\- pgvector



\### Infrastructure



\- Docker

\- Docker Compose



\### Testing



\- pytest

\- FastAPI TestClient

\- workflow integration tests



\---



\## Project Structure



```text

enterprise-ai-agent-platform/

│

├── backend/

│   ├── app/

│   │   ├── api/

│   │   ├── core/

│   │   ├── graph/

│   │   ├── models/

│   │   ├── rag/

│   │   ├── services/

│   │   └── tools/

│   │

│   ├── scripts/

│   ├── tests/

│   ├── Dockerfile

│   └── requirements.txt

│

├── frontend/

│   ├── src/

│   ├── public/

│   ├── Dockerfile

│   ├── nginx.conf

│   └── package.json

│

├── docs/

├── docker/

├── terraform/

├── docker-compose.yml

└── README.md

```



\---



\## Running with Docker



\### Prerequisites



Install:



\- Docker Desktop

\- Docker Compose



Clone the repository and enter the project directory:



```bash

git clone <repository-url>

cd enterprise-ai-agent-platform

```



Start the complete stack:



```bash

docker compose up --build

```



Docker Compose starts:



```text

enterprise-ai-postgres

enterprise-ai-backend

enterprise-ai-frontend

```



Check service status:



```bash

docker compose ps

```



The PostgreSQL service should report a healthy status.



\### Application



Frontend:



```text

http://localhost:5173

```



Backend API:



```text

http://localhost:8000

```



Swagger API documentation:



```text

http://localhost:8000/docs

```



Liveness endpoint:



```text

http://localhost:8000/api/v1/live

```



Stop the platform with:



```bash

docker compose down

```



\---



\## API



Core endpoints include:



```text

POST  /api/v1/planner



GET   /api/v1/workflows/{workflow\_id}

GET   /api/v1/workflows/{workflow\_id}/logs



POST  /api/v1/workflows/{workflow\_id}/run

POST  /api/v1/workflows/{workflow\_id}/approve

POST  /api/v1/workflows/{workflow\_id}/reject



POST  /api/v1/execute/{workflow\_id}



GET   /api/v1/knowledge/{document\_id}



GET   /api/v1/live

```



Interactive API documentation is available through FastAPI Swagger UI.



\---



\## Example Lifecycle



\### 1. Generate a plan



The user submits a natural-language business request.



The platform retrieves matching capabilities and creates a source-attributed plan.



Initial state:



```text

PENDING

```



\### 2. Run the workflow



```text

POST /api/v1/workflows/{workflow\_id}/run

```



A sensitive write operation causes the graph to pause:



```text

AWAITING\_APPROVAL

```



\### 3. Approve



```text

POST /api/v1/workflows/{workflow\_id}/approve

```



LangGraph resumes from its persisted checkpoint.



\### 4. Execute



The approved workflow invokes:



```text

Salesforce.create\_customer

&#x20;       ↓

SAP.verify\_customer

&#x20;       ↓

Slack.send\_notification

```



\### 5. Validate



The platform validates the results and records execution logs.



Final state:



```text

COMPLETED

```



\---



\## Automated Tests



The backend includes automated coverage for the planner, knowledge API, governance lifecycle, execution, validation, and audit behavior.



Run:



```bash

cd backend

pytest -v

```



The integration suite verifies scenarios including:



```text

planner → PENDING



run

→ AWAITING\_APPROVAL



approve

→ enterprise execution

→ validation

→ COMPLETED



reject

→ REJECTED

→ no protected tool execution



completed workflow

→ second approval rejected

```



\---



\## Design Decisions



\### Retrieval before planning



The platform retrieves enterprise capabilities before creating the workflow plan.



This reduces unsupported tool selection and gives each planned action traceable evidence.



\### Explicit governance boundary



Approval is part of the execution graph rather than a frontend-only confirmation dialog.



The workflow itself cannot continue past the protected operation until approval occurs.



\### Durable checkpoints



Approval may occur well after planning.



Persisting LangGraph checkpoints allows the workflow to resume rather than reconstructing execution state.



\### PostgreSQL as the operational foundation



PostgreSQL stores application data while pgvector adds semantic retrieval and the LangGraph checkpointer adds durable agent state.



This keeps the architecture understandable while demonstrating multiple enterprise AI data patterns.



\### Deterministic validation



The platform does not use an LLM to decide whether mocked enterprise operations succeeded.



Execution results are checked deterministically.



\### Inspectability



Retrieval evidence, plans, governance decisions, execution logs, outputs, and validation state are visible in the interface.



The goal is governed and observable agent execution rather than opaque autonomy.



\---



\## Current Enterprise Tool Adapters



The showcase currently demonstrates three enterprise capability adapters:



\### Salesforce



```text

salesforce.create\_customer

```



Creates a simulated Salesforce customer record.



\### SAP



```text

sap.verify\_customer

```



Validates the simulated customer record.



\### Slack



```text

slack.send\_notification

```



Simulates delivery of a workflow notification.



The adapters intentionally use deterministic showcase behavior so the orchestration, governance, retrieval, checkpointing, and audit architecture can be demonstrated without requiring external enterprise credentials.



\---



\## Current Scope



This repository is an engineering showcase rather than a production enterprise deployment.



Current limitations include:



\- enterprise tool adapters are simulated

\- authentication and RBAC are not yet implemented

\- secrets management is development-oriented

\- retrieval knowledge is seeded for the demonstration

\- production observability and distributed tracing are future work



These boundaries keep the showcase focused on the agent architecture itself.



\---



\## Roadmap



Potential extensions include:



\- real Salesforce integration

\- real Slack integration

\- authentication

\- role-based access control

\- approval roles and policies

\- organization/workspace isolation

\- secrets management

\- distributed tracing

\- additional enterprise systems

\- richer retrieval corpora

\- production cloud deployment

\- CI/CD

\- policy-as-code governance



\---



\## What This Project Demonstrates



This project explores a practical question in enterprise agent engineering:



> How can an AI system move from natural-language intent to enterprise action without giving the model unrestricted execution authority?



The architecture combines:



```text

Semantic Retrieval

&#x20;      +

Grounded Planning

&#x20;      +

Durable Orchestration

&#x20;      +

Human Governance

&#x20;      +

Tool Execution

&#x20;      +

Auditability

&#x20;      +

Validation

```



to create a controlled enterprise agent workflow.



\---



\## Status



```text

Core orchestration        COMPLETE

Semantic retrieval        COMPLETE

Grounded planning         COMPLETE

Source attribution        COMPLETE

Human approval            COMPLETE

Durable checkpoints       COMPLETE

Enterprise tool execution COMPLETE

Audit logging             COMPLETE

Validation                COMPLETE

Automated tests           COMPLETE

Dockerized full stack     COMPLETE

Showcase UI               COMPLETE

Public deployment         NEXT

```



\---



\## License



This project is currently intended as a portfolio and engineering showcase. Add an explicit open-source license before distributing or accepting external contributions.

