"""Experiências profissionais do candidato.

POR QUÊ: manter o histórico separado permite calcular anos de experiência e
alimentar o matching sem reprocessar texto livre. `end_date` nulo representa
o vínculo atual; por isso o CHECK aceita NULL, mas garante que, quando
informada, a data de término não seja anterior à de início.

`years` fica aqui (anos naquela função) e também existe em `candidate_skills`
(anos usando a habilidade) — cada um com CHECK `>= 0` no banco.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate


class CandidateExperience(Base):
    """Um vínculo profissional do candidato."""

    __tablename__ = "candidate_experiences"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )

    company: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    # NULL = vínculo atual (sem data de término).
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_used: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    years: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    candidate: Mapped[Candidate] = relationship(
        "Candidate", back_populates="experiences"
    )

    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_candidate_experiences_date_range",
        ),
        CheckConstraint(
            "years IS NULL OR years >= 0",
            name="ck_candidate_experiences_years_non_negative",
        ),
    )
