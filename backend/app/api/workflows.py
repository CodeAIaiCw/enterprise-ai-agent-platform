from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from langgraph.types import Command
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.graph.execution_graph import get_execution_graph
from app.repositories.execution_log_repository import ExecutionLogRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.planner import ExecutionPlan
from app.schemas.workflow import WorkflowResponse


router = APIRouter(
    prefix="/api/v1/workflows",
    tags=["Workflows"],
)


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
)
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
        "status": workflow.status,
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

    state = {
        "workflow_id": str(workflow_id),
        "execution_results": [],
        "validation_passed": False,
        "status": workflow.status,
        "error": None,
    }

    config = {
        "configurable": {
            "thread_id": str(workflow_id),
        }
    }

    execution_graph = await get_execution_graph()

    result = await execution_graph.ainvoke(
        state,
        config=config,
    )

    interrupts = result.get(
        "__interrupt__",
        (),
    )

    if interrupts:
        WorkflowRepository.update_status(
            db,
            workflow,
            "AWAITING_APPROVAL",
        )

        return {
            "workflow_id": str(workflow_id),
            "status": "AWAITING_APPROVAL",
            "interrupt": interrupts[0].value,
        }

    final_status = result.get(
        "status",
        workflow.status,
    )

    WorkflowRepository.update_status(
        db,
        workflow,
        final_status,
    )

    return result


@router.post("/{workflow_id}/approve")
async def approve_workflow(
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

    if workflow.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status_code=409,
            detail=(
                "Workflow is not awaiting approval. "
                f"Current status: {workflow.status}"
            ),
        )

    WorkflowRepository.update_status(
        db,
        workflow,
        "APPROVED",
    )

    config = {
        "configurable": {
            "thread_id": str(workflow_id),
        }
    }

    execution_graph = await get_execution_graph()

    try:
        result = await execution_graph.ainvoke(
            Command(resume=True),
            config=config,
        )

        final_status = result.get(
            "status",
            "COMPLETED",
        )

        WorkflowRepository.update_status(
            db,
            workflow,
            final_status,
        )

        return result

    except Exception as exc:
        WorkflowRepository.update_status(
            db,
            workflow,
            "FAILED",
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.post("/{workflow_id}/reject")
async def reject_workflow(
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

    if workflow.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status_code=409,
            detail=(
                "Workflow is not awaiting approval. "
                f"Current status: {workflow.status}"
            ),
        )

    config = {
        "configurable": {
            "thread_id": str(workflow_id),
        }
    }

    execution_graph = await get_execution_graph()

    result = await execution_graph.ainvoke(
        Command(resume=False),
        config=config,
    )

    WorkflowRepository.update_status(
        db,
        workflow,
        "REJECTED",
    )

    return {
        **result,
        "status": "REJECTED",
    }