"""Execução local e sequencial do pipeline de um lote."""

from functools import partial

from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context

from app.orchestration.deterministic import (
    deduplicate_jobs,
    filter_jobs,
    import_jobs,
    normalize_jobs,
)
from app.orchestration.matching import analyze_jobs, match_jobs, select_jobs
from app.orchestration.state import PipelineState
from app.services.job_analysis import JobAnalysisService
from app.services.job_import import JobImportService
from app.services.jobs import JobService
from app.services.matching import MatchingService


def run_pipeline(
    state: PipelineState,
    *,
    content: bytes,
    importer: JobImportService,
    jobs: JobService,
    matching: MatchingService,
    analysis: JobAnalysisService | None = None,
    filename: str | None = None,
    source: str | None = None,
) -> PipelineState:
    """Executa um novo lote com os serviços da mesma execução."""
    if state.imported is not None:
        raise ValueError("Informe o estado inicial da execução.")
    if state.llm_enabled and analysis is None:
        raise ValueError("O modo LLM exige um serviço de análise.")

    graph = StateGraph(PipelineState)
    graph.add_node(
        "importar",
        partial(
            import_jobs,
            content=content,
            filename=filename,
            source=source,
            importer=importer,
            jobs=jobs,
        ),
    )
    graph.add_node("normalizar", normalize_jobs)
    graph.add_node("deduplicar", partial(deduplicate_jobs, jobs=jobs))
    graph.add_node("filtrar", partial(filter_jobs, jobs=jobs))
    graph.add_node("calcular", partial(match_jobs, matching=matching))
    graph.add_node("selecionar", select_jobs)
    graph.add_node("sem_analise", lambda state: {"analyzed_ids": ()})
    graph.add_edge(START, "importar")
    graph.add_edge("importar", "normalizar")
    graph.add_edge("normalizar", "deduplicar")
    graph.add_edge("deduplicar", "filtrar")
    graph.add_edge("filtrar", "calcular")
    graph.add_edge("calcular", "selecionar")
    if analysis is not None:
        graph.add_node("analisar", partial(analyze_jobs, analysis=analysis))
        graph.add_conditional_edges(
            "selecionar",
            lambda current: "analisar" if current.selected_ids else "sem_analise",
            ["analisar", "sem_analise"],
        )
        graph.add_edge("analisar", END)
    else:
        graph.add_edge("selecionar", "sem_analise")
    graph.add_edge("sem_analise", END)
    # O lote e os dados do candidato devem permanecer no processo local.
    with tracing_context(enabled=False):
        return PipelineState.model_validate(graph.compile().invoke(state))
