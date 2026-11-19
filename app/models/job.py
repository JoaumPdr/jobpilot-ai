"""Vagas coletadas/importadas e lotes de importação.

POR QUÊ: a vaga é o insumo do matching e das candidaturas. Separar o catálogo
de vagas dos lotes de importação permite rastrear de onde cada vaga veio (CSV,
manual, API) sem repetir metadados do arquivo em cada linha, e mantém o
histórico de erros por linha mesmo quando parte do lote é rejeitada.

Os enums são `VARCHAR` + `CHECK` (como em `candidate_skills.level`) para evoluir
os valores sem `ALTER TYPE` no PostgreSQL. As funções que normalizam texto e
calculam `canonical_url`/`fingerprint` chegam na F1-T04.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.import_batch import ImportBatch


class WorkMode(StrEnum):
    """Modalidade de trabalho aceita em `jobs.work_mode`."""

    REMOTO = "remoto"
    HIBRIDO = "híbrido"
    PRESENCIAL = "presencial"
    DESCONHECIDO = "desconhecido"


class Seniority(StrEnum):
    """Senioridade aceita em `jobs.seniority` (desconhecida é o default)."""

    ESTAGIO = "estágio"
    JUNIOR = "júnior"
    PLENO = "pleno"
    SENIOR = "sênior"
    ESPECIALISTA = "especialista"
    DESCONHECIDO = "desconhecido"


class Job(Base):
    """Vaga normalizada; a dedup é sinalizada em `duplicate_of_job_id`."""

    __tablename__ = "jobs"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    # Descrição é opcional: algumas fontes só publicam o link.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # NOT NULL + default 'desconhecido': toda vaga tem uma modalidade legível,
    # mesmo antes da normalização automática da F1-T04.
    work_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'desconhecido'")
    )
    seniority: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'desconhecido'")
    )
    employment_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    # Código ISO 4217 (ex.: BRL, USD); sem conversão nesta fase.
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    # Origem: 'manual', nome do portal ou do arquivo. `external_id` só existe
    # em fontes que publicam um identificador estável.
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    url: Mapped[str] = mapped_column(Text, nullable=False)
    # URL sem parâmetros de rastreamento e normalizada (F1-T04).
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    # Hash de empresa + título + localização normalizados (camada 3 da dedup).
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)

    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    # Só preenchido quando o usuário confirma a duplicata (F1-T07). Nada é
    # apagado automaticamente; a vaga original continua sendo a referência.
    duplicate_of_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
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

    import_batch: Mapped[ImportBatch | None] = relationship(
        "ImportBatch", back_populates="jobs"
    )

    __table_args__ = (
        # Unicidade só quando há ID externo: CSV/manual sem ID não colidem.
        Index(
            "uq_jobs_source_external_id",
            "source",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
        Index("ix_jobs_fingerprint", "fingerprint"),
        Index("ix_jobs_canonical_url", "canonical_url"),
        CheckConstraint(
            "work_mode IN ('remoto', 'híbrido', 'presencial', 'desconhecido')",
            name="ck_jobs_work_mode",
        ),
        CheckConstraint(
            "seniority IN "
            "('estágio', 'júnior', 'pleno', 'sênior', 'especialista', 'desconhecido')",
            name="ck_jobs_seniority",
        ),
        CheckConstraint(
            "(salary_min IS NULL OR salary_min >= 0) "
            "AND (salary_max IS NULL OR salary_max >= 0)",
            name="ck_jobs_salary_non_negative",
        ),
        CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_max >= salary_min",
            name="ck_jobs_salary_range",
        ),
        CheckConstraint(
            "duplicate_of_job_id IS NULL OR duplicate_of_job_id <> id",
            name="ck_jobs_duplicate_not_self",
        ),
    )
