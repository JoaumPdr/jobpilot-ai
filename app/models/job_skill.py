"""Requisito extraído de uma vaga, com vínculo ao catálogo e evidência."""

import uuid

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.job import Job


class JobSkill(Base):
    """Evidência de uma habilidade no texto de uma vaga."""

    __tablename__ = "job_skills"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False
    )
    requirement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    weight: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(30), nullable=False)

    job: Mapped[Job] = relationship()

    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_job_skills_job_skill"),
        Index("ix_job_skills_skill_id", "skill_id"),
        CheckConstraint(
            "requirement_type IN ('obrigatorio', 'desejavel')",
            name="ck_job_skills_requirement_type",
        ),
        CheckConstraint("weight >= 0", name="ck_job_skills_weight_non_negative"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_job_skills_confidence"),
        CheckConstraint("btrim(evidence_snippet) <> ''", name="ck_job_skills_evidence"),
    )
