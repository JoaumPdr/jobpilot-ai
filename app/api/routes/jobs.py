"""Rotas de vagas: listagem, cadastro, importação CSV e revisão de duplicatas.

POR QUÊ: as rotas são finas sobre os serviços; normalização, dedup, contadores e
transação ficam neles. A revisão (F1-T07) expõe apenas o que o usuário precisa:
ver os grupos suspeitos, confirmar a duplicata e desfazer a decisão.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, Query, Response, UploadFile, status

from app.api.dependencies import (
    ApplicationServiceDep,
    JobDedupServiceDep,
    JobImportServiceDep,
    JobServiceDep,
)
from app.schemas.applications import ApplicationCreate, ApplicationRead
from app.schemas.dedup import (
    DuplicateConfirm,
    DuplicateGroupList,
    DuplicateGroupRead,
    DuplicateReviewLayer,
    JobDuplicateSummary,
)
from app.schemas.imports import ImportBatchRead
from app.schemas.jobs import (
    DuplicateLayer,
    DuplicateWarning,
    JobCreate,
    JobCreateResult,
    JobListQuery,
    JobPage,
    JobRead,
)

router = APIRouter(tags=["vagas"])


@router.get(
    "/jobs",
    response_model=JobPage,
    summary="Lista vagas com filtros e paginação",
)
def list_jobs(
    query: Annotated[JobListQuery, Query()], service: JobServiceDep
) -> JobPage:
    """Retorna primeiro as vagas cadastradas mais recentemente."""
    jobs, has_more = service.list_jobs(query)
    return JobPage(
        items=[JobRead.model_validate(job) for job in jobs],
        limit=query.limit,
        offset=query.offset,
        has_more=has_more,
    )


@router.post(
    "/jobs",
    response_model=JobCreateResult,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra uma vaga manualmente",
)
def create_job(payload: JobCreate, service: JobServiceDep) -> JobCreateResult:
    """Cadastra a vaga normalizada; duplicata certa retorna 409 com detalhes.

    Duplicata provável (mesmo `fingerprint`) não bloqueia: a vaga é criada e o
    corpo traz `duplicates`, para o usuário decidir na revisão de duplicatas.
    """
    job, probable = service.create_manual(payload)
    return JobCreateResult(
        job=job,
        duplicates=[
            DuplicateWarning.from_job(other, DuplicateLayer.FINGERPRINT)
            for other in probable
        ],
    )


@router.post(
    "/jobs/import",
    response_model=ImportBatchRead,
    status_code=status.HTTP_201_CREATED,
    summary="Importa vagas de um arquivo CSV",
)
def import_jobs(
    service: JobImportServiceDep,
    file: Annotated[
        UploadFile,
        File(description="CSV em UTF-8, separado por vírgula, com cabeçalho."),
    ],
    source: Annotated[
        str | None,
        Form(description="Origem usada quando a linha não traz a coluna source."),
    ] = None,
) -> ImportBatchRead:
    """Importa o lote e devolve contadores e erros por linha.

    Linha inválida é rejeitada com motivo e número da linha, sem abortar o
    restante. Reimportar o mesmo arquivo não insere nada (dedup por
    identificador externo e URL canônica).
    """
    content = file.file.read()
    return service.import_csv(
        filename=file.filename,
        content=content,
        source=source,
    )


@router.get(
    "/jobs/duplicates",
    response_model=DuplicateGroupList,
    summary="Lista possíveis duplicatas para revisão",
)
def list_duplicate_jobs(
    service: JobDedupServiceDep,
    layer: Annotated[
        DuplicateReviewLayer | None,
        Query(description="Filtra pelo critério que aproximou as vagas."),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> DuplicateGroupList:
    """Agrupa duplicatas prováveis pelas camadas 3 (fingerprint) e 4 (título).

    Nada é alterado: confirmar é uma ação explícita. Vagas arquivadas ou já
    marcadas como duplicata não aparecem.
    """
    scan = service.list_groups(layer=layer, limit=limit)
    return DuplicateGroupList(
        groups=[
            DuplicateGroupRead(
                layer=group.layer,
                similarity=group.similarity,
                canonical_job_id=group.canonical_job_id,
                jobs=[JobDuplicateSummary.model_validate(job) for job in group.jobs],
            )
            for group in scan.groups
        ],
        scanned_jobs=scan.scanned_jobs,
        truncated=scan.truncated,
    )


@router.post(
    "/jobs/{job_id}/duplicate",
    response_model=JobRead,
    summary="Confirma uma vaga como duplicata de outra",
)
def confirm_duplicate_job(
    job_id: uuid.UUID,
    payload: DuplicateConfirm,
    service: JobDedupServiceDep,
) -> JobRead:
    """Grava a decisão humana em `duplicate_of_job_id`; nada é apagado."""
    return service.confirm_duplicate(job_id, payload.duplicate_of_job_id)


@router.delete(
    "/jobs/{job_id}/duplicate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desfaz a marcação de duplicata",
)
def undo_duplicate_job(job_id: uuid.UUID, service: JobDedupServiceDep) -> Response:
    """Devolve a vaga à revisão, limpando `duplicate_of_job_id`."""
    service.undo_duplicate(job_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/jobs/{job_id}/archive", summary="Arquiva uma vaga")
def archive_job(job_id: uuid.UUID, service: JobServiceDep) -> JobRead:
    return JobRead.model_validate(service.archive(job_id))


@router.post(
    "/candidates/{candidate_id}/jobs/{job_id}/save",
    status_code=status.HTTP_201_CREATED,
    summary="Salva uma vaga para um candidato",
)
def save_job(
    candidate_id: uuid.UUID, job_id: uuid.UUID, service: ApplicationServiceDep
) -> ApplicationRead:
    application = service.create(candidate_id, ApplicationCreate(job_id=job_id))
    return ApplicationRead.model_validate(application)
