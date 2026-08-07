from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow import Workflow


class WorkflowRepository:

    @staticmethod
    def create(
        db: Session,
        user_request: str,
    ) -> Workflow:
        workflow = Workflow(
            user_request=user_request,
            status="PENDING",
        )

        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        return workflow

    @staticmethod
    def get(
        db: Session,
        workflow_id: str,
    ) -> Workflow | None:
        stmt = select(Workflow).where(
            Workflow.id == workflow_id
        )

        return db.scalar(stmt)

    @staticmethod
    def save_plan(
        db: Session,
        workflow: Workflow,
        plan: dict[str, Any],
    ) -> Workflow:
        workflow.plan = plan

        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        return workflow