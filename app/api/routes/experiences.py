"""Rotas de experiências profissionais.

POR QUÊ: rotas finas sobre `ExperienceService`; a validação de faixa de datas
que depende do estado atual fica no serviço.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status

from app.api.dependencies import ExperienceServiceDep
from app.schemas.experiences import (
    ExperienceCreate,
    ExperienceRead,
    ExperienceUpdate,
)

router = APIRouter(tags=["experiências"])


@router.get(
    "/candidates/{candidate_id}/experiences",
    response_model=list[ExperienceRead],
    summary="Lista as experiências do candidato",
)
def list_experiences(
    candidate_id: uuid.UUID,
    service: ExperienceServiceDep,
) -> list[ExperienceRead]:
    """Lista da mais recente para a mais antiga."""
    return service.list_experiences(candidate_id)


@router.post(
    "/candidates/{candidate_id}/experiences",
    response_model=ExperienceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma experiência",
)
def create_experience(
    candidate_id: uuid.UUID,
    payload: ExperienceCreate,
    service: ExperienceServiceDep,
) -> ExperienceRead:
    """Cria a experiência; `end_date` nula representa o vínculo atual."""
    return service.create_experience(candidate_id, payload)


@router.patch(
    "/candidates/{candidate_id}/experiences/{experience_id}",
    response_model=ExperienceRead,
    summary="Atualiza uma experiência",
)
def update_experience(
    candidate_id: uuid.UUID,
    experience_id: uuid.UUID,
    payload: ExperienceUpdate,
    service: ExperienceServiceDep,
) -> ExperienceRead:
    """Atualiza os campos enviados e revalida a faixa de datas."""
    return service.update_experience(candidate_id, experience_id, payload)


@router.delete(
    "/candidates/{candidate_id}/experiences/{experience_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma experiência",
)
def delete_experience(
    candidate_id: uuid.UUID,
    experience_id: uuid.UUID,
    service: ExperienceServiceDep,
) -> Response:
    """Remove a experiência do candidato."""
    service.delete_experience(candidate_id, experience_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
