"""Gera, valida e grava a análise LLM de um matching já calculado."""

import json
import re
from collections.abc import Iterable
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.errors import ConflictError, DomainError, InvalidDataError, NotFoundError
from app.core.logging import get_logger
from app.llm.job_analysis import (
    JobAnalysisEvidence,
    JobAnalysisOutput,
    JobAnalysisOutputError,
    VersionedJobAnalysis,
    load_job_analysis_repair_prompt,
    parse_job_analysis,
)
from app.llm.providers import LLMProviderError
from app.matching.skill_taxonomy import SkillTaxonomy, TaxonomySkill
from app.repositories.matching import MatchRepository
from app.schemas.matching import MatchAnalysis
from app.services.llm_cache import LLMCacheError, LLMCacheService
from app.services.llm_input import prepare_job_analysis_input
from app.services.normalization import comparison_text
from app.services.skill_taxonomy import get_default_skill_taxonomy

logger = get_logger(__name__)


class JobAnalysisPersistenceError(RuntimeError):
    """Falha no banco reportada sem parâmetros SQL ou texto de evidências."""


def _canonical_names(names: Iterable[str], taxonomy: SkillTaxonomy) -> list[str]:
    unique: dict[str, str] = {}
    for name in names:
        skill = taxonomy.lookup(name)
        canonical = skill.canonical_name if skill is not None else name
        unique.setdefault(comparison_text(canonical), canonical)
    return list(unique.values())


def _mentions_skill(text: str, skill: TaxonomySkill) -> bool:
    normalized = comparison_text(text)
    return any(
        re.search(
            rf"(?<![\w+#]){re.escape(comparison_text(term))}(?![\w+#])", normalized
        )
        for term in (skill.canonical_name, *skill.aliases)
    )


def _check_evidence(
    analysis: JobAnalysisOutput, matching: MatchAnalysis, user_prompt: str
) -> JobAnalysisOutput:
    # Compara com o conteúdo efetivamente enviado, inclusive após eventual truncamento.
    data = json.loads(user_prompt)
    description = data["job"]["description"]
    present = set(data["profile"]["skills"])
    absent = set(data["profile"]["confirmed_absent"])
    profile_names = present | absent
    taxonomy = get_default_skill_taxonomy()
    requirements: dict[str, list[str]] = {}
    for item in (*matching.met, *matching.absent, *matching.unconfirmed):
        skill = taxonomy.lookup(item.skill_name)
        if skill is not None:
            requirements.setdefault(skill.canonical_name, []).append(
                item.evidence_snippet
            )
    evidence: list[JobAnalysisEvidence] = []
    vacancy_evidence: set[str] = set()
    profile_evidence: set[str] = set()
    for item in analysis.evidence:
        skill = taxonomy.lookup(item.requirement)
        if skill is None or skill.canonical_name not in requirements:
            continue
        name = skill.canonical_name
        if item.source == "job":
            if (
                item.quote not in description
                or not any(item.quote in snippet for snippet in requirements[name])
                or not _mentions_skill(item.quote, skill)
            ):
                continue
            vacancy_evidence.add(name)
        else:
            if item.quote != name or name not in profile_names:
                continue
            profile_evidence.add(name)
        evidence.append(item.model_copy(update={"requirement": name}))

    matched = _canonical_names(analysis.matched_skills, taxonomy)
    missing = _canonical_names(analysis.missing_skills, taxonomy)
    unknown = _canonical_names(analysis.unknown_requirements, taxonomy)
    conflicting = (set(matched) & set(missing)) | (present & absent) | set(unknown)
    supported = (vacancy_evidence & profile_evidence) - conflicting
    matched_kept = [name for name in matched if name in supported and name in present]
    missing_kept = [name for name in missing if name in supported and name in absent]
    unknown = _canonical_names(
        [
            *unknown,
            *(name for name in matched if name not in matched_kept),
            *(name for name in missing if name not in missing_kept),
        ],
        taxonomy,
    )
    listed = set(matched_kept) | set(missing_kept) | set(unknown)
    # Resuma o que a aplicação conferiu. O texto livre pode repetir afirmações sem prova.
    return analysis.model_copy(
        update={
            "matched_skills": matched_kept,
            "missing_skills": missing_kept,
            "unknown_requirements": unknown,
            "evidence": [item for item in evidence if item.requirement in listed],
            "recommendation": "Revise os requisitos e as evidências antes de decidir.",
            "explanation": (
                f"Presença sustentada em {len(matched_kept)}, "
                f"ausência confirmada em {len(missing_kept)} e "
                f"{len(unknown)} requisitos sem confirmação."
            ),
        }
    )


class JobAnalysisService:
    """Persiste a análise validada no snapshot determinístico escolhido."""

    def __init__(self, matches: MatchRepository, cache: LLMCacheService) -> None:
        self._matches = matches
        self._cache = cache

    def analyze(
        self, candidate_id: UUID, job_id: UUID, scoring_version: str
    ) -> VersionedJobAnalysis:
        try:
            match = self._matches.get(candidate_id, job_id, scoring_version)
            if match is None:
                raise NotFoundError("Resultado de matching não encontrado.")
            matching = MatchAnalysis.model_validate(match.analysis)
            inputs = prepare_job_analysis_input(
                job_id=job_id, description=match.job.description, matching=matching
            )

            def validate(response: str) -> JobAnalysisOutput:
                parsed = parse_job_analysis(
                    response, expected_job_id=job_id, prompt=inputs.prompt
                )
                return _check_evidence(parsed.analysis, matching, inputs.user_prompt)

            result = self._cache.get_or_generate(
                inputs, validate=validate, repair=load_job_analysis_repair_prompt()
            )
            payload = {
                "prompt_version": result.prompt_version,
                "analysis": result.analysis.model_dump(mode="json"),
            }
            if not self._matches.save_llm_analysis(match, payload):
                raise ConflictError(
                    "O matching mudou durante a análise. Execute-a novamente."
                )
            self._matches.commit()
        except (
            DomainError,
            JobAnalysisOutputError,
            LLMProviderError,
            LLMCacheError,
            ValidationError,
            SQLAlchemyError,
        ) as error:
            self._matches.rollback()
            logger.warning(
                "llm_job_analysis_failed",
                job_id=str(job_id),
                error_type=type(error).__name__,
            )
            if isinstance(error, ValidationError):
                raise InvalidDataError(
                    "Snapshot de matching inválido para análise."
                ) from None
            if isinstance(error, SQLAlchemyError):
                raise JobAnalysisPersistenceError(
                    "Falha ao gravar a análise de vaga."
                ) from None
            raise
        return result
