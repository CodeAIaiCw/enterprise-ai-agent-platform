from typing import Any, TypedDict


class WorkflowState(TypedDict):
    workflow_id: str

    execution_results: list[dict[str, Any]]

    validation_passed: bool

    status: str

    error: str | None