from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.planner import ExecutionPlan
from app.schemas.workflow import WorkflowResponse


router = APIRouter(
    prefix="/api/v1/workflows",
    tags=["Workflows"],
)


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