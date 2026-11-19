"""Máquina de estados e gravação de candidaturas com histórico."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, InvalidDataError, NotFoundError
from app.models.application import (
    Application,
    ApplicationStatus,
    ApplicationStatusHistory,
)
from app.repositories.applications import ApplicationRepository
from app.repositories.jobs import JobRepository
from app.repositories.profile import CandidateRepository
from app.schemas.applications import ApplicationCreate, ApplicationUpdate

_TERMINAIS = {ApplicationStatus.REJEITADA, ApplicationStatus.ENCERRADA}
_TRANSITIONS = {
    ApplicationStatus.SALVA: _TERMINAIS | {ApplicationStatus.PLANEJADA},
    ApplicationStatus.PLANEJADA: _TERMINAIS | {ApplicationStatus.APLICADA},
    ApplicationStatus.APLICADA: _TERMINAIS | {ApplicationStatus.ENTREVISTA},
    ApplicationStatus.ENTREVISTA: _TERMINAIS | {ApplicationStatus.OFERTA},
    ApplicationStatus.OFERTA: _TERMINAIS,
}


def validate_transition(current: ApplicationStatus, target: ApplicationStatus) -> None:
    """Valida uma mudança de estado conforme o PLANO.md §5.1."""
    if target not in _TRANSITIONS.get(current, set()):
        raise InvalidDataError(f"Transição de '{current}' para '{target}' inválida.")


class ApplicationService:
    def __init__(
        self,
        applications: ApplicationRepository,
        candidates: CandidateRepository,
        jobs: JobRepository,
    ) -> None:
        self._applications = applications
        self._candidates = candidates
        self._jobs = jobs

    def _require_candidate(self, candidate_id: uuid.UUID) -> None:
        if self._candidates.get(candidate_id) is None:
            raise NotFoundError("Candidato não encontrado.")

    def list_by_candidate(self, candidate_id: uuid.UUID) -> list[Application]:
        self._require_candidate(candidate_id)
        return self._applications.list_by_candidate(candidate_id)

    def get_detail(
        self, candidate_id: uuid.UUID, application_id: uuid.UUID
    ) -> Application:
        application = self._applications.get_detail(candidate_id, application_id)
        if application is None:
            raise NotFoundError("Candidatura não encontrada.")
        return application

    def create(self, candidate_id: uuid.UUID, data: ApplicationCreate) -> Application:
        self._require_candidate(candidate_id)
        if self._jobs.get(data.job_id) is None:
            raise NotFoundError("Vaga não encontrada.")
        application = Application(
            candidate_id=candidate_id,
            job_id=data.job_id,
            status=ApplicationStatus.SALVA,
            notes=data.notes,
            status_history=[
                ApplicationStatusHistory(to_status=ApplicationStatus.SALVA)
            ],
        )
        self._applications.add(application)
        try:
            self._applications.commit()
        except IntegrityError as exc:
            self._applications.rollback()
            constraint = getattr(
                getattr(exc.orig, "diag", None), "constraint_name", None
            )
            if constraint == "uq_applications_candidate_job":
                raise ConflictError(
                    "Já existe uma candidatura para esta vaga e candidato."
                ) from exc
            if constraint == "applications_candidate_id_fkey":
                raise NotFoundError("Candidato não encontrado.") from exc
            if constraint == "applications_job_id_fkey":
                raise NotFoundError("Vaga não encontrada.") from exc
            raise
        return application

    def update(
        self,
        candidate_id: uuid.UUID,
        application_id: uuid.UUID,
        data: ApplicationUpdate,
    ) -> Application:
        application = self._applications.get(candidate_id, application_id, lock=True)
        if application is None:
            raise NotFoundError("Candidatura não encontrada.")
        if "status" in data.model_fields_set and data.status is None:
            raise InvalidDataError("O status da candidatura não pode ser nulo.")
        if data.status is not None:
            current = ApplicationStatus(application.status)
            validate_transition(current, data.status)
            changed_at = datetime.now(UTC)
            if (
                data.status is ApplicationStatus.APLICADA
                and application.applied_at is None
            ):
                application.applied_at = changed_at
            application.status = data.status
            self._applications.add_history(
                ApplicationStatusHistory(
                    application_id=application.id,
                    from_status=current,
                    to_status=data.status,
                    changed_at=changed_at,
                    note=data.transition_note,
                )
            )
        elif data.transition_note is not None:
            raise InvalidDataError(
                "Informe o novo status para registrar uma nota de transição."
            )
        if "notes" in data.model_fields_set:
            application.notes = data.notes
        self._applications.commit()
        return application
