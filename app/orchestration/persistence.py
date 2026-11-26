"""Executa o grafo em transações retomáveis, identificadas por run_id."""

from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from structlog.contextvars import bound_contextvars

from app.core.database import SessionLocal
from app.core.errors import ConflictError
from app.core.logging import get_logger
from app.llm.providers import LLMProvider
from app.models import PipelineRun
from app.orchestration.graph import invoke_graph
from app.orchestration.state import PipelineState
from app.repositories.imports import ImportBatchRepository
from app.repositories.jobs import JobRepository
from app.repositories.matching import MatchRepository
from app.repositories.pipeline_runs import PipelineRunRepository
from app.repositories.profile import CandidateRepository
from app.services.job_analysis import JobAnalysisService
from app.services.job_import import JobImportService
from app.services.jobs import JobService
from app.services.llm_cache import LLMCacheService
from app.services.matching import MatchingService
from app.services.scoring import load_score_calculator

logger = get_logger(__name__)


def _pending_node(state: PipelineState) -> str | None:
    for name, output in (
        ("importar", state.imported),
        ("normalizar", state.normalized_ids),
        ("deduplicar", state.deduplicated_ids),
        ("filtrar", state.filtered_ids),
        ("calcular", state.matching),
        ("selecionar", state.selected_ids),
        ("analisar" if state.selected_ids else "sem_analise", state.analyzed_ids),
    ):
        if output is None:
            return name
    return None


def _save(run: PipelineRun, state: PipelineState) -> None:
    run.state_snapshot = state.model_dump(mode="json")
    run.errors = [error.model_dump(mode="json") for error in state.errors]
    run.counters = {
        "imported": len(state.imported.job_ids) if state.imported else 0,
        "normalized": len(state.normalized_ids or ()),
        "deduplicated": len(state.deduplicated_ids or ()),
        "filtered": len(state.filtered_ids or ()),
        "matched": len(state.matching.jobs) if state.matching else 0,
        "selected": len(state.selected_ids or ()),
        "analyzed": len(state.analyzed_ids or ()),
        "errors": len(state.errors),
    }
    if state.analyzed_ids is None:
        run.status, run.finished_at = "running", None
    else:
        run.status = "partial" if state.errors else "completed"
        run.finished_at = datetime.now(UTC)


def run_persisted_pipeline(
    initial: PipelineState,
    *,
    content: bytes,
    filename: str | None = None,
    source: str | None = None,
    provider: LLMProvider | None = None,
    sessions: sessionmaker[Session] = SessionLocal,
) -> PipelineState:
    """Inicia ou retoma o lote. A repetição exige a mesma entrada e o mesmo UUID.

    Conflitos de parâmetros levantam ConflictError. Falhas do lote chegam ao
    chamador após registrar a etapa. O CSV é fornecido novamente na retomada.
    """
    if initial.imported is not None:
        raise ValueError("Informe o estado inicial da execução.")
    if initial.llm_enabled and provider is None:
        raise ValueError("O modo LLM exige um provedor de análise.")

    calculator = load_score_calculator()
    cache = (
        LLMCacheService(provider, sessions=sessions)
        if initial.llm_enabled and provider
        else None
    )
    params: dict[str, Any] = initial.model_dump(
        mode="json", include={"candidate_id", "filters", "llm_enabled"}
    )
    params.update(
        csv_sha256=sha256(content).hexdigest(),
        filename=filename,
        source=source,
        scoring_version=calculator.scoring_version,
        llm=[provider.name, provider.model] if cache and provider else None,
    )
    with bound_contextvars(run_id=str(initial.run_id)):
        with sessions.begin() as db:
            PipelineRunRepository(db).reserve(
                initial.run_id, params, initial.model_dump(mode="json")
            )

        while True:
            with sessions.begin() as db:
                run = PipelineRunRepository(db).lock(initial.run_id)
                if run.params != params:
                    raise ConflictError("O run_id já pertence a outra entrada.")
                state = PipelineState.model_validate(run.state_snapshot)
                node = _pending_node(state)
                if node is None:
                    return state
                try:
                    # Os commits internos dos serviços liberam savepoints. Só a
                    # transação externa publica os efeitos junto com o snapshot.
                    with (
                        db.begin_nested(),
                        Session(
                            bind=db.connection(),
                            join_transaction_mode="create_savepoint",
                        ) as work,
                    ):
                        repo = JobRepository(work)
                        jobs = JobService(repo)
                        matches = MatchRepository(work)
                        state = invoke_graph(
                            state,
                            single_step=node,
                            content=content,
                            filename=filename,
                            source=source,
                            jobs=jobs,
                            importer=JobImportService(
                                jobs, repo, ImportBatchRepository(work)
                            ),
                            matching=MatchingService(
                                matches, CandidateRepository(work), jobs, calculator
                            ),
                            analysis=JobAnalysisService(matches, cache)
                            if cache
                            else None,
                        )
                        _save(run, state)
                except Exception as exc:
                    run.status, run.finished_at = "failed", datetime.now(UTC)
                    run.errors = [
                        *(e.model_dump(mode="json") for e in state.errors),
                        {"stage": node, "error_type": type(exc).__name__},
                    ]
                    run.counters = {**run.counters, "errors": len(run.errors)}
                    # A saída por exceção reverteria também o registro da falha.
                    db.commit()
                    logger.error(
                        "pipeline_node_failed",
                        stage=node,
                        error_type=type(exc).__name__,
                    )
                    raise
            logger.info("pipeline_node_completed", stage=node)
            if state.analyzed_ids is not None:
                return state
