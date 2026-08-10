import time

from sqlalchemy.orm import Session

from app.agents.executor import ExecutionAgent
from app.models.workflow import Workflow
from app.repositories.execution_log_repository import ExecutionLogRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.planner import ExecutionPlan


class ExecutionService:
    def __init__(self) -> None:
        self.executor = ExecutionAgent()

    async def execute_workflow(
        self,
        db: Session,
        workflow: Workflow,
    ) -> list[dict]:

        if not workflow.plan:
            raise ValueError("Workflow has no execution plan")

        plan = ExecutionPlan.model_validate(workflow.plan)

        WorkflowRepository.update_status(
            db,
            workflow,
            "RUNNING",
        )

        results: list[dict] = []

        try:
            for step in plan.steps:
                start = time.perf_counter()

                tool_name = self._resolve_tool_name(
                    step.system,
                    step.action,
                )

                if tool_name is None:
                    duration_ms = (
                        time.perf_counter() - start
                    ) * 1000

                    ExecutionLogRepository.create(
                        db=db,
                        workflow_id=workflow.id,
                        step_id=step.step_id,
                        system=step.system,
                        tool_name="unsupported",
                        status="FAILED",
                        input_payload={
                            "description": step.description
                        },
                        execution_time_ms=duration_ms,
                        error="No matching tool registered",
                    )

                    raise ValueError(
                        f"No tool available for "
                        f"{step.system}.{step.action}"
                    )

                tool = self.executor.get_tool(tool_name)

                input_payload = {
                    "description": step.description
                }

                try:
                    result = await tool.execute(input_payload)

                    duration_ms = (
                        time.perf_counter() - start
                    ) * 1000

                    ExecutionLogRepository.create(
                        db=db,
                        workflow_id=workflow.id,
                        step_id=step.step_id,
                        system=step.system,
                        tool_name=tool_name,
                        status="SUCCESS",
                        input_payload=input_payload,
                        output_payload=result,
                        execution_time_ms=duration_ms,
                    )

                    results.append(
                        {
                            "step": step.step_id,
                            "system": step.system,
                            "result": result,
                        }
                    )

                except Exception as exc:
                    duration_ms = (
                        time.perf_counter() - start
                    ) * 1000

                    ExecutionLogRepository.create(
                        db=db,
                        workflow_id=workflow.id,
                        step_id=step.step_id,
                        system=step.system,
                        tool_name=tool_name,
                        status="FAILED",
                        input_payload=input_payload,
                        execution_time_ms=duration_ms,
                        error=str(exc),
                    )

                    raise

            WorkflowRepository.save_execution_results(
                db,
                workflow,
                results,
            )

            WorkflowRepository.update_status(
                db,
                workflow,
                "COMPLETED",
            )

            return results

        except Exception:
            WorkflowRepository.update_status(
                db,
                workflow,
                "FAILED",
            )
            raise

    @staticmethod
    def _resolve_tool_name(
        system: str,
        action: str,
    ) -> str | None:
        key = (
            system.lower(),
            action.lower(),
        )

        mapping = {
            ("salesforce", "create_customer"):
                "salesforce.create_customer",

            ("sap", "verify_customer"):
                "sap.verify_customer",

            ("slack", "send_notification"):
                "slack.send_notification",
        }

        return mapping.get(key)