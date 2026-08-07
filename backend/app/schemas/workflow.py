from pydantic import BaseModel

from app.schemas.planner import ExecutionPlan


class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    plan: ExecutionPlan