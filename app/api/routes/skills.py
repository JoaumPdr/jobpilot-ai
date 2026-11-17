"""Rotas de habilidades: catálogo e vínculo com o candidato.

POR QUÊ: rotas finas sobre `SkillService`; nenhuma consulta ou commit aqui.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status

from app.api.dependencies import SkillServiceDep
from app.schemas.skills import (
    CandidateSkillCreate,
    CandidateSkillRead,
    CandidateSkillUpdate,
    SkillCreate,
    SkillRead,
)

router = APIRouter(tags=["habilidades"])


@router.get(
    "/skills",
    response_model=list[SkillRead],
    summary="Lista o catálogo de habilidades",
)
def list_skills(
    service: SkillServiceDep,
    q: str | None = None,
) -> list[SkillRead]:
    """Lista o catálogo; `q` filtra o nome canônico sem diferenciar caixa."""
    return service.list_skills(q)


@router.post(
    "/skills",
    response_model=SkillRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma habilidade no catálogo",
)
def create_skill(
    payload: SkillCreate,
    service: SkillServiceDep,
) -> SkillRead:
    """Cria a habilidade; nome repetido (sem diferenciar caixa) retorna 409."""
    return service.create_skill(payload)


@router.get(
    "/candidates/{candidate_id}/skills",
    response_model=list[CandidateSkillRead],
    summary="Lista as habilidades do candidato",
)
def list_candidate_skills(
    candidate_id: uuid.UUID,
    service: SkillServiceDep,
) -> list[CandidateSkillRead]:
    """Lista os vínculos do candidato, com a habilidade canônica aninhada."""
    return service.list_candidate_skills(candidate_id)


@router.post(
    "/candidates/{candidate_id}/skills",
    response_model=CandidateSkillRead,
    status_code=status.HTTP_201_CREATED,
    summary="Vincula uma habilidade ao candidato",
)
def add_candidate_skill(
    candidate_id: uuid.UUID,
    payload: CandidateSkillCreate,
    service: SkillServiceDep,
) -> CandidateSkillRead:
    """Vincula por `skill_id` ou `canonical_name`; par repetido retorna 409."""
    return service.add_candidate_skill(candidate_id, payload)


@router.patch(
    "/candidates/{candidate_id}/skills/{skill_id}",
    response_model=CandidateSkillRead,
    summary="Atualiza o vínculo candidato/habilidade",
)
def update_candidate_skill(
    candidate_id: uuid.UUID,
    skill_id: uuid.UUID,
    payload: CandidateSkillUpdate,
    service: SkillServiceDep,
) -> CandidateSkillRead:
    """Atualiza nível, anos e evidência; `null` limpa o campo."""
    return service.update_candidate_skill(candidate_id, skill_id, payload)


@router.delete(
    "/candidates/{candidate_id}/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove o vínculo candidato/habilidade",
)
def remove_candidate_skill(
    candidate_id: uuid.UUID,
    skill_id: uuid.UUID,
    service: SkillServiceDep,
) -> Response:
    """Remove o vínculo sem apagar a habilidade do catálogo."""
    service.remove_candidate_skill(candidate_id, skill_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
