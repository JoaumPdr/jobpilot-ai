"""Schemas do relatório de importação de vagas.

POR QUÊ: o lote precisa devolver contadores e erros por linha em um formato
estável — é o que o usuário lê para corrigir o CSV e reimportar. O schema lê
direto do modelo (`from_attributes`) porque não há transformação de negócio:
os números são calculados no serviço.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImportRowError(BaseModel):
    """Erro de uma linha do CSV, com o número da linha física do arquivo."""

    # Primeira linha de dados é a 2 (a 1 é o cabeçalho).
    row: int = Field(ge=1)
    # Coluna problemática; "file" para erros do arquivo inteiro.
    field: str
    message: str


class ImportBatchRead(BaseModel):
    """Resultado auditável de uma importação."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    kind: str
    filename: str | None
    started_at: datetime
    finished_at: datetime | None
    total_rows: int
    inserted: int
    duplicates: int
    rejected: int
    errors: list[ImportRowError]
