from decimal import Decimal
from unittest.mock import call, create_autospec
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.models import JobMatch
from app.orchestration.matching import analyze_jobs, match_jobs, select_jobs
from app.orchestration.state import (
    ImportedJobs,
    MatchingResult,
    PipelineState,
    ScoredJob,
)
from app.services.job_analysis import JobAnalysisService
from app.services.matching import MatchingService


def filtered(ids: tuple[UUID, ...], *, enabled: bool = True) -> PipelineState:
    return PipelineState(
        run_id=uuid4(),
        candidate_id=uuid4(),
        llm_enabled=enabled,
        imported=ImportedJobs(batch_id=uuid4(), job_ids=ids),
        normalized_ids=ids,
        deduplicated_ids=ids,
        filtered_ids=ids,
    )


def advance(state: PipelineState, **patch: object) -> PipelineState:
    return PipelineState.model_validate({**state.model_dump(), **patch})


@pytest.mark.parametrize("ids", [(), (uuid4(), uuid4())])
def test_matching_registra_versao_e_score_deterministico(ids: tuple[UUID, ...]) -> None:
    state = filtered(ids)
    service = create_autospec(MatchingService, instance=True)
    service.scoring_version = "teste-v2"
    scores = (None, Decimal("0.91"))[: len(ids)]
    service.calculate.side_effect = [
        JobMatch(job_id=job_id, deterministic_score=score, match_score=Decimal("0.99"))
        for job_id, score in zip(ids, scores, strict=True)
    ]
    result = match_jobs(state, matching=service)["matching"]
    assert service.calculate.call_args_list == [
        call(state.candidate_id, i) for i in ids
    ]
    assert result.scoring_version == "teste-v2"
    assert tuple((j.job_id, j.score) for j in result.jobs) == tuple(
        zip(ids, scores, strict=True)
    )


def test_selecao_respeita_limiar_orcamento_e_desempate() -> None:
    ids = tuple(UUID(int=i) for i in range(1, 15))
    scores = [None, Decimal("0.79999"), *([Decimal("0.80")] * 11), Decimal("0.95")]
    jobs = tuple(ScoredJob(job_id=i, score=s) for i, s in zip(ids, scores, strict=True))
    state = advance(
        filtered(ids), matching=MatchingResult(scoring_version="v1", jobs=jobs[::-1])
    )
    selected = select_jobs(state)["selected_ids"]
    assert selected == (ids[-1], *ids[2:11])
    # Um snapshot reconstruído também deve respeitar o corte quando há mais de dez elegíveis.
    with pytest.raises(ValidationError, match="top-10"):
        advance(state, selected_ids=[ids[11]])


@pytest.mark.parametrize("enabled", [True, False])
def test_analise_recebe_apenas_selecao_candidato_e_versao(enabled: bool) -> None:
    ids = (uuid4(), uuid4())
    state = advance(
        filtered(ids, enabled=enabled),
        matching=MatchingResult(
            scoring_version="teste-v2",
            jobs=(
                ScoredJob(job_id=ids[0], score=None),
                ScoredJob(job_id=ids[1], score=Decimal("0.80")),
            ),
        ),
    )
    selected = (ids[1],) if enabled else ()
    state = advance(state, **select_jobs(state))
    assert state.selected_ids == selected
    service = create_autospec(JobAnalysisService, instance=True)
    assert analyze_jobs(state, analysis=service) == {"analyzed_ids": selected}
    assert service.analyze.call_args_list == [
        call(state.candidate_id, i, "teste-v2") for i in selected
    ]


def test_etapas_pendentes_sao_rejeitadas() -> None:
    state = PipelineState(run_id=uuid4(), candidate_id=uuid4())
    with pytest.raises(ValueError, match="filtragem"):
        match_jobs(state, matching=create_autospec(MatchingService, instance=True))
    with pytest.raises(ValueError, match="matching"):
        select_jobs(state)
    with pytest.raises(ValueError, match="seleção"):
        analyze_jobs(state, analysis=create_autospec(JobAnalysisService, instance=True))
