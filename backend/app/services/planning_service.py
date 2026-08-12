from sqlalchemy.orm import Session

from app.agents.planner import PlannerAgent
from app.rag.retriever import knowledge_retriever
from app.schemas.planner import ExecutionPlan


class PlanningService:
    def __init__(self) -> None:
        self.planner = PlannerAgent()

    async def create_plan(
        self,
        db: Session,
        user_request: str,
    ) -> ExecutionPlan:
        retrieval_results = knowledge_retriever.semantic_search(
            db=db,
            query=user_request,
            limit=5,
        )

        capabilities = []

        for result in retrieval_results:
            metadata = result.document.metadata_json or {}

            capabilities.append(
                {
                    "system": metadata.get(
                        "system",
                        result.document.source_name,
                    ),
                    "action": metadata.get(
                        "action",
                        "",
                    ),
                    "tool_name": metadata.get(
                        "tool_name",
                        "",
                    ),
                    "action_type": metadata.get(
                        "action_type",
                        "READ",
                    ),
                    "requires_approval": metadata.get(
                        "requires_approval",
                        False,
                    ),
                    "description": result.document.content,
                    "similarity": result.similarity,
                }
            )

        return await self.planner.plan_with_capabilities(
            user_request=user_request,
            capabilities=capabilities,
        )


planning_service = PlanningService()