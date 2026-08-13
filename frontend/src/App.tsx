import { useMemo, useState } from "react";
import "./App.css";

const API_BASE =
  "https://enterprise-ai-agent-platform-production.up.railway.app/api/v1";

type PlanSource = {
  document_id: string;
  source_name: string;
  title: string;
  similarity: number;
};

type PlanStep = {
  step_id: number;
  system: string;
  action: string;
  description: string;
  action_type: "READ" | "WRITE" | "VALIDATE" | "NOTIFY";
  requires_approval: boolean;
  sources: PlanSource[];
};

type ExecutionPlan = {
  steps: PlanStep[];
};

type PlannerResponse = {
  workflow_id: string;
  status: string;
  plan: ExecutionPlan;
};

type InterruptPayload = {
  type: string;
  workflow_id: string;
  message: string;
};

type ExecutionResult = {
  step: number;
  system: string;
  result: Record<string, unknown>;
};

type RunResponse = {
  workflow_id: string;
  status: string;
  interrupt?: InterruptPayload;
  execution_results?: ExecutionResult[];
  validation_passed?: boolean;
  error?: string | null;
};

type ExecutionLog = {
  id: string;
  step_id: number;
  system: string;
  tool_name: string;
  status: string;
  input_payload: Record<string, unknown> | null;
  output_payload: Record<string, unknown> | null;
  execution_time_ms: number | null;
  error: string | null;
  created_at: string;
};

type LogsResponse = {
  workflow_id: string;
  status?: string;
  logs: ExecutionLog[];
};

