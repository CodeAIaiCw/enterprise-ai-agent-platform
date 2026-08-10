from app.tools.registry import tool_registry
from app.schemas.planner import ExecutionPlan


class ExecutionAgent:

    async def execute(
        self,
        plan: ExecutionPlan,
    ) -> list[dict]:

        results = []

        for step in plan.steps:

            tool_name = None

            if step.system.lower() == "salesforce":
                tool_name = "salesforce.create_customer"

            elif step.system.lower() == "sap":
                tool_name = "sap.verify_customer"

            elif step.system.lower() == "slack":
                tool_name = "slack.send_notification"

            if tool_name is None:
                results.append(
                    {
                        "step": step.step_id,
                        "status": "unsupported",
                    }
                )
                continue

            tool = tool_registry.get(tool_name)

            result = await tool.execute(
                {
                    "description": step.description
                }
            )

            results.append(
                {
                    "step": step.step_id,
                    "system": step.system,
                    "result": result,
                }
            )

        return results