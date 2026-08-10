from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.execution_log import ExecutionLog


class ExecutionLogRepository:

    @staticmethod
    def create(
        db: Session,
        workflow_id: str,
        step_id: int,
        system: str,
        tool_name: str,
        status: str,
        input_payload: dict[str, Any] | None = None,
        output_payload: dict[str, Any] | None = None,
        execution_time_ms: float | None = None,
        error: str | None = None,
    ) -> ExecutionLog:
        log = ExecutionLog(
            workflow_id=workflow_id,
            step_id=step_id,
            system=system,
            tool_name=tool_name,
            status=status,
            input_payload=input_payload,
            output_payload=output_payload,
            execution_time_ms=execution_time_ms,
            error=error,
        )

        db.add(log)
        db.commit()
        db.refresh(log)

        return log

    @staticmethod
    def get_by_workflow(
        db: Session,
        workflow_id: str,
    ) -> list[ExecutionLog]:
        stmt = (
            select(ExecutionLog)
            .where(ExecutionLog.workflow_id == workflow_id)
            .order_by(ExecutionLog.step_id)
        )

        return list(db.scalars(stmt).all())