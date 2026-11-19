"""Schemas das experiências profissionais do candidato.

POR QUÊ: `end_date` nula representa o vínculo atual; validar a faixa aqui pega
o erro comum no `POST`, e o serviço revalida no `PATCH` combinando os valores
já gravados com os enviados. `years >= 0` espelha o CHECK do banco.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.common import clean_string_list


class ExperienceBase(BaseModel):
    """Campos compartilhados entre criação e leitura."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    start_date: date
    # NULL = vínculo atual (sem data de término).
    end_date: date | None = None
    description: str | None = None
    skills_used: list[str] = Field(default_factory=list)
    # Anos naquela função; distinto dos anos usando uma habilidade.
    years: int | None = Field(default=None, ge=0)

    @field_validator("skills_used")
    @classmethod
    def _normalize_skills_used(cls, value: list[str]) -> list[str]:
        return clean_string_list(value)

    @model_validator(mode="after")
    def _check_date_range(self) -> Self:
        """Garante que a experiência não termine antes de começar."""
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date não pode ser anterior a start_date.")
        return self


class ExperienceCreate(ExperienceBase):
    """Payload de criação de uma experiência."""


class ExperienceUpdate(BaseModel):
    """Payload de `PATCH`; apenas os campos enviados são alterados."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    company: str | None = Field(default=None, min_length=1, max_length=200)
    role: str | None = Field(default=None, min_length=1, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    skills_used: list[str] | None = None
    years: int | None = Field(default=None, ge=0)

    @field_validator("skills_used")
    @classmethod
    def _normalize_skills_used(cls, value: list[str] | None) -> list[str] | None:
        return None if value is None else clean_string_list(value)

    @model_validator(mode="after")
    def _reject_explicit_null_in_required(self) -> Self:
        """`null` explícito em campo obrigatório é erro, não "não alterar"."""
        required = ("company", "role", "start_date", "skills_used")
        for field in required:
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"O campo '{field}' não aceita null.")
        return self

    @model_validator(mode="after")
    def _check_date_range_when_both_present(self) -> Self:
        """Valida a faixa quando o payload traz as duas datas."""
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date não pode ser anterior a start_date.")
        return self


class ExperienceRead(ExperienceBase):
    """Experiência persistida, com identificadores e timestamps."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
