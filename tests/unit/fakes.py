"""Dublês em memória dos repositórios do perfil.

POR QUÊ: os testes unitários dos serviços não devem depender de PostgreSQL.
Cada dublê implementa o contrato mínimo usado pelo serviço e registra commits
para que os testes possam afirmar que a transação foi confirmada.
"""

from __future__ import annotations

import uuid

from app.models import (
    Candidate,
    CandidateExperience,
    CandidatePreference,
    CandidateSkill,
    Skill,
)


class FakeCandidateRepository:
    """Repositório em memória de candidatos."""

    def __init__(self) -> None:
        self.items: dict[uuid.UUID, Candidate] = {}
        self.commits = 0
        self.rollbacks = 0

    def get(self, candidate_id: uuid.UUID) -> Candidate | None:
        return self.items.get(candidate_id)

    def get_by_email(self, email: str) -> Candidate | None:
        normalized = email.strip().lower()
        return next(
            (
                candidate
                for candidate in self.items.values()
                if (candidate.email or "").lower() == normalized
            ),
            None,
        )

    def add(self, candidate: Candidate) -> Candidate:
        if candidate.id is None:
            candidate.id = uuid.uuid4()
        self.items[candidate.id] = candidate
        return candidate

    def delete(self, candidate: Candidate) -> None:
        self.items.pop(candidate.id, None)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakePreferenceRepository:
    """Repositório em memória de preferências (1:1 por candidato)."""

    def __init__(self) -> None:
        self.items: dict[uuid.UUID, CandidatePreference] = {}
        self.commits = 0
        self.rollbacks = 0

    def get(self, candidate_id: uuid.UUID) -> CandidatePreference | None:
        return self.items.get(candidate_id)

    def add(self, preference: CandidatePreference) -> CandidatePreference:
        if preference.id is None:
            preference.id = uuid.uuid4()
        self.items[preference.candidate_id] = preference
        return preference

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeSkillRepository:
    """Repositório em memória do catálogo de habilidades."""

    def __init__(self) -> None:
        self.items: dict[uuid.UUID, Skill] = {}
        self.commits = 0
        self.rollbacks = 0

    def list(self, query: str | None = None) -> list[Skill]:
        skills = list(self.items.values())
        if query and query.strip():
            needle = query.strip().lower()
            skills = [
                skill for skill in skills if needle in skill.canonical_name.lower()
            ]
        return sorted(skills, key=lambda skill: skill.canonical_name.lower())

    def get(self, skill_id: uuid.UUID) -> Skill | None:
        return self.items.get(skill_id)

    def get_by_name(self, canonical_name: str) -> Skill | None:
        normalized = canonical_name.strip().lower()
        return next(
            (
                skill
                for skill in self.items.values()
                if skill.canonical_name.lower() == normalized
            ),
            None,
        )

    def add(self, skill: Skill) -> Skill:
        if skill.id is None:
            skill.id = uuid.uuid4()
        self.items[skill.id] = skill
        return skill

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeCandidateSkillRepository:
    """Repositório em memória do vínculo candidato/skill."""

    def __init__(self) -> None:
        self.items: dict[tuple[uuid.UUID, uuid.UUID], CandidateSkill] = {}
        self.commits = 0
        self.rollbacks = 0

    def list_for_candidate(self, candidate_id: uuid.UUID) -> list[CandidateSkill]:
        return [
            link
            for (owner_id, _), link in self.items.items()
            if owner_id == candidate_id
        ]

    def get(
        self, candidate_id: uuid.UUID, skill_id: uuid.UUID
    ) -> CandidateSkill | None:
        return self.items.get((candidate_id, skill_id))

    def add(self, candidate_skill: CandidateSkill) -> CandidateSkill:
        if candidate_skill.id is None:
            candidate_skill.id = uuid.uuid4()
        if candidate_skill.skill_id is None:
            candidate_skill.skill_id = candidate_skill.skill.id
        self.items[(candidate_skill.candidate_id, candidate_skill.skill_id)] = (
            candidate_skill
        )
        return candidate_skill

    def delete(self, candidate_skill: CandidateSkill) -> None:
        self.items.pop((candidate_skill.candidate_id, candidate_skill.skill_id), None)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeExperienceRepository:
    """Repositório em memória de experiências."""

    def __init__(self) -> None:
        self.items: dict[uuid.UUID, CandidateExperience] = {}
        self.commits = 0

    def list_for_candidate(self, candidate_id: uuid.UUID) -> list[CandidateExperience]:
        return [
            experience
            for experience in self.items.values()
            if experience.candidate_id == candidate_id
        ]

    def get(
        self, candidate_id: uuid.UUID, experience_id: uuid.UUID
    ) -> CandidateExperience | None:
        experience = self.items.get(experience_id)
        if experience is None or experience.candidate_id != candidate_id:
            return None
        return experience

    def add(self, experience: CandidateExperience) -> CandidateExperience:
        if experience.id is None:
            experience.id = uuid.uuid4()
        self.items[experience.id] = experience
        return experience

    def delete(self, experience: CandidateExperience) -> None:
        self.items.pop(experience.id, None)

    def commit(self) -> None:
        self.commits += 1
