"""Nós de matching e análise do lote após a filtragem."""

from uuid import UUID

from app.orchestration.state import MatchingResult, PipelineState, ScoredJob
from app.services.job_analysis import JobAnalysisService
from app.services.matching import MatchingService


def match_jobs(
    state: PipelineState, *, matching: MatchingService
) -> dict[str, MatchingResult]:
    if state.filtered_ids is None:
        raise ValueError("O matching exige filtragem concluída.")
    scores = []
    for job_id in state.filtered_ids:
        match = matching.calculate(state.candidate_id, job_id)
        scores.append(ScoredJob(job_id=match.job_id, score=match.deterministic_score))
    return {
        "matching": MatchingResult(
            scoring_version=matching.scoring_version, jobs=tuple(scores)
        )
    }


def select_jobs(state: PipelineState) -> dict[str, tuple[UUID, ...]]:
    if state.matching is None:
        raise ValueError("A seleção exige matching concluído.")
    return {"selected_ids": state.matching.top_job_ids() if state.llm_enabled else ()}


def analyze_jobs(
    state: PipelineState, *, analysis: JobAnalysisService
) -> dict[str, tuple[UUID, ...]]:
    if state.selected_ids is None or state.matching is None:
        raise ValueError("A análise exige seleção concluída.")
    for job_id in state.selected_ids:
        analysis.analyze(state.candidate_id, job_id, state.matching.scoring_version)
    return {"analyzed_ids": state.selected_ids}
