"""Serviço de perfil: regras de negócio de candidato e preferências.

POR QUÊ: as rotas devem ser finas e os repositórios, burros. Aqui ficam as
regras que precisam valer para qualquer entrada (API, script, teste): e-mail
único, 404 de recurso inexistente, upsert 1:1 de preferências e tradução de
violação de integridade em erro de conflito.

Este módulo **não** importa FastAPI; os repositórios entram por injeção, o que
permite testar as regras sem banco.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.models import Candidate, CandidatePreference
from app.schemas.profile import CandidateCreate, CandidateUpdate, PreferencesPut


class CandidateRepositoryProtocol(Protocol):
    """Contrato mínimo do repositório de candidatos usado pelo serviço."""

    def get(self, candidate_id: uuid.UUID) -> Candidate | None: ...

    def get_by_email(self, email: str) -> Candidate | None: ...

    def add(self, candidate: Candidate) -> Candidate: ...

    def delete(self, candidate: Candidate) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class PreferenceRepositoryProtocol(Protocol):
    """Contrato mínimo do repositório de preferências usado pelo serviço."""

    def get(self, candidate_id: uuid.UUID) -> CandidatePreference | None: ...

    def add(self, preference: CandidatePreference) -> CandidatePreference: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class ProfileService:
    """Casos de uso de candidato e preferências."""

    def __init__(
        self,
        candidates: CandidateRepositoryProtocol,
        preferences: PreferenceRepositoryProtocol,
    ) -> None:
        self._candidates = candidates
        self._preferences = preferences

    # ------------------------------------------------------------------
    # Candidato
    # ------------------------------------------------------------------

    def create_candidate(self, data: CandidateCreate) -> Candidate:
        """Cria o candidato garantindo e-mail único."""
        self._ensure_email_available(data.email, candidate_id=None)

        candidate = Candidate(**data.model_dump(mode="json"))
        self._candidates.add(candidate)
        self._commit_or_conflict()
        return candidate

    def get_candidate(self, candidate_id: uuid.UUID) -> Candidate:
        """Retorna o candidato ou levanta 404."""
        candidate = self._candidates.get(candidate_id)
        if candidate is None:
            raise NotFoundError("Candidato não encontrado.")
        return candidate

    def update_candidate(
        self, candidate_id: uuid.UUID, data: CandidateUpdate
    ) -> Candidate:
        """Aplica apenas os campos enviados no `PATCH`."""
        candidate = self.get_candidate(candidate_id)
        payload = data.model_dump(exclude_unset=True, mode="json")
        if not payload:
            return candidate

        if payload.get("email"):
            self._ensure_email_available(payload["email"], candidate_id=candidate.id)

        for field, value in payload.items():
            setattr(candidate, field, value)
        self._commit_or_conflict()
        return candidate

    def delete_candidate(self, candidate_id: uuid.UUID) -> None:
        """Remove o candidato (preferências, skills e experiências em cascata)."""
        candidate = self.get_candidate(candidate_id)
        self._candidates.delete(candidate)
        self._candidates.commit()

    # ------------------------------------------------------------------
    # Preferências (1:1)
    # ------------------------------------------------------------------

    def get_preferences(self, candidate_id: uuid.UUID) -> CandidatePreference:
        """Retorna as preferências do candidato ou 404."""
        self.get_candidate(candidate_id)
        preference = self._preferences.get(candidate_id)
        if preference is None:
            raise NotFoundError("Preferências não encontradas.")
        return preference

    def put_preferences(
        self, candidate_id: uuid.UUID, data: PreferencesPut
    ) -> CandidatePreference:
        """Substitui o conjunto inteiro de preferências (upsert idempotente)."""
        candidate = self.get_candidate(candidate_id)
        payload = data.model_dump()

        preference = self._preferences.get(candidate.id)
        if preference is None:
            preference = CandidatePreference(candidate_id=candidate.id, **payload)
            self._preferences.add(preference)
        else:
            for field, value in payload.items():
                setattr(preference, field, value)

        self._preferences.commit()
        return preference

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------

    def _ensure_email_available(
        self, email: str | None, candidate_id: uuid.UUID | None
    ) -> None:
        """Levanta 409 se o e-mail já pertence a outro candidato.

        A checagem prévia dá uma mensagem clara no caso comum; a corrida entre
        duas requisições simultâneas ainda é coberta pelo índice único do banco
        (ver `_commit_or_conflict`).
        """
        if not email:
            return
        existing = self._candidates.get_by_email(email)
        if existing is not None and existing.id != candidate_id:
            raise ConflictError("Já existe um candidato com este e-mail.")

    def _commit_or_conflict(self) -> None:
        """Confirma a transação, traduzindo violação de unicidade em 409."""
        try:
            self._candidates.commit()
        except IntegrityError as exc:
            self._candidates.rollback()
            raise ConflictError("Já existe um candidato com este e-mail.") from exc
