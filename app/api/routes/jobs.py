"""Rotas de vagas: cadastro manual.

POR QUÊ: rota fina sobre `JobService`; a normalização, a dedup e a transação
ficam no serviço. A listagem/filtros chegam na F1-T08 e a revisão de duplicatas
na F1-T07.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from app.api.dependencies import JobImportServiceDep, JobServiceDep
from app.schemas.imports import ImportBatchRead
from app.schemas.jobs import (
    DuplicateLayer,
    DuplicateWarning,
    JobCreate,
    JobCreateResult,
)

router = APIRouter(tags=["vagas"])


@router.post(
    "/jobs",
    response_model=JobCreateResult,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra uma vaga manualmente",
)
def create_job(payload: JobCreate, service: JobServiceDep) -> JobCreateResult:
    """Cadastra a vaga normalizada; duplicata certa retorna 409 com detalhes.

    Duplicata provável (mesmo `fingerprint`) não bloqueia: a vaga é criada e o
    corpo traz `duplicates`, para o usuário decidir na revisão da F1-T07.
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
