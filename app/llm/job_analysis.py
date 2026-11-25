"""Contrato da análise de vaga e vínculo com a versão do prompt."""

import json
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError

JOB_ANALYSIS_PROMPT_VERSION = "job-analysis-v1"
_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"

_NonEmptyText = Annotated[str, Field(min_length=1)]
_OUTPUT_CONFIG = ConfigDict(
    strict=True,
    extra="forbid",
    str_strip_whitespace=True,
    hide_input_in_errors=True,
)


class JobAnalysisEvidence(BaseModel):
    """Trecho atribuído a um requisito e à sua fonte."""

    model_config = _OUTPUT_CONFIG

    requirement: _NonEmptyText
    source: Literal["job", "profile"]
    quote: _NonEmptyText


class JobAnalysisOutput(BaseModel):
    """Estrutura esperada do provedor para a análise de uma vaga."""

    model_config = _OUTPUT_CONFIG

    job_id: UUID
    matched_skills: list[_NonEmptyText]
    missing_skills: list[_NonEmptyText]
    unknown_requirements: list[_NonEmptyText]
    recommendation: _NonEmptyText
    explanation: _NonEmptyText
    evidence: list[JobAnalysisEvidence]


@dataclass(frozen=True, slots=True)
class JobAnalysisPrompt:
    """Instruções de sistema e versão a usar para a mesma chamada."""

    version: str
    system_prompt: str


@dataclass(frozen=True, slots=True)
class VersionedJobAnalysis:
    """Saída estruturalmente válida associada ao prompt usado."""

    prompt_version: str
    analysis: JobAnalysisOutput = field(repr=False)


class JobAnalysisOutputError(ValueError):
    """Resposta inválida que pode ser diagnosticada sem expor dados."""


@cache
def load_job_analysis_prompt() -> JobAnalysisPrompt:
    """Carrega o prompt ativo e incorpora o contrato usado na validação."""
    path = _PROMPTS_DIR / f"{JOB_ANALYSIS_PROMPT_VERSION}.txt"
    instructions = path.read_text(encoding="utf-8").strip()
    schema = json.dumps(JobAnalysisOutput.model_json_schema(), ensure_ascii=False)
    return JobAnalysisPrompt(
        version=JOB_ANALYSIS_PROMPT_VERSION,
        system_prompt=f"{instructions}\n\n{schema}",
    )


def parse_job_analysis(
    response: str,
    *,
    expected_job_id: UUID,
    prompt: JobAnalysisPrompt,
) -> VersionedJobAnalysis:
    """Valida o JSON e registra a versão a partir do prompt carregado pela aplicação."""
    try:
        analysis = JobAnalysisOutput.model_validate_json(response)
    except ValidationError:
        # A validação do Pydantic pode conter trechos devolvidos pelo modelo.
        raise JobAnalysisOutputError(
            "Resposta fora do contrato de análise de vaga."
        ) from None

    if analysis.job_id != expected_job_id:
        raise JobAnalysisOutputError("A resposta pertence a outra vaga.")

    return VersionedJobAnalysis(prompt_version=prompt.version, analysis=analysis)
