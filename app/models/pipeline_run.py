"""Registro durável que permite ao pipeline reencontrar a próxima etapa."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PipelineRun(Base):
    """Uma linha por UUID fornecido pelo chamador, inclusive após uma retomada."""

    __tablename__ = "pipeline_runs"

    id: Mapped[UUID] = mapped_column("run_id", Uuid(), primary_key=True)
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    params: Mapped[dict[str, Any]] = mapped_column(JSONB)
    counters: Mapped[dict[str, int]] = mapped_column(JSONB)
    errors: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    state_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)

    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'failed', 'partial', 'completed')",
            name="ck_pipeline_runs_status",
        ),
    )
