"""Rotas de cálculo, detalhe e ranking de matching por candidato."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import MatchingServiceDep
from app.schemas.matching import (
    MatchCalculate,
    MatchDetail,
    MatchRankingPage,
    MatchRankingQuery,
)

router = APIRouter(prefix="/candidates/{candidate_id}/matches", tags=["matching"])


@router.post("/{job_id}")
def calculate_match(
    candidate_id: uuid.UUID,
    job_id: uuid.UUID,
    service: MatchingServiceDep,
    payload: MatchCalculate | None = None,
) -> MatchDetail:
    """Calcula e persiste a versão ativa para o par candidato e vaga."""
    match = service.calculate(
        candidate_id,
        job_id,
        confirmed_absent=payload.confirmed_absent if payload else (),
    )
    return MatchDetail.model_validate(match)


@router.get("")
def list_matches(
    candidate_id: uuid.UUID,
    service: MatchingServiceDep,
    query: Annotated[MatchRankingQuery, Query()],
) -> MatchRankingPage:
    """Lista resultados já calculados pelos filtros de ranking."""
    return service.ranking(candidate_id, query)


@router.get("/{job_id}")
def get_match(
    candidate_id: uuid.UUID,
    job_id: uuid.UUID,
    service: MatchingServiceDep,
    scoring_version: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
) -> MatchDetail:
    """Retorna a avaliação persistida com os detalhes das evidências."""
    return MatchDetail.model_validate(
        service.detail(candidate_id, job_id, scoring_version)
    )
