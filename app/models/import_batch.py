"""Lotes de importação de vagas.

POR QUÊ: cada importação (CSV, cadastro manual ou API futura) precisa de um
registro auditável com contadores e erros por linha. O lote não apaga vagas em
cascata: se o registro do lote for removido, as vagas ficam com
`import_batch_id = NULL` (`ON DELETE SET NULL`).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.job import Job


class ImportKind(StrEnum):
    """Origem do lote aceita em `import_batches.kind`."""

    CSV = "csv"
    MANUAL = "manual"
    API = "api"


class ImportBatch(Base):
    """Execução de importação com contadores e erros por linha."""

    __tablename__ = "import_batches"

    source: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # NULL enquanto o lote ainda está em andamento.
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Contadores do relatório por linha; nunca negativos.
    total_rows: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    inserted: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    duplicates: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    rejected: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    # Lista de erros por linha: [{row, field, message}, ...].
    errors: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    jobs: Mapped[list[Job]] = relationship("Job", back_populates="import_batch")

    __table_args__ = (
        CheckConstraint(
            "kind IN ('csv', 'manual', 'api')",
            name="ck_import_batches_kind",
        ),
        CheckConstraint(
            "total_rows >= 0 AND inserted >= 0 AND duplicates >= 0 AND rejected >= 0",
            name="ck_import_batches_counters_non_negative",
        ),
        CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at",
            name="ck_import_batches_finished_after_started",
        ),
    )
