import os
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app.core.database import SessionLocal
from app.graph.state import WorkflowState
from app.repositories.workflow_repository import WorkflowRepository
from app.services.execution_service import ExecutionService


CHECKPOINT_DB_URI = os.getenv(
    "CHECKPOINT_DB_URI",
    "postgresql://postgres:postgres@localhost:5432/enterprise_ai",
)

execution_service = ExecutionService()

_execution_graph = None
_checkpointer_context = None


async def approval_node(
    state: WorkflowState,
) -> dict:
    decision = interrupt(
        {
            "type": "approval_required",
            "workflow_id": state["workflow_id"],
            "message": "Approve execution of this enterprise workflow?",
        }
    )

    if decision is True:
        return {
            "status": "APPROVED",
            "error": None,
        }

    return {
        "status": "REJECTED",
        "error": "Workflow rejected by human reviewer",
    }


async def execution_node(
    state: WorkflowState,
) -> dict:
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


def route_after_approval(
    state: WorkflowState,
) -> str:
    if state["status"] == "REJECTED":
        return "end"

    return "execute"


def route_after_execution(
    state: WorkflowState,
) -> str:
    if state.get("error"):
        return "end"

    return "validate"


def build_graph_builder():
    graph = StateGraph(WorkflowState)

    graph.add_node(
        "approval",
        approval_node,
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
        "approval",
    )

    graph.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "execute": "execute",
            "end": END,
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

    return graph


async def get_execution_graph():
    global _execution_graph
    global _checkpointer_context

    if _execution_graph is None:
        _checkpointer_context = (
            AsyncPostgresSaver.from_conn_string(
                CHECKPOINT_DB_URI
            )
        )

        checkpointer = await _checkpointer_context.__aenter__()

        await checkpointer.setup()

        builder = build_graph_builder()

        _execution_graph = builder.compile(
            checkpointer=checkpointer
        )

    return _execution_graph