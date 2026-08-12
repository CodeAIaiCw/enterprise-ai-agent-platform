from typing import Any

from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.planner import (
    ExecutionPlan,
    PlanSource,
    PlanStep,
)


SYSTEM_PROMPT = """
You are an enterprise workflow planning agent.

Convert the user's business request into a safe, ordered execution plan.

You will receive a list of available enterprise capabilities retrieved
from enterprise documentation.

Rules:
- Only use capabilities supplied in the retrieved capability list.
- Do not invent systems, actions, tools, or API capabilities.
- Preserve logical execution order.
- Use lowercase snake_case action names.
- Classify actions as READ, WRITE, NOTIFY, or VALIDATE.
- WRITE actions require approval.
- Do not claim anything has already executed.
- Do not invent credentials, IDs, API responses, or results.
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

            self.structured_llm = (
                self.llm.with_structured_output(
                    ExecutionPlan
                )
            )

    async def plan(
        self,
        user_request: str,
    ) -> ExecutionPlan:
        return await self.plan_with_capabilities(
            user_request=user_request,
            capabilities=[],
        )

    async def plan_with_capabilities(
        self,
        user_request: str,
        capabilities: list[dict[str, Any]],
    ) -> ExecutionPlan:
        if self.mode == "mock":
            return self._mock_plan_from_capabilities(
                user_request=user_request,
                capabilities=capabilities,
            )

        if self.mode == "openai":
            capability_context = self._format_capabilities(
                capabilities
            )

            return await self.structured_llm.ainvoke(
                [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Business request:\n"
                            f"{user_request}\n\n"
                            f"Available capabilities:\n"
                            f"{capability_context}"
                        ),
                    },
                ]
            )

        raise ValueError(
            f"Unsupported planner mode: {self.mode}"
        )

    def _mock_plan_from_capabilities(
        self,
        user_request: str,
        capabilities: list[dict[str, Any]],
    ) -> ExecutionPlan:
        request = user_request.lower()

        steps: list[PlanStep] = []
        step_id = 1

        for capability in capabilities:
            system = str(
                capability.get("system", "")
            )
            action = str(
                capability.get("action", "")
            )
            action_type = str(
                capability.get("action_type", "READ")
            )
            description = str(
                capability.get("description", "")
            )
            requires_approval = bool(
                capability.get(
                    "requires_approval",
                    False,
                )
            )

            if not system or not action:
                continue

            if not self._capability_matches_request(
                request=request,
                system=system,
                action=action,
                description=description,
            ):
                continue

            source = PlanSource(
                document_id=str(
                    capability.get("document_id", "")
                ),
                source_name=str(
                    capability.get("source_name", system)
                ),
                title=str(
                    capability.get("title", "")
                ),
                similarity=float(
                    capability.get("similarity", 0.0)
                ),
            )

            steps.append(
                PlanStep(
                    step_id=step_id,
                    system=system,
                    action=action,
                    description=(
                        f"Execute retrieved capability "
                        f"{system}.{action}."
                    ),
                    action_type=action_type,
                    requires_approval=requires_approval,
                    sources=[source],
                )
            )

            step_id += 1

        if not steps:
            steps.append(
                PlanStep(
                    step_id=1,
                    system="Unknown",
                    action="clarify_request",
                    description=(
                        "No retrieved enterprise capability "
                        "matched the request."
                    ),
                    action_type="READ",
                    requires_approval=False,
                    sources=[],
                )
            )

        return ExecutionPlan(
            steps=self._order_steps(steps)
        )

    @staticmethod
    def _capability_matches_request(
        request: str,
        system: str,
        action: str,
        description: str,
    ) -> bool:
        searchable = (
            f"{system} {action} {description}"
        ).lower()

        request_terms = {
            term
            for term in request.replace(",", " ").split()
            if len(term) > 3
        }

        if not request_terms:
            return False

        return any(
            term in searchable
            for term in request_terms
        )

    @staticmethod
    def _order_steps(
        steps: list[PlanStep],
    ) -> list[PlanStep]:
        priority = {
            "WRITE": 1,
            "READ": 2,
            "VALIDATE": 3,
            "NOTIFY": 4,
        }

        ordered = sorted(
            steps,
            key=lambda step: priority.get(
                step.action_type,
                99,
            ),
        )

        return [
            step.model_copy(
                update={"step_id": index}
            )
            for index, step in enumerate(
                ordered,
                start=1,
            )
        ]

    @staticmethod
    def _format_capabilities(
        capabilities: list[dict[str, Any]],
    ) -> str:
        if not capabilities:
            return "No enterprise capabilities were retrieved."

        lines = []

        for index, capability in enumerate(
            capabilities,
            start=1,
        ):
            lines.append(
                "\n".join(
                    [
                        f"{index}. System: "
                        f"{capability.get('system')}",
                        f"   Action: "
                        f"{capability.get('action')}",
                        f"   Tool: "
                        f"{capability.get('tool_name')}",
                        f"   Type: "
                        f"{capability.get('action_type')}",
                        f"   Requires approval: "
                        f"{capability.get('requires_approval')}",
                        f"   Source: "
                        f"{capability.get('title')}",
                        f"   Similarity: "
                        f"{capability.get('similarity', 0):.4f}",
                    ]
                )
            )

        return "\n\n".join(lines)