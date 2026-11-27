"""Rotas do perfil: candidato e preferências.

POR QUÊ: rotas finas apenas traduzem HTTP → serviço → resposta. Nenhum
`select`, nenhuma regra de negócio e nenhum `commit` aqui; a transação é do
serviço e os erros viram 404/409/422 pelos handlers globais.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status

from app.api.dependencies import ProfileServiceDep
from app.schemas.profile import (
    CandidateCreate,
    CandidateRead,
    CandidateUpdate,
    PreferencesPut,
    PreferencesRead,
)

router = APIRouter(tags=["perfil"])


@router.post(
    "/candidates",
    response_model=CandidateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um candidato",
)
def create_candidate(
    payload: CandidateCreate,
    service: ProfileServiceDep,
) -> CandidateRead:
    """Cria o candidato; e-mail repetido retorna 409."""
    return service.create_candidate(payload)


@router.get(
    "/candidates/{candidate_id}",
    response_model=CandidateRead,
    summary="Detalha o candidato",
)
def get_candidate(
    candidate_id: uuid.UUID,
    service: ProfileServiceDep,
) -> CandidateRead:
    """Retorna o candidato com preferências (quando existirem)."""
    return service.get_candidate(candidate_id)


@router.patch(
    "/candidates/{candidate_id}",
    response_model=CandidateRead,
    summary="Atualiza o candidato",
)
def update_candidate(
    candidate_id: uuid.UUID,
    payload: CandidateUpdate,
    service: ProfileServiceDep,
) -> CandidateRead:
    """Atualiza apenas os campos enviados."""
    return service.update_candidate(candidate_id, payload)


@router.delete(
    "/candidates/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove o candidato",
)
def delete_candidate(
    candidate_id: uuid.UUID,
    service: ProfileServiceDep,
) -> Response:
    """Remove o candidato e seus dependentes (CASCADE)."""
    service.delete_candidate(candidate_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/candidates/{candidate_id}/preferences",
    response_model=PreferencesRead,
    summary="Lê as preferências",
)
def get_preferences(
    candidate_id: uuid.UUID,
    service: ProfileServiceDep,
) -> PreferencesRead:
    """Retorna as preferências; 404 se o candidato ou a linha não existir."""
    return service.get_preferences(candidate_id)


@router.put(
    "/candidates/{candidate_id}/preferences",
    response_model=PreferencesRead,
    summary="Substitui as preferências",
)
def put_preferences(
    candidate_id: uuid.UUID,
    payload: PreferencesPut,
    service: ProfileServiceDep,
) -> PreferencesRead:
    """Substitui o conjunto inteiro de preferências (upsert idempotente)."""
    return service.put_preferences(candidate_id, payload)
