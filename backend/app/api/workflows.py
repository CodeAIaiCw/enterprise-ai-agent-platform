from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.graph.execution_graph import execution_graph
from app.repositories.execution_log_repository import ExecutionLogRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.planner import ExecutionPlan
from app.schemas.workflow import WorkflowResponse


router = APIRouter(
    prefix="/api/v1/workflows",
    tags=["Workflows"],
)


class RunWorkflowRequest(BaseModel):
    approved: bool = False


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
):
    workflow = WorkflowRepository.get(
        db,
        str(workflow_id),
    )

    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    plan = ExecutionPlan.model_validate(
        workflow.plan or {"steps": []}
    )

    return WorkflowResponse(
        workflow_id=workflow.id,
        status=workflow.status,
        plan=plan,
    )


@router.get("/{workflow_id}/logs")
async def get_workflow_logs(
    workflow_id: UUID,
    db: Session = Depends(get_db),
):
    workflow = WorkflowRepository.get(
        db,
        str(workflow_id),
    )

    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    logs = ExecutionLogRepository.get_by_workflow(
        db,
        str(workflow_id),
    )

    return {
        "workflow_id": str(workflow_id),
        "logs": [
            {
                "id": log.id,
                "step_id": log.step_id,
                "system": log.system,
                "tool_name": log.tool_name,
                "status": log.status,
                "input_payload": log.input_payload,
                "output_payload": log.output_payload,
                "execution_time_ms": log.execution_time_ms,
                "error": log.error,
                "created_at": log.created_at,
            }
            for log in logs
        ],
    }


@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: UUID,
    request: RunWorkflowRequest,
    db: Session = Depends(get_db),
):
    workflow = WorkflowRepository.get(
        db,
        str(workflow_id),
    )

    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    state = {
        "workflow_id": str(workflow_id),
        "approved": request.approved,
        "blocked": False,
        "execution_results": [],
        "validation_passed": False,
        "status": workflow.status,
        "error": None,
    }

    result = await execution_graph.ainvoke(state)

    return result