from app.schemas.planner import ExecutionPlan
from app.tools.registry import tool_registry


class ExecutionAgent:

    def get_tool(self, tool_name: str):
        return tool_registry.get(tool_name)

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

            tool = self.get_tool(tool_name)

            if tool is None:
                results.append(
                    {
                        "step": step.step_id,
                        "system": step.system,
                        "status": "tool_not_found",
                    }
                )
                continue

            result = await tool.execute(
                {
                    "description": step.description,
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