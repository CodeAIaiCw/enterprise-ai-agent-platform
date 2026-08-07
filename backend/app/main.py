from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.api.planner import router as planner_router
from app.api.workflows import router as workflow_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import configure_logging
from app.models.workflow import Workflow  # noqa: F401

configure_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "application_starting",
        environment=settings.environment,
        version=settings.app_version,
    )

    Base.metadata.create_all(bind=engine)

    logger.info("database_initialized")

    yield

    logger.info("application_stopping")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(planner_router)
app.include_router(workflow_router)


@app.get("/api/v1/live")
async def live():
    logger.info("liveness_check")

    return {
        "status": "ok",
        "service": "enterprise-ai-agent",
        "environment": settings.environment,
    }