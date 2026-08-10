import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    workflow_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflows.id"),
        nullable=False,
        index=True,
    )

    step_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    system: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    tool_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    input_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    output_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    execution_time_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )