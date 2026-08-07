from fastapi import FastAPI
import structlog

from app.core.config import settings
from app.core.logging import configure_logging


configure_logging()

logger = structlog.get_logger()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)


@app.on_event("startup")
async def startup_event():
    logger.info(
        "application_started",
        environment=settings.environment,
        version=settings.app_version,
    )


@app.get("/api/v1/live")
async def live():
    logger.info("liveness_check")

    return {
        "status": "ok",
        "service": "enterprise-ai-agent",
        "environment": settings.environment,
    }