"""Rotas locais de execução e consulta do pipeline de vagas."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Path, Query, UploadFile

from app.api.dependencies import get_pipeline_run_service
from app.schemas.jobs import JobListQuery
from app.schemas.pipeline_runs import PipelineRunRead
from app.services.job_import import MAX_CSV_BYTES
from app.services.pipeline_runs import PipelineRunService

router = APIRouter(prefix="/pipeline/runs", tags=["pipeline"])
PipelineServiceDep = Annotated[PipelineRunService, Depends(get_pipeline_run_service)]


@router.post("")
def execute_run(
    service: PipelineServiceDep,
    run_id: Annotated[
        UUID, Form(description="Repita o UUID para retomar a mesma entrada.")
    ],
    candidate_id: Annotated[UUID, Form()],
    file: Annotated[UploadFile, File(description="CSV em UTF-8, até 5 MB.")],
    filters: Annotated[JobListQuery, Query()],
    source: Annotated[str | None, Form(max_length=100)] = None,
    llm_enabled: Annotated[bool, Form()] = False,
) -> PipelineRunRead:
    """Processa o lote até o fim ou devolve o resultado persistido da mesma entrada."""
    return service.execute(
        run_id,
        candidate_id,
        content=file.file.read(MAX_CSV_BYTES + 1),
        filename=file.filename,
        source=source,
        filters=filters,
        llm_enabled=llm_enabled,
    )


@router.get("/{id}")
def get_run(
    run_id: Annotated[UUID, Path(alias="id")], service: PipelineServiceDep
) -> PipelineRunRead:
    """Devolve o último estado confirmado, os erros e as recomendações do lote."""
    return service.get(run_id)
