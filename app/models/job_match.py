"""Resultado versionado de matching persistido para um candidato e uma vaga."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.job import Job


class JobMatch(Base):
    """Snapshot do score, das flags e das evidências de uma avaliação."""

    __tablename__ = "job_matches"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    scoring_version: Mapped[str] = mapped_column(String(80), nullable=False)
    # NUMERIC sem escala fixa preserva a precisão decimal do cálculo.
    deterministic_score: Mapped[Decimal | None] = mapped_column(Numeric)
    semantic_score: Mapped[Decimal | None] = mapped_column(Numeric)
    match_score: Mapped[Decimal | None] = mapped_column(Numeric)
    knockout_flags: Mapped[list[dict[str, str]]] = mapped_column(JSONB, nullable=False)
    analysis: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    llm_analysis: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    job: Mapped[Job] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "job_id",
            "scoring_version",
            name="uq_job_matches_candidate_job_version",
        ),
        Index(
            "ix_job_matches_ranking", "candidate_id", "scoring_version", "match_score"
        ),
        Index("ix_job_matches_job_id", "job_id"),
        CheckConstraint(
            "deterministic_score BETWEEN 0 AND 1 AND semantic_score BETWEEN 0 AND 1 "
            "AND match_score BETWEEN 0 AND 1",
            name="ck_job_matches_score_range",
        ),
    )
