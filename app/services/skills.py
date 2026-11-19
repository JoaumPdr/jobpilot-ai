"""Serviço do catálogo de habilidades e do vínculo com o candidato.

POR QUÊ: o catálogo é compartilhado; criar/consultar skill e vincular ao
candidato são regras de negócio que não podem morar na rota. O serviço resolve
a skill por id ou nome, impede duplicidade do par e mantém o catálogo vivo
quando o vínculo é removido.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError, NotFoundError
from app.models import Candidate, CandidateSkill, Skill
from app.schemas.skills import CandidateSkillCreate, CandidateSkillUpdate, SkillCreate


class CandidateRepositoryProtocol(Protocol):
    """Contrato mínimo do repositório de candidatos."""

    def get(self, candidate_id: uuid.UUID) -> Candidate | None: ...


class SkillRepositoryProtocol(Protocol):
    """Contrato mínimo do catálogo de habilidades."""

    def list(self, query: str | None = None) -> list[Skill]: ...

    def get(self, skill_id: uuid.UUID) -> Skill | None: ...

    def get_by_name(self, canonical_name: str) -> Skill | None: ...

    def add(self, skill: Skill) -> Skill: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class CandidateSkillRepositoryProtocol(Protocol):
    """Contrato mínimo do vínculo candidato/skill."""

    def list_for_candidate(self, candidate_id: uuid.UUID) -> list[CandidateSkill]: ...

    def get(
        self, candidate_id: uuid.UUID, skill_id: uuid.UUID
    ) -> CandidateSkill | None: ...

    def add(self, candidate_skill: CandidateSkill) -> CandidateSkill: ...

    def delete(self, candidate_skill: CandidateSkill) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class SkillService:
    """Casos de uso do catálogo e do vínculo candidato/skill."""

    def __init__(
        self,
        candidates: CandidateRepositoryProtocol,
        skills: SkillRepositoryProtocol,
        candidate_skills: CandidateSkillRepositoryProtocol,
    ) -> None:
        self._candidates = candidates
        self._skills = skills
        self._candidate_skills = candidate_skills

    # ------------------------------------------------------------------
    # Catálogo
    # ------------------------------------------------------------------

    def list_skills(self, query: str | None = None) -> list[Skill]:
        """Lista o catálogo, opcionalmente filtrando por nome."""
        return self._skills.list(query)

    def create_skill(self, data: SkillCreate) -> Skill:
        """Cria uma habilidade canônica, sem duplicar nome (case-insensitive)."""
        if self._skills.get_by_name(data.canonical_name) is not None:
            raise ConflictError("Já existe uma habilidade com este nome.")

        skill = Skill(**data.model_dump(mode="json"))
        self._skills.add(skill)
        try:
            self._skills.commit()
        except IntegrityError as exc:
            self._skills.rollback()
            raise ConflictError("Já existe uma habilidade com este nome.") from exc
        return skill

    # ------------------------------------------------------------------
    # Vínculo candidato/skill
    # ------------------------------------------------------------------

    def list_candidate_skills(self, candidate_id: uuid.UUID) -> list[CandidateSkill]:
        """Lista as habilidades do candidato (404 se ele não existir)."""
        self._ensure_candidate(candidate_id)
        return self._candidate_skills.list_for_candidate(candidate_id)

    def add_candidate_skill(
        self, candidate_id: uuid.UUID, data: CandidateSkillCreate
    ) -> CandidateSkill:
        """Vincula uma skill existente ou cria pelo nome canônico."""
        self._ensure_candidate(candidate_id)
        skill = self._resolve_skill(data)

        if skill.id is not None and (
            self._candidate_skills.get(candidate_id, skill.id) is not None
        ):
            raise ConflictError("O candidato já possui esta habilidade.")

        candidate_skill = CandidateSkill(
            candidate_id=candidate_id,
            skill=skill,
            level=data.level.value if data.level is not None else None,
            years=data.years,
            evidence_note=data.evidence_note,
        )
        self._candidate_skills.add(candidate_skill)
        try:
            self._candidate_skills.commit()
        except IntegrityError as exc:
            self._candidate_skills.rollback()
            raise ConflictError(
                "Não foi possível vincular: habilidade já vinculada ou nome duplicado."
            ) from exc
        return candidate_skill

    def update_candidate_skill(
        self,
        candidate_id: uuid.UUID,
        skill_id: uuid.UUID,
        data: CandidateSkillUpdate,
    ) -> CandidateSkill:
        """Atualiza nível/anos/evidência do vínculo; `null` limpa o campo."""
        self._ensure_candidate(candidate_id)
        candidate_skill = self._candidate_skills.get(candidate_id, skill_id)
        if candidate_skill is None:
            raise NotFoundError("Habilidade do candidato não encontrada.")

        payload = data.model_dump(exclude_unset=True, mode="json")
        for field, value in payload.items():
            setattr(candidate_skill, field, value)
        self._candidate_skills.commit()
        return candidate_skill

    def remove_candidate_skill(
        self, candidate_id: uuid.UUID, skill_id: uuid.UUID
    ) -> None:
        """Remove o vínculo, preservando o catálogo."""
        self._ensure_candidate(candidate_id)
        candidate_skill = self._candidate_skills.get(candidate_id, skill_id)
        if candidate_skill is None:
            raise NotFoundError("Habilidade do candidato não encontrada.")

        self._candidate_skills.delete(candidate_skill)
        self._candidate_skills.commit()

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------

    def _ensure_candidate(self, candidate_id: uuid.UUID) -> None:
        """Levanta 404 se o candidato não existir."""
        if self._candidates.get(candidate_id) is None:
            raise NotFoundError("Candidato não encontrado.")

    def _resolve_skill(self, data: CandidateSkillCreate) -> Skill:
        """Resolve a skill por id ou por nome, criando no catálogo se faltar."""
        if data.skill_id is not None:
            skill = self._skills.get(data.skill_id)
            if skill is None:
                raise NotFoundError("Habilidade não encontrada.")
            return skill

        canonical_name = (data.canonical_name or "").strip()
        existing = self._skills.get_by_name(canonical_name)
        if existing is not None:
            return existing
        return self._skills.add(Skill(canonical_name=canonical_name))
