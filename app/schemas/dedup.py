"""Schemas da revisão de duplicatas.

POR QUÊ: a revisão precisa de um retrato leve das vagas (id, título, empresa,
fonte, URL), do grupo que as aproximou e da nota de similaridade quando a
camada 4 foi a responsável. Reaproveitar `JobRead` traria descrição e
metadados de auditoria que não ajudam a decidir — e deixaria a listagem pesada.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DuplicateReviewLayer(StrEnum):
    """Camada que gerou o grupo na revisão (as camadas 1 e 2 bloqueiam na escrita)."""

    FINGERPRINT = "fingerprint"
    SIMILARITY = "similarity"


class JobDuplicateSummary(BaseModel):
    """Retrato mínimo de uma vaga dentro de um grupo de possíveis duplicatas."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: str
    location: str | None
    source: str
    canonical_url: str
    posted_at: datetime | None
    created_at: datetime
    # Já preenchido quando o usuário confirmou a duplicata (não aparece na lista).
    duplicate_of_job_id: uuid.UUID | None


class DuplicateGroupRead(BaseModel):
    """Conjunto de vagas que podem ser a mesma publicação."""

    layer: DuplicateReviewLayer
    # Nota da camada 4 (0–100); `null` quando o grupo veio do fingerprint.
    similarity: float | None
    # Vaga mais antiga do grupo: candidata natural a registro principal.
    canonical_job_id: uuid.UUID
    # Da mais antiga para a mais recente.
    jobs: list[JobDuplicateSummary]


class DuplicateGroupList(BaseModel):
    """Resultado da varredura, com o alcance real para não parecer completa."""

    groups: list[DuplicateGroupRead] = Field(default_factory=list)
    # Vagas efetivamente comparadas (não arquivadas e ainda não marcadas).
    scanned_jobs: int
    # `true` quando o catálogo passou do limite da varredura.
    truncated: bool


class DuplicateConfirm(BaseModel):
    """Corpo da confirmação: a vaga que deve continuar como principal."""

    model_config = ConfigDict(extra="forbid")

    duplicate_of_job_id: uuid.UUID
