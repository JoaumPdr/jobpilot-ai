"""Serviço das experiências profissionais do candidato.

POR QUÊ: o `PATCH` pode receber só uma das datas; validar a faixa exige
combinar o payload com o estado atual — regra que não cabe no schema nem na
rota. `end_date` nula representa o vínculo atual.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from app.core.errors import InvalidDataError, NotFoundError
from app.models import Candidate, CandidateExperience
from app.schemas.experiences import ExperienceCreate, ExperienceUpdate


class CandidateRepositoryProtocol(Protocol):
    """Contrato mínimo do repositório de candidatos."""

    def get(self, candidate_id: uuid.UUID) -> Candidate | None: ...


class ExperienceRepositoryProtocol(Protocol):
    """Contrato mínimo do repositório de experiências."""

    def list_for_candidate(
        self, candidate_id: uuid.UUID
    ) -> list[CandidateExperience]: ...

    def get(
        self, candidate_id: uuid.UUID, experience_id: uuid.UUID
    ) -> CandidateExperience | None: ...

    def add(self, experience: CandidateExperience) -> CandidateExperience: ...

    def delete(self, experience: CandidateExperience) -> None: ...

    def commit(self) -> None: ...


class ExperienceService:
    """Casos de uso das experiências do candidato."""

    def __init__(
        self,
        candidates: CandidateRepositoryProtocol,
        experiences: ExperienceRepositoryProtocol,
    ) -> None:
        self._candidates = candidates
        self._experiences = experiences

    def list_experiences(self, candidate_id: uuid.UUID) -> list[CandidateExperience]:
        """Lista as experiências (404 se o candidato não existir)."""
        self._ensure_candidate(candidate_id)
        return self._experiences.list_for_candidate(candidate_id)

    def create_experience(
        self, candidate_id: uuid.UUID, data: ExperienceCreate
    ) -> CandidateExperience:
        """Cria uma experiência para o candidato."""
        self._ensure_candidate(candidate_id)

        experience = CandidateExperience(
            candidate_id=candidate_id,
            **data.model_dump(),
        )
        self._experiences.add(experience)
        self._experiences.commit()
        return experience

    def update_experience(
        self,
        candidate_id: uuid.UUID,
        experience_id: uuid.UUID,
        data: ExperienceUpdate,
    ) -> CandidateExperience:
        """Atualiza só os campos enviados e revalida a faixa de datas."""
        self._ensure_candidate(candidate_id)
        experience = self._get_experience(candidate_id, experience_id)

        payload = data.model_dump(exclude_unset=True)
        new_start = payload.get("start_date", experience.start_date)
        new_end = payload.get("end_date", experience.end_date)
        if new_start is not None and new_end is not None and new_end < new_start:
            raise InvalidDataError("end_date não pode ser anterior a start_date.")

        for field, value in payload.items():
            setattr(experience, field, value)
        self._experiences.commit()
        return experience

    def delete_experience(
        self, candidate_id: uuid.UUID, experience_id: uuid.UUID
    ) -> None:
        """Remove uma experiência do candidato."""
        self._ensure_candidate(candidate_id)
        experience = self._get_experience(candidate_id, experience_id)

        self._experiences.delete(experience)
        self._experiences.commit()

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------

    def _ensure_candidate(self, candidate_id: uuid.UUID) -> None:
        """Levanta 404 se o candidato não existir."""
        if self._candidates.get(candidate_id) is None:
            raise NotFoundError("Candidato não encontrado.")

    def _get_experience(
        self, candidate_id: uuid.UUID, experience_id: uuid.UUID
    ) -> CandidateExperience:
        """Retorna a experiência ou 404."""
        experience = self._experiences.get(candidate_id, experience_id)
        if experience is None:
            raise NotFoundError("Experiência não encontrada.")
        return experience
