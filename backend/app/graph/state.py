from typing import Any, TypedDict


class WorkflowState(TypedDict):
    workflow_id: str
    user_request: str

    plan: list[dict[str, Any]]
    current_step: int

    retrieved_context: list[dict[str, Any]]
    execution_results: list[dict[str, Any]]

    requires_approval: bool

    error: str | None
    final_summary: str | None