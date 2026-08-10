from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.executor import ExecutionAgent
from app.api.dependencies import get_db
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.planner import ExecutionPlan


router = APIRouter(
    prefix="/api/v1/execute",
    tags=["Execution"],
)

executor = ExecutionAgent()


@router.post("/{workflow_id}")
async def execute_workflow(
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

    if not workflow.plan:
        raise HTTPException(
            status_code=400,
            detail="Workflow has no stored execution plan",
        )

    WorkflowRepository.update_status(
        db,
        workflow,
        "RUNNING",
    )

    try:
        plan = ExecutionPlan.model_validate(
            workflow.plan
        )

        results = await executor.execute(plan)

        WorkflowRepository.save_execution_results(
            db,
            workflow,
            results,
        )

        WorkflowRepository.update_status(
            db,
            workflow,
            "COMPLETED",
        )

        return {
            "workflow_id": workflow.id,
            "status": "COMPLETED",
            "results": results,
        }

    except Exception as exc:
        WorkflowRepository.update_status(
            db,
            workflow,
            "FAILED",
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )