from typing import Any, TypedDict


class WorkflowState(TypedDict):
    workflow_id: str

    approved: bool
    blocked: bool

    execution_results: list[dict[str, Any]]

    validation_passed: bool

    status: str

    error: str | None