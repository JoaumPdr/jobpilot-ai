"""Habilidades: catálogo canônico (`skills`) e vínculo com o candidato.

POR QUÊ: separar o catálogo do vínculo evita repetir o nome da habilidade em
cada perfil e permite que a Fase 2 use a mesma taxonomia para as vagas.
`canonical_name` é único; `aliases` guarda sinônimos PT/EN em JSONB.

O `level` usa VARCHAR + CHECK (em vez de ENUM nativo) para permitir evoluir
os valores sem `ALTER TYPE`.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate


class Skill(Base):
    """Habilidade canônica compartilhada entre perfis e (futuramente) vagas."""

    __tablename__ = "skills"

    canonical_name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Texto livre nesta fase; a taxonomia com categorias fechadas é da F2-T01.
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aliases: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    candidate_skills: Mapped[list[CandidateSkill]] = relationship(
        "CandidateSkill", back_populates="skill", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("canonical_name", name="uq_skills_canonical_name"),
    )


class CandidateSkill(Base):
    """Habilidade declarada pelo candidato, com nível e evidência opcionais."""

    __tablename__ = "candidate_skills"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    # NULL = nível desconhecido/não informado; nunca significa "não possui".
    level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    candidate: Mapped[Candidate] = relationship("Candidate", back_populates="skills")
    skill: Mapped[Skill] = relationship("Skill", back_populates="candidate_skills")

    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "skill_id",
            name="uq_candidate_skills_candidate_skill",
        ),
        CheckConstraint(
            "level IS NULL OR level IN ('iniciante', 'intermediário', 'avançado')",
            name="ck_candidate_skills_level",
        ),
        CheckConstraint(
            "years IS NULL OR years >= 0",
            name="ck_candidate_skills_years_non_negative",
        ),
    )
