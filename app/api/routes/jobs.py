"""Rotas de vagas: cadastro manual.

POR QUÊ: rota fina sobre `JobService`; a normalização, a dedup e a transação
ficam no serviço. A listagem/filtros chegam na F1-T08 e a revisão de duplicatas
na F1-T07.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.dependencies import JobServiceDep
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
