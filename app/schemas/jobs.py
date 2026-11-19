"""Schemas do cadastro e da leitura de vagas.

POR QUÊ: a vaga entra pela API com texto livre ("home office", "Sênior") e
precisa sair com enums válidos e URL canônica. Validar aqui evita que o serviço
grave algo que o CHECK do banco rejeitaria e dá ao cliente um 422 claro antes de
qualquer consulta de deduplicação.

`work_mode` e `seniority` são strings livres de propósito: quem cadastra não
decorou os valores internos. A conversão para os enums do banco é feita pelas
funções puras da F1-T04 (`normalize_work_mode`/`normalize_seniority`).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models import Job
from app.models.job import Seniority, WorkMode
from app.services.normalization import canonicalize_url


class DuplicateLayer(StrEnum):
    """Camada da deduplicação que detectou a duplicata (`PLANO.md` §6.3)."""

    EXTERNAL_ID = "external_id"
    CANONICAL_URL = "canonical_url"
    FINGERPRINT = "fingerprint"


class JobCreate(BaseModel):
    """Payload do cadastro manual de uma vaga."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=300)
    company: str = Field(min_length=1, max_length=200)
    # Descrição é opcional: algumas fontes só publicam o link.
    description: str | None = None
    location: str | None = Field(default=None, max_length=200)
    # Texto livre; normalizado pelo serviço. `None`/vazio vira "desconhecido".
    work_mode: str | None = Field(default=None, max_length=50)
    seniority: str | None = Field(default=None, max_length=50)
    employment_type: str | None = Field(default=None, max_length=100)

    # Decimal (e não float) para não perder centavos no caminho até o NUMERIC.
    salary_min: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    salary_max: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    # ISO 4217: três letras, guardadas em maiúsculas ("brl" → "BRL").
    currency: str | None = Field(default=None, min_length=3, max_length=3)

    source: str = Field(default="manual", min_length=1, max_length=100)
    external_id: str | None = Field(default=None, max_length=200)

    url: str = Field(min_length=1)
    posted_at: datetime | None = None

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        """Rejeita cedo URLs que a canonização não conseguiria interpretar.

        `canonicalize_url` levanta `ValueError` para URL vazia, sem host ou com
        esquema não suportado (`ftp:` etc.). Traduzir para `ValueError` aqui faz
        o FastAPI responder `422 validation_error` em vez de 500.
        """
        try:
            canonicalize_url(value)
        except ValueError as exc:
            raise ValueError(f"URL inválida: {exc}") from exc
        return value

    @field_validator("currency")
    @classmethod
    def _normalize_currency(cls, value: str | None) -> str | None:
        """Valida o formato ISO 4217 e padroniza em maiúsculas."""
        if value is None:
            return None
        code = value.upper()
        if not code.isalpha():
            raise ValueError("Moeda deve ter três letras (ISO 4217, ex.: BRL).")
        return code

    @field_validator("posted_at")
    @classmethod
    def _normalize_posted_at(cls, value: datetime | None) -> datetime | None:
        """Converte para UTC; data sem fuso é tratada como UTC."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @field_validator("description")
    @classmethod
    def _strip_description(cls, value: str | None) -> str | None:
        """Apara as pontas sem colapsar parágrafos (descrição é texto longo)."""
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("external_id")
    @classmethod
    def _empty_external_id_is_none(cls, value: str | None) -> str | None:
        """Trata string vazia como ausência de identificador externo."""
        if value is None:
            return None
        return value or None

    @model_validator(mode="after")
    def _validate_salary_range(self) -> JobCreate:
        """Garante `salary_max >= salary_min` quando ambos existem."""
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError("salary_max não pode ser menor que salary_min.")
        return self


class JobRead(BaseModel):
    """Vaga persistida, no formato devolvido pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: str
    description: str | None
    location: str | None
    work_mode: str
    seniority: str
    employment_type: str | None
    salary_min: Decimal | None
    salary_max: Decimal | None
    currency: str | None
    source: str
    external_id: str | None
    url: str
    canonical_url: str
    fingerprint: str
    posted_at: datetime | None
    collected_at: datetime
    import_batch_id: uuid.UUID | None
    is_archived: bool
    duplicate_of_job_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class JobListQuery(BaseModel):
    """Filtros combinados por interseção e parâmetros de página."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    q: str | None = Field(default=None, min_length=1, max_length=300)
    work_mode: WorkMode | None = None
    location: str | None = Field(default=None, min_length=1, max_length=200)
    seniority: Seniority | None = None
    source: str | None = Field(default=None, min_length=1, max_length=100)
    posted_from: AwareDatetime | None = None
    posted_to: AwareDatetime | None = None
    include_archived: bool = False
    include_duplicates: bool = False
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=2**63 - 1)

    @model_validator(mode="after")
    def _validate_posted_range(self) -> JobListQuery:
        if (
            self.posted_from is not None
            and self.posted_to is not None
            and self.posted_from > self.posted_to
        ):
            raise ValueError("posted_from não pode ser posterior a posted_to.")
        return self


class JobPage(BaseModel):
    """Página do catálogo com indicação de que há mais itens no filtro atual."""

    items: list[JobRead]
    limit: int
    offset: int
    has_more: bool


class DuplicateWarning(BaseModel):
    """Vaga já existente que pode ser a mesma do cadastro atual."""

    job_id: uuid.UUID
    title: str
    company: str
    source: str
    canonical_url: str
    layer: DuplicateLayer

    @classmethod
    def from_job(cls, job: Job, layer: DuplicateLayer) -> DuplicateWarning:
        """Monta o aviso a partir do modelo, mantendo a conversão em um só lugar."""
        return cls(
            job_id=job.id,
            title=job.title,
            company=job.company,
            source=job.source,
            canonical_url=job.canonical_url,
            layer=layer,
        )


class JobCreateResult(BaseModel):
    """Resultado do cadastro: a vaga criada e as duplicatas prováveis."""

    job: JobRead
    # Vazio quando nada parecido foi encontrado; nunca bloqueia a criação.
    duplicates: list[DuplicateWarning] = Field(default_factory=list)
