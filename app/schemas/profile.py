"""Schemas Pydantic do perfil (candidato e preferências).

POR QUÊ: o banco guarda `education`/`languages` em JSONB, mas JSONB só garante
JSON válido — não a forma. Estes schemas são a fronteira de validação: campos
desconhecidos são rejeitados (`extra="forbid"`), datas são datas de verdade e
listas são normalizadas antes de virar JSON.

Decisões registradas em `docs/tasks/FASE-01/F1-T02-a.md`:
- rotas REST por `candidate_id`;
- `education`/`languages` com estrutura detalhada;
- `knockout_rules` como objeto livre até a F2-T03.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

# Limite defensivo para itens de listas livres (títulos, locais, aliases).
_MAX_LIST_ITEM_LENGTH = 200


def _clean_string_list(value: list[str]) -> list[str]:
    """Remove espaços nas pontas e descarta itens vazios.

    POR QUÊ: listas de preferências chegam de UI/CSV; sem normalização,
    `[" Remoto ", ""]` viraria dois valores distintos no JSONB e quebraria
    filtros futuros.
    """
    cleaned: list[str] = []
    for item in value:
        text = item.strip()
        if not text:
            continue
        if len(text) > _MAX_LIST_ITEM_LENGTH:
            raise ValueError(
                f"Item de lista excede {_MAX_LIST_ITEM_LENGTH} caracteres."
            )
        cleaned.append(text)
    return cleaned


class LanguageLevel(StrEnum):
    """Níveis aceitos para idiomas (valores acentuados, como no domínio)."""

    BASICO = "básico"
    INTERMEDIARIO = "intermediário"
    AVANCADO = "avançado"
    FLUENTE = "fluente"
    NATIVO = "nativo"


class EducationEntry(BaseModel):
    """Uma formação acadêmica dentro do JSONB `candidates.education`."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    institution: str = Field(min_length=1, max_length=200)
    degree: str = Field(min_length=1, max_length=200)
    field_of_study: str | None = Field(default=None, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None

    @model_validator(mode="after")
    def _check_date_range(self) -> Self:
        """Garante que a formação não termine antes de começar."""
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date não pode ser anterior a start_date.")
        return self


class LanguageEntry(BaseModel):
    """Um idioma dentro do JSONB `candidates.languages`."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    level: LanguageLevel


class PreferencesBase(BaseModel):
    """Campos de preferência compartilhados entre entrada e saída."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    desired_titles: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    work_modes: list[str] = Field(default_factory=list)
    seniority_levels: list[str] = Field(default_factory=list)
    min_salary: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )
    # Regras de eliminação serão formalizadas na F2-T03; aqui só exigimos
    # um objeto JSON, sem inventar chaves que o domínio ainda não definiu.
    knockout_rules: dict[str, Any] = Field(default_factory=dict)

    @field_validator("desired_titles", "locations", "work_modes", "seniority_levels")
    @classmethod
    def _normalize_lists(cls, value: list[str]) -> list[str]:
        return _clean_string_list(value)


class PreferencesPut(PreferencesBase):
    """Substitui o conjunto inteiro de preferências (PUT idempotente)."""


class PreferencesRead(PreferencesBase):
    """Preferências persistidas, com identificadores e timestamps."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CandidateCreate(BaseModel):
    """Payload de criação do candidato."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None
    resume_text: str = Field(min_length=1)
    headline: str | None = Field(default=None, max_length=200)
    education: list[EducationEntry] = Field(default_factory=list)
    languages: list[LanguageEntry] = Field(default_factory=list)

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: object) -> object:
        """Normaliza o e-mail (trim + minúsculas) antes da validação.

        A unicidade no banco é sobre `lower(email)`; normalizar na entrada
        mantém a API coerente com o índice funcional.
        """
        if isinstance(value, str):
            normalized = value.strip().lower()
            return normalized or None
        return value


class CandidateUpdate(BaseModel):
    """Payload de `PATCH`; apenas os campos enviados são alterados."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    resume_text: str | None = Field(default=None, min_length=1)
    headline: str | None = Field(default=None, max_length=200)
    education: list[EducationEntry] | None = None
    languages: list[LanguageEntry] | None = None

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: object) -> object:
        """Mesma normalização da criação; `null` limpa o e-mail."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            return normalized or None
        return value

    @model_validator(mode="after")
    def _reject_explicit_null_in_required(self) -> Self:
        """`null` explícito em campo obrigatório é erro, não "não alterar"."""
        required = ("name", "resume_text", "education", "languages")
        for field in required:
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"O campo '{field}' não aceita null.")
        return self


class CandidateRead(BaseModel):
    """Representação de saída do candidato (com preferências, se houver)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str | None
    resume_text: str
    headline: str | None
    education: list[EducationEntry]
    languages: list[LanguageEntry]
    created_at: datetime
    updated_at: datetime
    preferences: PreferencesRead | None = None
