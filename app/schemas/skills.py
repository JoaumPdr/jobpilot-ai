"""Schemas do catálogo de habilidades e do vínculo candidato/skill.

POR QUÊ: o catálogo é compartilhado entre perfis (e, na Fase 2, entre vagas);
validar nome, aliases e nível aqui evita que a API grave valores que o CHECK do
banco rejeitaria depois. `level` usa os mesmos valores do CHECK
(`iniciante`, `intermediário`, `avançado`); `None` = desconhecido.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.common import clean_string_list


class SkillLevel(StrEnum):
    """Níveis aceitos para uma habilidade (valores acentuados)."""

    INICIANTE = "iniciante"
    INTERMEDIARIO = "intermediário"
    AVANCADO = "avançado"


class SkillCreate(BaseModel):
    """Payload de criação de uma habilidade canônica."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    canonical_name: str = Field(min_length=1, max_length=200)
    # Texto livre nesta fase; a taxonomia com categorias fechadas é da F2-T01.
    category: str | None = Field(default=None, max_length=100)
    aliases: list[str] = Field(default_factory=list)

    @field_validator("aliases")
    @classmethod
    def _normalize_aliases(cls, value: list[str]) -> list[str]:
        return clean_string_list(value)


class SkillRead(BaseModel):
    """Habilidade canônica persistida."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    canonical_name: str
    category: str | None
    aliases: list[str]


class CandidateSkillCreate(BaseModel):
    """Vincula uma habilidade ao candidato, por id ou por nome canônico."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    skill_id: uuid.UUID | None = None
    canonical_name: str | None = Field(default=None, min_length=1, max_length=200)
    level: SkillLevel | None = None
    years: int | None = Field(default=None, ge=0)
    evidence_note: str | None = None

    @model_validator(mode="after")
    def _require_exactly_one_reference(self) -> Self:
        """Exige exatamente um entre `skill_id` e `canonical_name`."""
        has_id = self.skill_id is not None
        has_name = self.canonical_name is not None
        if has_id == has_name:
            raise ValueError(
                "Informe exatamente um entre 'skill_id' e 'canonical_name'."
            )
        return self


class CandidateSkillUpdate(BaseModel):
    """Atualiza o vínculo; campos omitidos não mudam e `null` limpa."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    level: SkillLevel | None = None
    years: int | None = Field(default=None, ge=0)
    evidence_note: str | None = None


class CandidateSkillRead(BaseModel):
    """Vínculo persistido, com a habilidade canônica aninhada."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    skill_id: uuid.UUID
    skill: SkillRead
    level: SkillLevel | None
    years: int | None
    evidence_note: str | None
    created_at: datetime
