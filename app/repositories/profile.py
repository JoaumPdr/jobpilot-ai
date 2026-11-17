"""Repositórios do perfil (acesso a dados SQLAlchemy).

POR QUÊ: isolar consultas/escritas aqui mantém o serviço independente do ORM e
permite testar as regras com repositórios falsos. Nenhum repositório conhece
HTTP; nenhum serviço monta `select`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Candidate,
    CandidateExperience,
    CandidatePreference,
    CandidateSkill,
    Skill,
)


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
        """Busca o candidato com preferências, skills e experiências carregadas.

        POR QUÊ: `GET /candidates/{id}` devolve tudo; sem `selectinload` o
        Pydantic dispararia consultas N+1 ao serializar as listas.
        """
        stmt = (
            select(Candidate)
            .where(Candidate.id == candidate_id)
            .options(
                selectinload(Candidate.preferences),
                selectinload(Candidate.skills).selectinload(CandidateSkill.skill),
                selectinload(Candidate.experiences),
            )
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


class SkillRepository(BaseRepository):
    """Consultas e escritas do catálogo `skills`."""

    def list(self, query: str | None = None) -> list[Skill]:
        """Lista o catálogo; `query` filtra o nome sem diferenciar caixa."""
        stmt = select(Skill)
        if query and query.strip():
            pattern = f"%{query.strip().lower()}%"
            stmt = stmt.where(func.lower(Skill.canonical_name).like(pattern))
        stmt = stmt.order_by(func.lower(Skill.canonical_name))
        return list(self._db.scalars(stmt))

    def get(self, skill_id: uuid.UUID) -> Skill | None:
        """Retorna a habilidade pelo id."""
        return self._db.get(Skill, skill_id)

    def get_by_name(self, canonical_name: str) -> Skill | None:
        """Busca pelo nome canônico sem diferenciar maiúsculas de minúsculas."""
        stmt = select(Skill).where(
            func.lower(Skill.canonical_name) == canonical_name.strip().lower()
        )
        return self._db.scalar(stmt)

    def add(self, skill: Skill) -> Skill:
        """Adiciona uma habilidade ao catálogo."""
        self._db.add(skill)
        return skill


class CandidateSkillRepository(BaseRepository):
    """Consultas e escritas do vínculo `candidate_skills`."""

    def list_for_candidate(self, candidate_id: uuid.UUID) -> list[CandidateSkill]:
        """Lista os vínculos do candidato, com a habilidade carregada."""
        stmt = (
            select(CandidateSkill)
            .where(CandidateSkill.candidate_id == candidate_id)
            .options(selectinload(CandidateSkill.skill))
            .order_by(CandidateSkill.created_at)
        )
        return list(self._db.scalars(stmt))

    def get(
        self, candidate_id: uuid.UUID, skill_id: uuid.UUID
    ) -> CandidateSkill | None:
        """Retorna o vínculo do par candidato/skill, se existir."""
        stmt = (
            select(CandidateSkill)
            .where(
                CandidateSkill.candidate_id == candidate_id,
                CandidateSkill.skill_id == skill_id,
            )
            .options(selectinload(CandidateSkill.skill))
        )
        return self._db.scalar(stmt)

    def add(self, candidate_skill: CandidateSkill) -> CandidateSkill:
        """Adiciona um vínculo candidato/skill."""
        self._db.add(candidate_skill)
        return candidate_skill

    def delete(self, candidate_skill: CandidateSkill) -> None:
        """Remove o vínculo (o catálogo permanece)."""
        self._db.delete(candidate_skill)


class ExperienceRepository(BaseRepository):
    """Consultas e escritas de `candidate_experiences`."""

    def list_for_candidate(self, candidate_id: uuid.UUID) -> list[CandidateExperience]:
        """Lista as experiências, da mais recente para a mais antiga."""
        stmt = (
            select(CandidateExperience)
            .where(CandidateExperience.candidate_id == candidate_id)
            .order_by(CandidateExperience.start_date.desc())
        )
        return list(self._db.scalars(stmt))

    def get(
        self, candidate_id: uuid.UUID, experience_id: uuid.UUID
    ) -> CandidateExperience | None:
        """Retorna a experiência do candidato, se existir."""
        stmt = select(CandidateExperience).where(
            CandidateExperience.candidate_id == candidate_id,
            CandidateExperience.id == experience_id,
        )
        return self._db.scalar(stmt)

    def add(self, experience: CandidateExperience) -> CandidateExperience:
        """Adiciona uma experiência."""
        self._db.add(experience)
        return experience

    def delete(self, experience: CandidateExperience) -> None:
        """Remove uma experiência."""
        self._db.delete(experience)
