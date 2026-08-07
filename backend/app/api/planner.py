from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.planner import PlannerAgent
from app.schemas.planner import ExecutionPlan


router = APIRouter(
    prefix="/api/v1/planner",
    tags=["Planner"],
)

planner = PlannerAgent()


class PlannerRequest(BaseModel):
    request: str


@router.post("", response_model=ExecutionPlan)
async def create_plan(payload: PlannerRequest) -> ExecutionPlan:
    return await planner.plan(payload.request)