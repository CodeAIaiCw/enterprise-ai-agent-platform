from typing import Literal

from pydantic import BaseModel, Field


class PlanSource(BaseModel):
    document_id: str
    source_name: str
    title: str
    similarity: float


class PlanStep(BaseModel):
    step_id: int
    system: str
    action: str
    description: str
    action_type: Literal[
        "READ",
        "WRITE",
        "NOTIFY",
        "VALIDATE",
    ]
    requires_approval: bool
    sources: list[PlanSource] = Field(
        default_factory=list
    )


class ExecutionPlan(BaseModel):
    steps: list[PlanStep]