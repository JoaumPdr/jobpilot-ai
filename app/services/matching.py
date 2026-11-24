"""Calcula e consulta resultados de matching com as regras da Fase 2."""

import uuid
from collections.abc import Iterable

from sqlalchemy.exc import SQLAlchemyError

from app.core.errors import NotFoundError
from app.matching.job_requirements import RequirementType
from app.matching.knockouts import evaluate_knockouts
from app.matching.scoring import ScoreCalculator
from app.models import JobMatch
from app.repositories.matching import MatchRepository
from app.repositories.profile import CandidateRepository
from app.schemas.matching import (
    MatchAnalysis,
    MatchRankingPage,
    MatchRankingQuery,
    MatchRead,
)
from app.services.jobs import JobService
from app.services.skill_taxonomy import get_default_skill_taxonomy


class MatchingService:
    """Coordena o cálculo, o snapshot persistido e as consultas por candidato."""

    def __init__(
        self,
        matches: MatchRepository,
        candidates: CandidateRepository,
        jobs: JobService,
        calculator: ScoreCalculator,
    ) -> None:
        self._matches = matches
        self._candidates = candidates
        self._jobs = jobs
        self._calculator = calculator

    def calculate(
        self,
        candidate_id: uuid.UUID,
        job_id: uuid.UUID,
        *,
        confirmed_absent: Iterable[str] = (),
    ) -> JobMatch:
        """Calcula e grava a versão ativa. Levanta NotFoundError para entradas ausentes."""
        candidate = self._candidates.get(candidate_id)
        if candidate is None:
            raise NotFoundError("Candidato não encontrado.")
        job, requirements = self._jobs.get_matching_inputs(job_id)
        knockouts = evaluate_knockouts(
            job,
            candidate.preferences,
            taxonomy=get_default_skill_taxonomy(),
            required_skill_names=(
                item.skill.canonical_name
                for item in requirements
                if item.requirement_type == RequirementType.REQUIRED
            ),
        )
        result = self._calculator.score(
            requirements,
            (item.skill.canonical_name for item in candidate.skills),
            knockouts=knockouts,
            confirmed_absent=confirmed_absent,
        )
        match = JobMatch(
            candidate_id=candidate_id,
            job_id=job_id,
            scoring_version=result.scoring_version,
            deterministic_score=result.score,
            match_score=result.score,
            knockout_flags=[
                {"code": flag.code.value, "actual": flag.actual}
                for flag in result.knockouts.flags
            ],
            analysis=MatchAnalysis.from_score(result).model_dump(mode="json"),
        )
        try:
            stored = self._matches.upsert(match)
            self._matches.commit()
        except SQLAlchemyError:
            self._matches.rollback()
            raise
        return stored

    def detail(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID, version: str | None = None
    ) -> JobMatch:
        """Obtém a avaliação solicitada ou levanta NotFoundError."""
        match = self._matches.get(
            candidate_id, job_id, version or self._calculator.scoring_version
        )
        if match is None:
            raise NotFoundError("Resultado de matching não encontrado.")
        return match

    def ranking(
        self, candidate_id: uuid.UUID, query: MatchRankingQuery
    ) -> MatchRankingPage:
        """Obtém a página da versão escolhida. Candidato inexistente retorna 404."""
        if not self._candidates.exists(candidate_id):
            raise NotFoundError("Candidato não encontrado.")
        version = query.scoring_version or self._calculator.scoring_version
        matches = self._matches.list_page(candidate_id, version, query)
        return MatchRankingPage(
            items=[MatchRead.model_validate(item) for item in matches[: query.limit]],
            scoring_version=version,
            limit=query.limit,
            offset=query.offset,
            has_more=len(matches) > query.limit,
        )
