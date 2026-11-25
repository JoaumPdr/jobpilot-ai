"""Nós de matching e análise do lote após a filtragem."""

from time import sleep
from typing import NotRequired, TypedDict
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.exc import (
    DataError,
    DBAPIError,
    IntegrityError,
    InterfaceError,
    OperationalError,
)
from sqlalchemy.exc import TimeoutError as PoolTimeout

from app.core.errors import DomainError
from app.llm.job_analysis import JobAnalysisOutputError
from app.llm.providers import LLMProviderError
from app.orchestration.state import ItemError, MatchingResult, PipelineState, ScoredJob
from app.services.job_analysis import JobAnalysisPersistenceError, JobAnalysisService
from app.services.llm_cache import LLMCacheError
from app.services.matching import MatchingService


class MatchUpdate(TypedDict):
    matching: MatchingResult
    errors: NotRequired[tuple[ItemError, ...]]


class AnalysisUpdate(TypedDict):
    analyzed_ids: tuple[UUID, ...]
    errors: NotRequired[tuple[ItemError, ...]]


def _transient(error: Exception) -> bool:
    if isinstance(error, DBAPIError):
        # PostgreSQL abortou a transação por serialização ou deadlock.
        return error.connection_invalidated or getattr(
            error.orig, "sqlstate", None
        ) in {"40001", "40P01"}
    return isinstance(error, PoolTimeout)


def match_jobs(state: PipelineState, *, matching: MatchingService) -> MatchUpdate:
    if state.filtered_ids is None:
        raise ValueError("O matching exige filtragem concluída.")
    scores = []
    errors = []
    for job_id in state.filtered_ids:
        for attempt in (1, 2):
            try:
                match = matching.calculate(state.candidate_id, job_id)
                scores.append(
                    ScoredJob(job_id=match.job_id, score=match.deterministic_score)
                )
            except (
                DomainError,
                ValidationError,
                DataError,
                IntegrityError,
                InterfaceError,
                OperationalError,
                PoolTimeout,
            ) as error:
                if isinstance(error, (DBAPIError, PoolTimeout)):
                    matching.rollback()
                if attempt == 1 and _transient(error):
                    sleep(0.25)
                    continue
                errors.append(
                    ItemError(
                        job_id=job_id,
                        stage="matching",
                        error_type=type(error).__name__,
                        attempts=attempt,
                    )
                )
            break
    update: MatchUpdate = {
        "matching": MatchingResult(
            scoring_version=matching.scoring_version, jobs=tuple(scores)
        )
    }
    if errors:
        update["errors"] = (*state.errors, *errors)
    return update


def select_jobs(state: PipelineState) -> dict[str, tuple[UUID, ...]]:
    if state.matching is None:
        raise ValueError("A seleção exige matching concluído.")
    return {"selected_ids": state.matching.top_job_ids() if state.llm_enabled else ()}


def analyze_jobs(
    state: PipelineState, *, analysis: JobAnalysisService
) -> AnalysisUpdate:
    if state.selected_ids is None or state.matching is None:
        raise ValueError("A análise exige seleção concluída.")
    analyzed = []
    errors = []
    for job_id in state.selected_ids:
        try:
            analysis.analyze(state.candidate_id, job_id, state.matching.scoring_version)
        except (
            DomainError,
            JobAnalysisOutputError,
            LLMProviderError,
            LLMCacheError,
            JobAnalysisPersistenceError,
        ) as error:
            # Provedor e serviço já limitam retry e reparo. Repetir o nó multiplicaria o orçamento.
            errors.append(
                ItemError(
                    job_id=job_id,
                    stage="analysis",
                    error_type=type(error).__name__,
                    attempts=1,
                )
            )
        else:
            analyzed.append(job_id)
    update: AnalysisUpdate = {"analyzed_ids": tuple(analyzed)}
    if errors:
        update["errors"] = (*state.errors, *errors)
    return update
