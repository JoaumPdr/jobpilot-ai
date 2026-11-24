"""Contratos do cálculo, ranking e detalhe de matching."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.matching.job_requirements import RequirementType
from app.matching.knockouts import KnockoutFlag
from app.matching.scoring import MatchLevel, RequirementAssessment, ScoreResult
from app.models import WorkMode
from app.schemas.common import clean_string_list


class MatchCalculate(BaseModel):
    """Ausências verificadas pelo chamador para este cálculo."""

    model_config = ConfigDict(extra="forbid")

    confirmed_absent: list[str] = Field(default_factory=list, max_length=500)

    @field_validator("confirmed_absent")
    @classmethod
    def _normalize_absences(cls, value: list[str]) -> list[str]:
        return clean_string_list(value)


class MatchRankingQuery(BaseModel):
    """Filtros combináveis para listar resultados de uma versão."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scoring_version: str | None = Field(default=None, min_length=1, max_length=80)
    min_score: Decimal | None = Field(default=None, ge=0, le=1)
    work_mode: WorkMode | None = None
    include_unscored: bool = False
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=2**63 - 1)


class MatchEvidence(BaseModel):
    """Evidência de um requisito na vaga e sua correspondência no perfil."""

    skill_name: str
    requirement_type: RequirementType
    confidence: float
    evidence_snippet: str
    level: MatchLevel
    weight: Decimal
    factor: Decimal | None
    candidate_skill: str | None

    @classmethod
    def from_assessment(cls, assessment: RequirementAssessment) -> "MatchEvidence":
        """Converte um requisito avaliado preservando a evidência original."""
        requirement = assessment.requirement
        return cls(
            skill_name=requirement.skill.canonical_name,
            requirement_type=requirement.requirement_type,
            confidence=requirement.confidence,
            evidence_snippet=requirement.evidence_snippet,
            level=assessment.level,
            weight=assessment.weight,
            factor=assessment.factor,
            candidate_skill=assessment.candidate_skill,
        )


class MatchAnalysis(BaseModel):
    """Explicação do resultado guardada no JSONB de cada avaliação."""

    weighted_sum: Decimal
    total_weight: Decimal
    met: list[MatchEvidence]
    absent: list[MatchEvidence]
    unconfirmed: list[MatchEvidence]

    @classmethod
    def from_score(cls, result: ScoreResult) -> "MatchAnalysis":
        """Prepara os grupos e termos da média para serialização."""
        return cls(
            weighted_sum=result.weighted_sum,
            total_weight=result.total_weight,
            met=[MatchEvidence.from_assessment(item) for item in result.met],
            absent=[MatchEvidence.from_assessment(item) for item in result.absent],
            unconfirmed=[
                MatchEvidence.from_assessment(item) for item in result.unconfirmed
            ],
        )


class MatchJobRead(BaseModel):
    """Campos da vaga necessários para identificar um item do ranking."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: str
    work_mode: WorkMode
    location: str | None


class MatchRead(BaseModel):
    """Identificação, pontuação e flags de um resultado persistido."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    job: MatchJobRead
    scoring_version: str
    deterministic_score: Decimal | None
    semantic_score: Decimal | None
    match_score: Decimal | None
    knockout_flags: list[KnockoutFlag]
    created_at: datetime
    updated_at: datetime


class MatchDetail(MatchRead):
    """Resultado com a explicação completa da avaliação."""

    analysis: MatchAnalysis


class MatchRankingPage(BaseModel):
    """Página ordenada dos resultados consultados."""

    items: list[MatchRead]
    scoring_version: str
    limit: int
    offset: int
    has_more: bool
