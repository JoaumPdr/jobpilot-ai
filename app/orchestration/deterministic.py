"""Nós do pipeline que usam o importador CSV e o catálogo de vagas."""

from uuid import UUID

from app.orchestration.state import ImportedJobs, PipelineState
from app.services.job_import import JobImportService
from app.services.jobs import JobService


def import_jobs(
    state: PipelineState,
    *,
    importer: JobImportService,
    jobs: JobService,
    content: bytes,
    filename: str | None = None,
    source: str | None = None,
) -> dict[str, ImportedJobs]:
    if state.imported is not None:
        return {"imported": state.imported}
    batch = importer.import_csv(content=content, filename=filename, source=source)
    return {
        "imported": ImportedJobs(
            batch_id=batch.id, job_ids=jobs.list_batch_ids(batch.id)
        )
    }


def normalize_jobs(state: PipelineState) -> dict[str, tuple[UUID, ...]]:
    if state.imported is None:
        raise ValueError("A normalização exige uma importação concluída.")
    # O importador só vincula ao lote vagas normalizadas por JobService.prepare_job.
    return {"normalized_ids": state.imported.job_ids}


def deduplicate_jobs(
    state: PipelineState, *, jobs: JobService
) -> dict[str, tuple[UUID, ...]]:
    if state.normalized_ids is None:
        raise ValueError("A deduplicação exige normalização concluída.")
    return {"deduplicated_ids": jobs.deduplicate_ids(state.normalized_ids)}


def filter_jobs(
    state: PipelineState, *, jobs: JobService
) -> dict[str, tuple[UUID, ...]]:
    if state.deduplicated_ids is None:
        raise ValueError("A filtragem exige deduplicação concluída.")
    return {"filtered_ids": jobs.filter_ids(state.deduplicated_ids, state.filters)}
