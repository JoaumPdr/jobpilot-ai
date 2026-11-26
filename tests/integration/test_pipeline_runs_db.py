"""Reexecuções usam sessões reais e independentes no PostgreSQL isolado."""

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, func, inspect, select, text
from sqlalchemy.orm import Session, sessionmaker
from structlog.contextvars import get_contextvars

from app.core.errors import ConflictError
from app.models import Candidate, ImportBatch, Job, JobMatch, PipelineRun
from app.orchestration.persistence import run_persisted_pipeline
from app.orchestration.state import PipelineState
from app.services.jobs import JobService

CSV = b"title,company,description,url\nAnalista,Equipe,Vaga local,https://example.invalid/lote"


@pytest.fixture
def sessions(test_engine: Engine) -> Iterator[sessionmaker[Session]]:
    yield sessionmaker(test_engine)
    with test_engine.begin() as conn:
        conn.execute(
            text("TRUNCATE pipeline_runs, candidates, jobs, import_batches CASCADE")
        )


@pytest.fixture
def initial(sessions: sessionmaker[Session]) -> PipelineState:
    with sessions.begin() as db:
        candidate = Candidate(name="Teste", resume_text="Perfil sintético")
        db.add(candidate)
        db.flush()
        return PipelineState(run_id=uuid4(), candidate_id=candidate.id)


def test_queda_entre_commit_do_importador_e_snapshot(
    initial: PipelineState,
    sessions: sessionmaker[Session],
) -> None:
    with (
        patch.object(JobService, "list_batch_ids", side_effect=KeyboardInterrupt),
        pytest.raises(KeyboardInterrupt),
    ):
        run_persisted_pipeline(initial, content=CSV, sessions=sessions)
    with sessions() as db:
        row = db.get_one(PipelineRun, initial.run_id)
        assert row.status == "running"
        assert row.state_snapshot["imported"] is None
        assert db.scalar(select(func.count()).select_from(ImportBatch)) == 0
        assert db.scalar(select(func.count()).select_from(Job)) == 0
    result = run_persisted_pipeline(initial, content=CSV, sessions=sessions)
    assert result.imported and len(result.imported.job_ids) == 1


def test_retomada_preserva_lote_e_registra_so_tipo_do_erro(
    initial: PipelineState,
    sessions: sessionmaker[Session],
) -> None:
    def fail(*args: object) -> None:
        assert get_contextvars()["run_id"] == str(initial.run_id)
        raise RuntimeError("detalhe privado")

    with (
        patch.object(JobService, "filter_ids", fail),
        pytest.raises(RuntimeError, match="privado"),
    ):
        run_persisted_pipeline(initial, content=CSV, sessions=sessions)
    assert "run_id" not in get_contextvars()
    with sessions() as db:
        row = db.get_one(PipelineRun, initial.run_id)
        assert row.status == "failed" and row.finished_at is not None
        assert row.errors == [{"stage": "filtrar", "error_type": "RuntimeError"}]
        checkpoint = PipelineState.model_validate(row.state_snapshot)
        assert checkpoint.deduplicated_ids and checkpoint.filtered_ids is None
    with pytest.raises(ConflictError):
        run_persisted_pipeline(initial, content=CSV + b"\n", sessions=sessions)
    with patch.object(JobService, "list_batch_ids", side_effect=AssertionError):
        result = run_persisted_pipeline(initial, content=CSV, sessions=sessions)
    assert result.imported == checkpoint.imported
    assert result.matching and len(result.matching.jobs) == 1
    with sessions() as db:
        row = db.get_one(PipelineRun, initial.run_id)
        assert row.status == "completed" and row.errors == []
        assert row.counters["matched"] == 1
        assert row.finished_at and row.finished_at >= row.started_at
        assert PipelineState.model_validate(row.state_snapshot) == result


def test_chamadas_concorrentes_e_repeticao_devolvem_mesmo_resultado(
    initial: PipelineState,
    sessions: sessionmaker[Session],
) -> None:
    ready = Barrier(2)

    def invoke() -> PipelineState:
        ready.wait(timeout=10)
        return run_persisted_pipeline(initial, content=CSV, sessions=sessions)

    with ThreadPoolExecutor(max_workers=2) as pool:
        callers = [pool.submit(invoke) for _ in range(2)]
        first, second = [caller.result(timeout=20) for caller in callers]
    assert (
        first
        == second
        == run_persisted_pipeline(initial, content=CSV, sessions=sessions)
    )
    with sessions() as db:
        for model in (PipelineRun, ImportBatch, Job, JobMatch):
            assert db.scalar(select(func.count()).select_from(model)) == 1


def test_falha_por_vaga_e_terminal(sessions: sessionmaker[Session]) -> None:
    initial = PipelineState(run_id=uuid4(), candidate_id=uuid4())
    result = run_persisted_pipeline(initial, content=CSV, sessions=sessions)
    assert len(result.errors) == 1
    assert result == run_persisted_pipeline(initial, content=CSV, sessions=sessions)
    with sessions() as db:
        row = db.get_one(PipelineRun, initial.run_id)
        assert row.status == "partial"
        assert row.errors == [result.errors[0].model_dump(mode="json")]


def test_migracao_preserva_lotes_ao_reverter(test_engine: Engine) -> None:
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.set_main_option(
        "sqlalchemy.url",
        test_engine.url.render_as_string(hide_password=False).replace("%", "%%"),
    )
    try:
        command.downgrade(config, "000000000007")
        assert not inspect(test_engine).has_table("pipeline_runs")
        assert inspect(test_engine).has_table("import_batches")
    finally:
        command.upgrade(config, "head")
    assert inspect(test_engine).get_pk_constraint("pipeline_runs")[
        "constrained_columns"
    ] == ["run_id"]
