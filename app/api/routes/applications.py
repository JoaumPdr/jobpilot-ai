"""Rotas de candidaturas de um candidato."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.dependencies import ApplicationServiceDep
from app.schemas.applications import (
    ApplicationCreate,
    ApplicationDetail,
    ApplicationRead,
    ApplicationUpdate,
)

router = APIRouter(
    prefix="/candidates/{candidate_id}/applications", tags=["candidaturas"]
)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_application(
    candidate_id: uuid.UUID, payload: ApplicationCreate, service: ApplicationServiceDep
) -> ApplicationRead:
    return ApplicationRead.model_validate(service.create(candidate_id, payload))


@router.get("")
def list_applications(
    candidate_id: uuid.UUID, service: ApplicationServiceDep
) -> list[ApplicationRead]:
    return [
        ApplicationRead.model_validate(application)
        for application in service.list_by_candidate(candidate_id)
    ]


@router.get("/{application_id}")
def get_application(
    candidate_id: uuid.UUID, application_id: uuid.UUID, service: ApplicationServiceDep
) -> ApplicationDetail:
    return ApplicationDetail.model_validate(
        service.get_detail(candidate_id, application_id)
    )


@router.patch("/{application_id}")
def update_application(
    candidate_id: uuid.UUID,
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    service: ApplicationServiceDep,
) -> ApplicationRead:
    return ApplicationRead.model_validate(
        service.update(candidate_id, application_id, payload)
    )
