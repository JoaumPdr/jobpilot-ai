"""Candidaturas vinculadas ao perfil e histórico de status.

POR QUÊ: o estado atual atende às consultas do dia a dia. O histórico
preserva as mudanças necessárias para explicar a trajetória da candidatura.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.job import Job


class ApplicationStatus(StrEnum):
    """Valores persistidos do fluxo de candidaturas do PLANO.md §5.1."""

    SALVA = "salva"
    PLANEJADA = "planejada"
    APLICADA = "aplicada"
    ENTREVISTA = "entrevista"
    OFERTA = "oferta"
    REJEITADA = "rejeitada"
    ENCERRADA = "encerrada"


_STATUS_VALUES = ", ".join(f"'{status.value}'" for status in ApplicationStatus)


class Application(Base):
    """Estado atual de uma candidatura para um par candidato e vaga."""

    __tablename__ = "applications"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    # A vaga pode ser arquivada. Sua exclusão física perderia a referência
    # que dá sentido à candidatura e ao histórico.
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("jobs.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=ApplicationStatus.SALVA.value
    )
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    candidate: Mapped[Candidate] = relationship("Candidate")
    job: Mapped[Job] = relationship("Job")
    status_history: Mapped[list[ApplicationStatusHistory]] = relationship(
        back_populates="application",
        cascade="all, delete",
        passive_deletes=True,
        order_by=lambda: (
            ApplicationStatusHistory.changed_at,
            ApplicationStatusHistory.id,
        ),
    )

    __table_args__ = (
        UniqueConstraint(
            "candidate_id", "job_id", name="uq_applications_candidate_job"
        ),
        CheckConstraint(f"status IN ({_STATUS_VALUES})", name="ck_applications_status"),
        Index("ix_applications_job_id", "job_id"),
    )


class ApplicationStatusHistory(Base):
    """Registro do status anterior e do novo status de uma candidatura."""

    __tablename__ = "application_status_history"

    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    # O registro inicial pode representar a criação, sem um status anterior.
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    application: Mapped[Application] = relationship(back_populates="status_history")

    __table_args__ = (
        CheckConstraint(
            f"from_status IN ({_STATUS_VALUES})",
            name="ck_application_status_history_from_status",
        ),
        CheckConstraint(
            f"to_status IN ({_STATUS_VALUES})",
            name="ck_application_status_history_to_status",
        ),
        Index(
            "ix_application_status_history_application_changed",
            "application_id",
            "changed_at",
        ),
    )
