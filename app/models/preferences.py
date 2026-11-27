"""Preferências de busca do candidato (1:1 com `candidates`).

POR QUÊ: separar as preferências do perfil mantém `candidates` estável e
permite atualizar critérios de busca sem reescrever o currículo. A relação é
1:1 garantida por `candidate_id` único.

Decisão de salário: `Numeric(12, 2)` sem coluna de moeda nesta fase
(ver `docs/tasks/FASE-01/F1-T01.md`).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate


class CandidatePreference(Base):
    """Critérios usados pelos futuros filtros de vaga (Fase 2)."""

    __tablename__ = "candidate_preferences"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )

    # Listas e regras em JSONB: a validação de estrutura é da camada de
    # serviço (F1-T02); aqui só garantimos JSON válido e default vazio.
    desired_titles: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    locations: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    work_modes: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    seniority_levels: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    min_salary: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    knockout_rules: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

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
        "Candidate", back_populates="preferences"
    )

    __table_args__ = (
        UniqueConstraint("candidate_id", name="uq_candidate_preferences_candidate_id"),
    )
