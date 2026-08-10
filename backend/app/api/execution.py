from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.repositories.workflow_repository import WorkflowRepository
from app.services.execution_service import ExecutionService


router = APIRouter(
    prefix="/api/v1/execute",
    tags=["Execution"],
)

execution_service = ExecutionService()


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

    try:
        results = await execution_service.execute_workflow(
            db=db,
            workflow=workflow,
        )

        return {
            "workflow_id": workflow.id,
            "status": workflow.status,
            "results": results,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc