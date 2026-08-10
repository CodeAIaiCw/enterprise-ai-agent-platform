from langgraph.graph import END, START, StateGraph

from app.core.database import SessionLocal
from app.graph.state import WorkflowState
from app.repositories.workflow_repository import WorkflowRepository
from app.services.execution_service import ExecutionService


execution_service = ExecutionService()


async def security_node(
    state: WorkflowState,
) -> dict:
    """
    Prevent execution unless the workflow has been approved.
    """

    if not state["approved"]:
        return {
            "blocked": True,
            "status": "AWAITING_APPROVAL",
        }

    return {
        "blocked": False,
        "status": "APPROVED",
    }


async def execution_node(
    state: WorkflowState,
) -> dict:
    """
    Execute the persisted workflow using the existing ExecutionService.
    """

    db = SessionLocal()

    try:
        workflow = WorkflowRepository.get(
            db,
            state["workflow_id"],
        )

        if workflow is None:
            return {
                "status": "FAILED",
                "error": "Workflow not found",
                "execution_results": [],
            }

        results = await execution_service.execute_workflow(
            db=db,
            workflow=workflow,
        )

        return {
            "execution_results": results,
            "status": "EXECUTED",
            "error": None,
        }

    except Exception as exc:
        return {
            "status": "FAILED",
            "error": str(exc),
            "execution_results": [],
        }

    finally:
        db.close()


async def validation_node(
    state: WorkflowState,
) -> dict:
    """
    Deterministically validate that all executed tools succeeded.
    """

    if state.get("error"):
        return {
            "validation_passed": False,
            "status": "FAILED",
        }

    results = state.get(
        "execution_results",
        [],
    )

    if not results:
        return {
            "validation_passed": False,
            "status": "FAILED",
            "error": "No execution results were produced",
        }

    all_successful = all(
        item.get("result", {}).get("status") == "success"
        for item in results
    )

    return {
        "validation_passed": all_successful,
        "status": (
            "COMPLETED"
            if all_successful
            else "FAILED"
        ),
    }


def route_after_security(
    state: WorkflowState,
) -> str:
    if state["blocked"]:
        return "blocked"

    return "execute"


def route_after_execution(
    state: WorkflowState,
) -> str:
    if state.get("error"):
        return "end"

    return "validate"


def build_execution_graph():
    graph = StateGraph(WorkflowState)

    graph.add_node(
        "security",
        security_node,
    )

    graph.add_node(
        "execute",
        execution_node,
    )

    graph.add_node(
        "validate",
        validation_node,
    )

    graph.add_edge(
        START,
        "security",
    )

    graph.add_conditional_edges(
        "security",
        route_after_security,
        {
            "blocked": END,
            "execute": "execute",
        },
    )

    graph.add_conditional_edges(
        "execute",
        route_after_execution,
        {
            "validate": "validate",
            "end": END,
        },
    )

    graph.add_edge(
        "validate",
        END,
    )

    return graph.compile()


execution_graph = build_execution_graph()