from decimal import Decimal
from unittest.mock import Mock, call, create_autospec
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import TimeoutError as PoolTimeout

from app.core.errors import NotFoundError
from app.llm.providers import LLMProviderError
from app.models import JobMatch
from app.orchestration.graph import run_pipeline
from app.orchestration.state import PipelineState
from app.services.job_analysis import JobAnalysisService
from app.services.job_import import JobImportService
from app.services.jobs import JobService
from app.services.matching import MatchingService


def services(ids: tuple[UUID, ...]) -> tuple[Mock, Mock, Mock, Mock]:
    importer = create_autospec(JobImportService, instance=True)
    importer.import_csv.return_value.id = uuid4()
    jobs = create_autospec(JobService, instance=True)
    jobs.list_batch_ids.return_value = ids
    jobs.deduplicate_ids.return_value = ids
    jobs.filter_ids.return_value = ids
    matching = create_autospec(MatchingService, instance=True)
    matching.scoring_version = "teste-v1"
    return importer, jobs, matching, create_autospec(JobAnalysisService, instance=True)


def score(job_id: UUID) -> JobMatch:
    return JobMatch(job_id=job_id, deterministic_score=Decimal("0.90"))


def test_falhas_por_vaga_preservam_sucessos_e_limitam_tentativas() -> None:
    ids = tuple(UUID(int=i) for i in range(1, 6))
    importer, jobs, matching, analysis = services(ids)
    matching.calculate.side_effect = [
        PoolTimeout(),
        score(ids[0]),
        PoolTimeout(),
        PoolTimeout(),
        NotFoundError("texto privado"),
        score(ids[3]),
        score(ids[4]),
    ]
    analysis.analyze.side_effect = [None, LLMProviderError("texto privado"), None]
    state = PipelineState(run_id=uuid4(), candidate_id=uuid4(), llm_enabled=True)
    result = run_pipeline(
        state,
        content=b"csv",
        importer=importer,
        jobs=jobs,
        matching=matching,
        analysis=analysis,
    )
    assert result.selected_ids == (ids[0], ids[3], ids[4])
    assert result.analyzed_ids == (ids[0], ids[4])
    review = result.recommendations_for_review
    assert review is not None
    assert tuple(job.job_id for job in review) == (ids[0], ids[3], ids[4])
    assert [(e.job_id, e.stage, e.attempts, e.error_type) for e in result.errors] == [
        (ids[1], "matching", 2, "TimeoutError"),
        (ids[2], "matching", 1, "NotFoundError"),
        (ids[3], "analysis", 1, "LLMProviderError"),
    ]
    assert matching.calculate.call_args_list == [
        call(state.candidate_id, i) for i in (ids[0], ids[0], ids[1], ids[1], *ids[2:])
    ]
    assert matching.rollback.call_count == 3
    assert analysis.analyze.call_count == 3
    assert "texto privado" not in result.model_dump_json()
    assert PipelineState.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize("enabled,empty", [(False, False), (True, True)])
def test_finaliza_sem_analise_quando_selecao_vazia(enabled: bool, empty: bool) -> None:
    ids = () if empty else (uuid4(),)
    importer, jobs, matching, analysis = services(ids)
    matching.calculate.side_effect = [score(i) for i in ids]
    result = run_pipeline(
        PipelineState(run_id=uuid4(), candidate_id=uuid4(), llm_enabled=enabled),
        content=b"csv",
        importer=importer,
        jobs=jobs,
        matching=matching,
        analysis=analysis if enabled else None,
    )
    assert result.selected_ids == result.analyzed_ids == result.errors == ()
    assert result.matching is not None
    assert len(result.matching.jobs) == len(ids)
    analysis.analyze.assert_not_called()


def test_falha_do_lote_chega_ao_chamador() -> None:
    importer, jobs, matching, _ = services(())
    importer.import_csv.side_effect = ValueError("CSV inválido")
    with pytest.raises(ValueError, match="CSV inválido"):
        run_pipeline(
            PipelineState(run_id=uuid4(), candidate_id=uuid4()),
            content=b"",
            importer=importer,
            jobs=jobs,
            matching=matching,
        )
    jobs.filter_ids.assert_not_called()


@pytest.mark.parametrize("stage", ["matching", "analysis"])
def test_erro_de_programacao_chega_ao_chamador(stage: str) -> None:
    job_id = uuid4()
    importer, jobs, matching, analysis = services((job_id,))
    matching.calculate.return_value = score(job_id)
    broken_call = matching.calculate if stage == "matching" else analysis.analyze
    broken_call.side_effect = TypeError("contrato incompatível")
    with pytest.raises(TypeError, match="contrato incompatível"):
        run_pipeline(
            PipelineState(run_id=uuid4(), candidate_id=uuid4(), llm_enabled=True),
            content=b"csv",
            importer=importer,
            jobs=jobs,
            matching=matching,
            analysis=analysis,
        )
    broken_call.assert_called_once()
