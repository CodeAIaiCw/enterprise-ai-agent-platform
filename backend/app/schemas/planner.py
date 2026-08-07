from typing import Literal

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    step_id: int = Field(..., description="Sequential step number")
    system: str = Field(..., description="Target enterprise system")
    action: str = Field(..., description="Machine-friendly action name")
    description: str = Field(..., description="Human-readable explanation")
    action_type: Literal["READ", "WRITE", "NOTIFY", "VALIDATE"]
    requires_approval: bool = False


class ExecutionPlan(BaseModel):
    steps: list[PlanStep]