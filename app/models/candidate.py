"""Modelo do candidato (perfil principal do JobPilot AI).

POR QUÊ: o candidato é a raiz do domínio — preferências, habilidades e
experiências pertencem a ele e são apagadas junto (ON DELETE CASCADE).
O e-mail é opcional, mas quando informado é normalizado e único sem
diferenciar maiúsculas de minúsculas (ver `_normalize_email` e o índice
funcional `uq_candidates_email_lower`).

Decisões de desenho: ver `docs/tasks/FASE-01/F1-T01.md` e `docs/data-model.md`.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.experience import CandidateExperience
    from app.models.preferences import CandidatePreference
    from app.models.skill import CandidateSkill


class Candidate(Base):
    """Pessoa dona do perfil; no MVP é single-user, mas o modelo já é multiusuário."""

    __tablename__ = "candidates"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    headline: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # JSONB porque a estrutura interna é validada por Pydantic na camada de
    # serviço (F1-T02); o banco só garante que o valor é JSON válido.
    education: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    languages: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    # Timestamps gerados pelo banco (TIMESTAMPTZ), não pelo relógio da aplicação.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    preferences: Mapped[CandidatePreference | None] = relationship(
        "CandidatePreference",
        back_populates="candidate",
        cascade="all, delete-orphan",
        uselist=False,
    )
    skills: Mapped[list[CandidateSkill]] = relationship(
        "CandidateSkill",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    experiences: Mapped[list[CandidateExperience]] = relationship(
        "CandidateExperience",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Índice único funcional: 'Joao@email.com' e 'joao@email.com' colidem.
        # Escolhido em vez de CITEXT para não exigir extensão no PostgreSQL.
        Index("uq_candidates_email_lower", text("lower(email)"), unique=True),
    )

    @validates("email")
    def _normalize_email(self, _key: str, value: str | None) -> str | None:
        """Normaliza o e-mail antes de gravar (trim + minúsculas).

        POR QUÊ: a unicidade do banco é sobre `lower(email)`; normalizar na
        escrita evita cadastros duplicados que só diferem por caixa/espaços.
        """
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None