type KnowledgeDocument = {
  document_id: string;
  source_type: string;
  source_name: string;
  title: string;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

const DEFAULT_REQUEST =
  "Onboard a new client and alert the team after checking the customer record.";

function App() {
  const [request, setRequest] = useState(DEFAULT_REQUEST);
  const [workflow, setWorkflow] = useState<PlannerResponse | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState("IDLE");
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [executionResults, setExecutionResults] = useState<ExecutionResult[]>([]);
  const [selectedSource, setSelectedSource] =
    useState<KnowledgeDocument | null>(null);

  const [loadingPlan, setLoadingPlan] = useState(false);
  const [runningWorkflow, setRunningWorkflow] = useState(false);
  const [loadingSource, setLoadingSource] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const needsApproval = workflowStatus === "AWAITING_APPROVAL";

  const approvalRequired = useMemo(
    () => workflow?.plan.steps.some((step) => step.requires_approval) ?? false,
    [workflow],
  );

  async function parseResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let detail = `${response.status} ${response.statusText}`;

      try {
        const body = await response.json();
        detail = body.detail ?? JSON.stringify(body);
      } catch {
        // Keep HTTP status as fallback.
      }

      throw new Error(detail);
    }

    return response.json() as Promise<T>;
  }

  async function createPlan() {
    if (!request.trim()) {
      setError("Enter a business request first.");
      return;
    }

    setLoadingPlan(true);
    setError(null);
    setWorkflow(null);
    setLogs([]);
    setExecutionResults([]);
    setWorkflowStatus("PLANNING");

    try {
      const response = await fetch(`${API_BASE}/planner`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          request: request.trim(),
        }),
      });

      const data = await parseResponse<PlannerResponse>(response);

      setWorkflow(data);
      setWorkflowStatus(data.status);
    } catch (err) {
      setWorkflowStatus("FAILED");
      setError(err instanceof Error ? err.message : "Planning failed.");
    } finally {
      setLoadingPlan(false);
    }
  }

  async function runWorkflow() {
    if (!workflow) return;

    setRunningWorkflow(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/workflows/${workflow.workflow_id}/run`,
        {
          method: "POST",
        },
      );

      const data = await parseResponse<RunResponse>(response);

      setWorkflowStatus(data.status);

      if (data.execution_results) {
        setExecutionResults(data.execution_results);
      }

      if (data.status === "COMPLETED" || data.status === "FAILED") {
        await refreshLogs(workflow.workflow_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workflow run failed.");
    } finally {
      setRunningWorkflow(false);
    }
  }

  async function approveWorkflow() {
    if (!workflow) return;

    setRunningWorkflow(true);
    setError(null);
    setWorkflowStatus("APPROVED");

    try {
      const response = await fetch(
        `${API_BASE}/workflows/${workflow.workflow_id}/approve`,
        {
          method: "POST",
        },
      );

      const data = await parseResponse<RunResponse>(response);

      setWorkflowStatus(data.status);

      if (data.execution_results) {
        setExecutionResults(data.execution_results);
      }

      await refreshLogs(workflow.workflow_id);
    } catch (err) {
      setWorkflowStatus("FAILED");
      setError(err instanceof Error ? err.message : "Approval failed.");
    } finally {
      setRunningWorkflow(false);
    }
  }

  async function rejectWorkflow() {
    if (!workflow) return;

    setRunningWorkflow(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/workflows/${workflow.workflow_id}/reject`,
        {
          method: "POST",
        },
      );

      const data = await parseResponse<RunResponse>(response);

      setWorkflowStatus(data.status);
      await refreshLogs(workflow.workflow_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rejection failed.");
    } finally {
      setRunningWorkflow(false);
    }
  }

  async function refreshLogs(workflowId?: string) {
    const id = workflowId ?? workflow?.workflow_id;

    if (!id) return;

    try {
      const response = await fetch(`${API_BASE}/workflows/${id}/logs`);
      const data = await parseResponse<LogsResponse>(response);

      setLogs(data.logs);

      if (data.status) {
        setWorkflowStatus(data.status);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load logs.");
    }
  }

  async function openSource(documentId: string) {
    setLoadingSource(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/knowledge/${documentId}`);
      const data = await parseResponse<KnowledgeDocument>(response);

      setSelectedSource(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load knowledge document.",
      );
    } finally {
      setLoadingSource(false);
    }
  }

  function resetDemo() {
    setWorkflow(null);
    setWorkflowStatus("IDLE");
    setLogs([]);
    setExecutionResults([]);
    setError(null);
    setSelectedSource(null);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">AI</div>

          <div>
            <div className="brand-title">Enterprise Agent Platform</div>

            <div className="brand-subtitle">
              Governed multi-agent workflow orchestration
            </div>
          </div>
        </div>

        <div className="topbar-right">
          <div className="environment-dot" />
          <span>Development</span>

          <div
            className={`status-pill status-${workflowStatus.toLowerCase()}`}
          >
            {workflowStatus.replaceAll("_", " ")}
          </div>
        </div>
      </header>

      <main className="dashboard">
        <section className="hero">
          <div>
            <div className="eyebrow">ENTERPRISE AI ORCHESTRATION</div>

            <h1>
              Plan, approve, and execute
              <span> enterprise workflows.</span>
            </h1>

            <p>
              Grounded planning with pgvector retrieval, durable LangGraph
              orchestration, human approval, and auditable tool execution.
            </p>
          </div>

          <div className="hero-stats">
            <div className="stat">
              <strong>3</strong>
              <span>Connected systems</span>
            </div>

            <div className="stat">
              <strong>RAG</strong>
              <span>Grounded planning</span>
            </div>

            <div className="stat">
              <strong>HITL</strong>
              <span>Human approval</span>
            </div>
          </div>
        </section>

        {error && (
          <div className="error-banner">
            <strong>Request failed</strong>
            <span>{error}</span>
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        <section className="request-card panel">
          <div className="section-heading">
            <div>
              <span className="section-number">01</span>

              <div>
                <h2>Business request</h2>
                <p>Describe the outcome you want the agents to accomplish.</p>
              </div>
            </div>

            {workflow && (
              <button className="text-button" onClick={resetDemo}>
                New workflow
              </button>
            )}
          </div>

          <textarea
            value={request}
            onChange={(event) => setRequest(event.target.value)}
            placeholder="Describe an enterprise workflow..."
            disabled={loadingPlan || runningWorkflow}
          />

          <div className="request-footer">
            <div className="request-hints">
              <span>Salesforce</span>
              <span>SAP</span>
              <span>Slack</span>
            </div>

            <button
              className="primary-button"
              onClick={createPlan}
              disabled={loadingPlan || runningWorkflow}
            >
              {loadingPlan ? "Generating plan..." : "Generate grounded plan"}
            </button>
          </div>
        </section>

        {workflow && (
          <>
            <section className="panel">
              <div className="section-heading">
                <div>
                  <span className="section-number">02</span>

                  <div>
                    <h2>Grounded execution plan</h2>
                    <p>
                      Capabilities were selected from your enterprise knowledge
                      base.
                    </p>
                  </div>
                </div>

                <div className="workflow-id">
                  <span>Workflow</span>
                  <code>{workflow.workflow_id.slice(0, 8)}</code>
                </div>
              </div>

              <div className="plan-list">
                {workflow.plan.steps.map((step, index) => (
                  <article className="plan-step" key={step.step_id}>
                    <div className="step-track">
                      <div className="step-index">{step.step_id}</div>

                      {index < workflow.plan.steps.length - 1 && (
                        <div className="step-line" />
                      )}
                    </div>

                    <div className="step-content">
                      <div className="step-header">
                        <div>
                          <div className="system-name">{step.system}</div>
                          <h3>{step.action}</h3>
                        </div>

                        <div className="step-badges">
                          <span
                            className={`action-badge action-${step.action_type.toLowerCase()}`}
                          >
                            {step.action_type}
                          </span>

                          {step.requires_approval && (
                            <span className="approval-badge">
                              Approval required
                            </span>
                          )}
                        </div>
                      </div>

                      <p className="step-description">{step.description}</p>

                      {step.sources.length > 0 && (
                        <div className="sources">
                          {step.sources.map((source) => (
                            <button
                              className="source-chip"
                              key={source.document_id}
                              onClick={() => openSource(source.document_id)}
                              disabled={loadingSource}
                            >
                              <span className="source-icon">↗</span>

                              <span>
                                <strong>{source.title}</strong>

                                <small>
                                  {source.source_name} ·{" "}
                                  {(source.similarity * 100).toFixed(1)}% match
                                </small>
                              </span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </article>
                ))}
              </div>

              <div className="plan-footer">
                <div>
                  <strong>
                    {approvalRequired
                      ? "Human approval policy detected"
                      : "No manual approval required"}
                  </strong>

                  <span>
                    WRITE operations are held before enterprise execution.
                  </span>
                </div>

                {workflowStatus === "PENDING" && (
                  <button
                    className="primary-button"
                    onClick={runWorkflow}
                    disabled={runningWorkflow}
                  >
                    {runningWorkflow
                      ? "Starting workflow..."
                      : "Run workflow"}
                  </button>
                )}
              </div>
            </section>

            {needsApproval && (
              <section className="approval-panel">
                <div className="approval-icon">!</div>

                <div>
                  <div className="eyebrow">HUMAN-IN-THE-LOOP</div>

                  <h2>Execution paused for approval</h2>

                  <p>
                    This workflow contains a write operation. LangGraph has
                    checkpointed the workflow and will resume only after a
                    decision.
                  </p>
                </div>

                <div className="approval-actions">
                  <button
                    className="danger-button"
                    onClick={rejectWorkflow}
                    disabled={runningWorkflow}
                  >
                    Reject
                  </button>

                  <button
                    className="primary-button"
                    onClick={approveWorkflow}
                    disabled={runningWorkflow}
                  >
                    {runningWorkflow
                      ? "Executing..."
                      : "Approve & execute"}
                  </button>
                </div>
              </section>
            )}

            {(executionResults.length > 0 ||
              logs.length > 0 ||
              workflowStatus === "COMPLETED" ||
              workflowStatus === "REJECTED" ||
              workflowStatus === "FAILED") && (
              <section className="panel">
                <div className="section-heading">
                  <div>
                    <span className="section-number">03</span>

                    <div>
                      <h2>Execution timeline</h2>

                      <p>
                        Auditable enterprise tool calls and execution results.
                      </p>
                    </div>
                  </div>

                  <button
                    className="text-button"
                    onClick={() => refreshLogs()}
                  >
                    Refresh logs
                  </button>
                </div>

                {logs.length > 0 ? (
                  <div className="timeline">
                    {logs.map((log) => (
                      <div className="timeline-row" key={log.id}>
                        <div
                          className={`timeline-status ${
                            log.status === "SUCCESS" ? "success" : "failed"
                          }`}
                        >
                          {log.status === "SUCCESS" ? "✓" : "×"}
                        </div>

                        <div className="timeline-main">
                          <div>
                            <strong>{log.system}</strong>
                            <code>{log.tool_name}</code>
                          </div>

                          <span
                            className={
                              log.status === "SUCCESS"
                                ? "success-text"
                                : "failed-text"
                            }
                          >
                            {log.status}
                          </span>
                        </div>

                        <div className="timeline-latency">
                          {log.execution_time_ms !== null
                            ? `${log.execution_time_ms.toFixed(3)} ms`
                            : "—"}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : workflowStatus === "REJECTED" ? (
                  <div className="empty-state">
                    Workflow rejected. No enterprise tools were executed.
                  </div>
                ) : workflowStatus === "FAILED" ? (
                  <div className="empty-state">
                    Workflow execution failed. Review the backend audit logs.
                  </div>
                ) : (
                  <div className="empty-state">Loading execution logs...</div>
                )}

                <div className="completion-card">
                  <div>
                    <span>Workflow status</span>
                    <strong>{workflowStatus.replaceAll("_", " ")}</strong>
                  </div>

                  <div>
                    <span>Executed steps</span>
                    <strong>{logs.length}</strong>
                  </div>

                  <div>
                    <span>Validation</span>
                    <strong>
                      {workflowStatus === "COMPLETED"
                        ? "PASSED"
                        : workflowStatus === "FAILED"
                          ? "FAILED"
                          : "—"}
                    </strong>
                  </div>
                </div>
              </section>
            )}

            {executionResults.length > 0 && (
              <section className="panel">
                <div className="section-heading">
                  <div>
                    <span className="section-number">04</span>

                    <div>
                      <h2>Execution results</h2>

                      <p>
                        Outputs returned by the enterprise systems during
                        workflow execution.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="results-grid">
                  {executionResults.map((execution) => {
                    const result = execution.result;

                    return (
                      <article className="result-card" key={execution.step}>
                        <div className="result-card-header">
                          <div className="result-system">
                            <div className="result-check">✓</div>

                            <div>
                              <span>STEP {execution.step}</span>
                              <h3>{execution.system}</h3>
                            </div>
                          </div>

                          <span className="result-success">
                            {String(result.status ?? "success").toUpperCase()}
                          </span>
                        </div>

                        <div className="result-details">
                          {result.customer_id !== undefined && (
                            <div className="result-row">
                              <span>Customer ID</span>
                              <code>{String(result.customer_id)}</code>
                            </div>
                          )}

                          {result.sap_customer_id !== undefined && (
                            <div className="result-row">
                              <span>SAP Customer ID</span>
                              <code>{String(result.sap_customer_id)}</code>
                            </div>
                          )}

                          {result.verified !== undefined && (
                            <div className="result-row">
                              <span>Verified</span>

                              <strong>
                                {Boolean(result.verified) ? "Yes" : "No"}
                              </strong>
                            </div>
                          )}

                          {result.delivered !== undefined && (
                            <div className="result-row">
                              <span>Notification delivered</span>

                              <strong>
                                {Boolean(result.delivered) ? "Yes" : "No"}
                              </strong>
                            </div>
                          )}

                          <div className="result-row">
                            <span>System</span>

                            <strong>
                              {String(result.system ?? execution.system)}
                            </strong>
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </section>
            )}
          </>
        )}
    {workflow && (
  <section className="panel">
    <div className="section-heading">
      <div>
        <span className="section-number">05</span>

        <div>
          <h2>Agent trace</h2>
          <p>
            Decision evidence captured across retrieval, planning, approval,
            execution, and validation.
          </p>
        </div>
      </div>
    </div>

    <div className="trace-grid">
      <article className="trace-card">
        <div className="trace-card-top">
          <span className="trace-label">RETRIEVAL</span>
          <span className="trace-status trace-success">GROUNDED</span>
        </div>

        <h3>Enterprise capabilities retrieved</h3>

        <div className="trace-list">
          {workflow.plan.steps.flatMap((step) =>
            step.sources.map((source) => (
              <div
                className="trace-row"
                key={`${step.step_id}-${source.document_id}`}
              >
                <div>
                  <strong>{source.source_name}</strong>
                  <span>{source.title}</span>
                </div>

                <code>
                  {(source.similarity * 100).toFixed(1)}%
                </code>
              </div>
            )),
          )}
        </div>
      </article>

      <article className="trace-card">
        <div className="trace-card-top">
          <span className="trace-label">PLANNER</span>
          <span className="trace-status trace-success">VALID</span>
        </div>

        <h3>Grounded plan generated</h3>

        <div className="trace-metric">
          <strong>{workflow.plan.steps.length}</strong>
          <span>planned actions</span>
        </div>

        <div className="trace-list compact">
          {workflow.plan.steps.map((step) => (
            <div className="trace-row" key={step.step_id}>
              <div>
                <strong>
                  {step.system}.{step.action}
                </strong>
                <span>{step.action_type}</span>
              </div>

              <span>
                {step.requires_approval ? "Approval" : "Auto"}
              </span>
            </div>
          ))}
        </div>
      </article>

      <article className="trace-card">
        <div className="trace-card-top">
          <span className="trace-label">GOVERNANCE</span>

          <span
            className={`trace-status ${
              workflowStatus === "REJECTED"
                ? "trace-failed"
                : "trace-success"
            }`}
          >
            {workflowStatus === "REJECTED"
              ? "REJECTED"
              : approvalRequired
                ? "HITL"
                : "AUTO"}
          </span>
        </div>

        <h3>Human approval policy</h3>

        <div className="trace-metric">
          <strong>
            {approvalRequired ? "Required" : "Not required"}
          </strong>
          <span>for sensitive write operations</span>
        </div>

        <div className="trace-note">
          LangGraph pauses execution and persists a checkpoint before
          approved WRITE operations continue.
        </div>
      </article>

      <article className="trace-card">
        <div className="trace-card-top">
          <span className="trace-label">VALIDATION</span>

          <span
            className={`trace-status ${
              workflowStatus === "COMPLETED"
                ? "trace-success"
                : workflowStatus === "FAILED"
                  ? "trace-failed"
                  : "trace-neutral"
            }`}
          >
            {workflowStatus === "COMPLETED"
              ? "PASSED"
              : workflowStatus === "FAILED"
                ? "FAILED"
                : "PENDING"}
          </span>
        </div>

        <h3>Execution outcome</h3>

        <div className="trace-metric">
          <strong>{logs.length}</strong>
          <span>audited tool calls</span>
        </div>

        <div className="trace-list compact">
          <div className="trace-row">
            <div>
              <strong>Workflow</strong>
              <span>Final state</span>
            </div>

            <span>{workflowStatus.replaceAll("_", " ")}</span>
          </div>

          <div className="trace-row">
            <div>
              <strong>Validation</strong>
              <span>Deterministic result check</span>
            </div>

            <span>
              {workflowStatus === "COMPLETED"
                ? "PASSED"
                : workflowStatus === "FAILED"
                  ? "FAILED"
                  : "—"}
            </span>
          </div>
        </div>
      </article>
    </div>
  </section>
)}
        <section className="architecture-section">
  <div className="section-heading architecture-heading">
    <div>
      <span className="section-number">06</span>

      <div>
        <h2>How it works</h2>
        <p>
          A governed enterprise AI workflow from natural-language request to
          auditable execution.
        </p>
      </div>
    </div>
  </div>

  <div className="architecture-diagram">
    <div className="architecture-row architecture-row-top">
      <div className="architecture-node">
        <span className="architecture-step">01</span>
        <strong>User Request</strong>
        <small>
          Natural-language business request enters the platform.
        </small>
      </div>

      <div className="architecture-arrow">→</div>

      <div className="architecture-node">
        <span className="architecture-step">02</span>
        <strong>Semantic Retrieval</strong>
        <small>
          FastEmbed + pgvector retrieve relevant enterprise capabilities.
        </small>
      </div>

      <div className="architecture-arrow">→</div>

      <div className="architecture-node">
        <span className="architecture-step">03</span>
        <strong>Grounded Planner</strong>
        <small>
          The planner creates a source-attributed execution plan.
        </small>
      </div>

      <div className="architecture-arrow">→</div>

      <div className="architecture-node">
        <span className="architecture-step">04</span>
        <strong>LangGraph</strong>
        <small>
          Durable graph orchestration manages execution state and checkpoints.
        </small>
      </div>
    </div>

    <div className="architecture-turn">
      <span>↓</span>
    </div>

    <div className="architecture-row architecture-row-bottom">
      <div className="architecture-node">
        <span className="architecture-step">05</span>
        <strong>Human Approval</strong>
        <small>
          Sensitive write operations pause for explicit approval.
        </small>
      </div>

      <div className="architecture-arrow">→</div>

      <div className="architecture-node">
        <span className="architecture-step">06</span>
        <strong>Enterprise Tools</strong>
        <small>
          Salesforce, SAP, and Slack execute the approved workflow.
        </small>
      </div>

      <div className="architecture-arrow">→</div>

      <div className="architecture-node">
        <span className="architecture-step">07</span>
        <strong>Audit &amp; Validation</strong>
        <small>
          PostgreSQL stores execution logs, results, and validation status.
        </small>
      </div>
    </div>
  </div>

  <div className="architecture-tech">
    <span>React</span>
    <span>FastAPI</span>
    <span>FastEmbed</span>
    <span>pgvector</span>
    <span>PostgreSQL</span>
    <span>LangGraph</span>
    <span>Docker</span>
  </div>
</section>
      </main>

      {selectedSource && (
        <div
          className="modal-backdrop"
          onMouseDown={() => setSelectedSource(null)}
        >
          <div
            className="source-modal"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="modal-header">
              <div>
                <div className="eyebrow">RETRIEVED SOURCE</div>

                <h2>{selectedSource.title}</h2>
                <p>{selectedSource.source_name}</p>
              </div>

              <button
                className="close-button"
                onClick={() => setSelectedSource(null)}
              >
                ×
              </button>
            </div>

            <div className="source-metadata">
              <span>{selectedSource.source_type}</span>

              <span>
                Action: {String(selectedSource.metadata.action ?? "—")}
              </span>

              <span>
                Type: {String(selectedSource.metadata.action_type ?? "—")}
              </span>
            </div>

            <pre className="source-content">{selectedSource.content}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;