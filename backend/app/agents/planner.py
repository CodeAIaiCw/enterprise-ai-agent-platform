from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.planner import ExecutionPlan, PlanStep


SYSTEM_PROMPT = """
You are an enterprise workflow planning agent.

Convert the user's business request into a safe, ordered execution plan.

Rules:
- Return only actions required to satisfy the request.
- Use lowercase snake_case action names.
- Classify each action as READ, WRITE, NOTIFY, or VALIDATE.
- WRITE actions should require human approval.
- Do not claim that actions have already executed.
- Do not invent credentials, customer IDs, API responses, or execution results.
- Preserve logical dependencies between workflow steps.
"""


class PlannerAgent:
    def __init__(self) -> None:
        self.mode = settings.planner_mode.lower()

        if self.mode == "openai":
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0,
            )

            self.structured_llm = self.llm.with_structured_output(
                ExecutionPlan
            )

    async def plan(self, user_request: str) -> ExecutionPlan:
        if self.mode == "mock":
            return self._mock_plan(user_request)

        if self.mode == "openai":
            return await self.structured_llm.ainvoke(
                [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": user_request,
                    },
                ]
            )

        raise ValueError(
            f"Unsupported planner mode: {self.mode}"
        )

    def _mock_plan(self, user_request: str) -> ExecutionPlan:
        request = user_request.lower()

        steps: list[PlanStep] = []
        step_id = 1

        if "salesforce" in request and (
            "create" in request or "customer" in request
        ):
            steps.append(
                PlanStep(
                    step_id=step_id,
                    system="Salesforce",
                    action="create_customer",
                    description="Create the customer record in Salesforce.",
                    action_type="WRITE",
                    requires_approval=True,
                )
            )
            step_id += 1

        if "sap" in request and (
            "verify" in request or "customer" in request
        ):
            steps.append(
                PlanStep(
                    step_id=step_id,
                    system="SAP",
                    action="verify_customer",
                    description="Verify the customer record in SAP.",
                    action_type="VALIDATE",
                    requires_approval=False,
                )
            )
            step_id += 1

        if "slack" in request or "notify" in request:
            steps.append(
                PlanStep(
                    step_id=step_id,
                    system="Slack",
                    action="send_notification",
                    description="Notify the relevant team in Slack.",
                    action_type="NOTIFY",
                    requires_approval=False,
                )
            )

        if not steps:
            steps.append(
                PlanStep(
                    step_id=1,
                    system="Unknown",
                    action="clarify_request",
                    description=(
                        "The request could not be mapped to a supported "
                        "enterprise workflow."
                    ),
                    action_type="READ",
                    requires_approval=False,
                )
            )

        return ExecutionPlan(steps=steps)