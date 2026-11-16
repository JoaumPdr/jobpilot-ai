"""Repositórios do perfil (acesso a dados SQLAlchemy).

POR QUÊ: isolar consultas/escritas aqui mantém o serviço independente do ORM e
permite testar as regras com repositórios falsos. Nenhum repositório conhece
HTTP; nenhum serviço monta `select`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Candidate, CandidatePreference


class BaseRepository:
    """Base com o controle de transação usado pelo serviço."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def commit(self) -> None:
        """Confirma a transação corrente."""
        self._db.commit()

    def rollback(self) -> None:
        """Descarta a transação corrente (após erro de integridade)."""
        self._db.rollback()


class CandidateRepository(BaseRepository):
    """Consultas e escritas de `candidates`."""

    def get(self, candidate_id: uuid.UUID) -> Candidate | None:
        """Busca o candidato com as preferências já carregadas (1:1)."""
        stmt = (
            select(Candidate)
            .where(Candidate.id == candidate_id)
            .options(selectinload(Candidate.preferences))
        )
        return self._db.scalar(stmt)

    def get_by_email(self, email: str) -> Candidate | None:
        """Busca por e-mail sem diferenciar maiúsculas de minúsculas."""
        stmt = select(Candidate).where(
            func.lower(Candidate.email) == email.strip().lower()
        )
        return self._db.scalar(stmt)

    def add(self, candidate: Candidate) -> Candidate:
        """Adiciona um novo candidato à sessão."""
        self._db.add(candidate)
        return candidate

    def delete(self, candidate: Candidate) -> None:
        """Remove o candidato (dependentes caem por CASCADE no banco)."""
        self._db.delete(candidate)


class PreferenceRepository(BaseRepository):
    """Consultas e escritas de `candidate_preferences` (1:1)."""

    def get(self, candidate_id: uuid.UUID) -> CandidatePreference | None:
        """Retorna as preferências do candidato, se existirem."""
        stmt = select(CandidatePreference).where(
            CandidatePreference.candidate_id == candidate_id
        )
        return self._db.scalar(stmt)

    def add(self, preference: CandidatePreference) -> CandidatePreference:
        """Adiciona a linha de preferências à sessão."""
        self._db.add(preference)
        return preference
