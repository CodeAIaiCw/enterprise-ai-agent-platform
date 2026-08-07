from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.planner import PlannerAgent
from app.api.dependencies import get_db
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.workflow import WorkflowResponse


router = APIRouter(
    prefix="/api/v1/planner",
    tags=["Planner"],
)

planner = PlannerAgent()


class PlannerRequest(BaseModel):
    request: str


@router.post("", response_model=WorkflowResponse)
async def create_plan(
    payload: PlannerRequest,
    db: Session = Depends(get_db),
):

    workflow = WorkflowRepository.create(
        db=db,
        user_request=payload.request,
    )

    plan = await planner.plan(payload.request)

    return WorkflowResponse(
        workflow_id=workflow.id,
        status=workflow.status,
        plan=plan,
    )