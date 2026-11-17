"""Testes unitários do serviço de habilidades (sem banco e sem HTTP)."""

from __future__ import annotations

import uuid
from typing import NamedTuple

import pytest

from app.core.errors import ConflictError, NotFoundError
from app.models import Candidate
from app.schemas.skills import CandidateSkillCreate, CandidateSkillUpdate, SkillCreate
from app.services.skills import SkillService
from tests.unit.fakes import (
    FakeCandidateRepository,
    FakeCandidateSkillRepository,
    FakeSkillRepository,
)


class SkillContext(NamedTuple):
    service: SkillService
    candidates: FakeCandidateRepository
    skills: FakeSkillRepository
    links: FakeCandidateSkillRepository
    candidate: Candidate


@pytest.fixture
def context() -> SkillContext:
    candidates = FakeCandidateRepository()
    skills = FakeSkillRepository()
    links = FakeCandidateSkillRepository()
    candidate = Candidate(
        name="Ana Silva",
        email="ana@example.com",
        resume_text="Currículo em texto.",
    )
    candidates.add(candidate)
    return SkillContext(
        SkillService(candidates, skills, links), candidates, skills, links, candidate
    )


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------


def test_create_skill_trims_name(context: SkillContext) -> None:
    skill = context.service.create_skill(SkillCreate(canonical_name="  Python  "))

    assert skill.canonical_name == "Python"
    assert skill.id in context.skills.items


def test_create_skill_rejects_duplicate_name_case_insensitive(
    context: SkillContext,
) -> None:
    context.service.create_skill(SkillCreate(canonical_name="Python"))

    with pytest.raises(ConflictError):
        context.service.create_skill(SkillCreate(canonical_name="python"))


def test_list_skills_filters_case_insensitive(context: SkillContext) -> None:
    context.service.create_skill(SkillCreate(canonical_name="Python"))
    context.service.create_skill(SkillCreate(canonical_name="SQL"))

    assert [skill.canonical_name for skill in context.service.list_skills("py")] == [
        "Python"
    ]


# ---------------------------------------------------------------------------
# Vínculo candidato/skill
# ---------------------------------------------------------------------------


def test_add_skill_by_name_creates_catalog_entry(context: SkillContext) -> None:
    link = context.service.add_candidate_skill(
        context.candidate.id,
        CandidateSkillCreate(canonical_name="Python", level="intermediário"),
    )

    assert link.skill.canonical_name == "Python"
    assert link.level == "intermediário"
    assert len(context.skills.items) == 1
    assert len(context.links.items) == 1


def test_add_skill_by_name_reuses_catalog_entry(context: SkillContext) -> None:
    context.service.create_skill(SkillCreate(canonical_name="Python"))

    link = context.service.add_candidate_skill(
        context.candidate.id, CandidateSkillCreate(canonical_name="python")
    )

    assert len(context.skills.items) == 1
    assert link.skill_id == next(iter(context.skills.items))


def test_add_skill_by_id(context: SkillContext) -> None:
    skill = context.service.create_skill(SkillCreate(canonical_name="SQL"))

    link = context.service.add_candidate_skill(
        context.candidate.id,
        CandidateSkillCreate(skill_id=skill.id, years=3),
    )

    assert link.skill_id == skill.id
    assert link.years == 3


def test_add_skill_rejects_unknown_id(context: SkillContext) -> None:
    with pytest.raises(NotFoundError):
        context.service.add_candidate_skill(
            context.candidate.id,
            CandidateSkillCreate(skill_id=uuid.uuid4()),
        )


def test_add_skill_rejects_duplicate_pair(context: SkillContext) -> None:
    context.service.add_candidate_skill(
        context.candidate.id, CandidateSkillCreate(canonical_name="Python")
    )

    with pytest.raises(ConflictError):
        context.service.add_candidate_skill(
            context.candidate.id, CandidateSkillCreate(canonical_name="Python")
        )


def test_add_skill_rejects_unknown_candidate(context: SkillContext) -> None:
    with pytest.raises(NotFoundError):
        context.service.add_candidate_skill(
            uuid.uuid4(), CandidateSkillCreate(canonical_name="Python")
        )


def test_update_skill_link_and_clear_level(context: SkillContext) -> None:
    link = context.service.add_candidate_skill(
        context.candidate.id,
        CandidateSkillCreate(canonical_name="Python", level="iniciante", years=1),
    )

    updated = context.service.update_candidate_skill(
        context.candidate.id,
        link.skill_id,
        CandidateSkillUpdate(years=4),
    )

    assert updated.years == 4
    assert updated.level == "iniciante"

    cleared = context.service.update_candidate_skill(
        context.candidate.id,
        link.skill_id,
        CandidateSkillUpdate(level=None),
    )

    assert cleared.level is None


def test_update_unknown_link_returns_404(context: SkillContext) -> None:
    with pytest.raises(NotFoundError):
        context.service.update_candidate_skill(
            context.candidate.id, uuid.uuid4(), CandidateSkillUpdate(years=1)
        )


def test_remove_skill_link_keeps_catalog(context: SkillContext) -> None:
    context.service.create_skill(SkillCreate(canonical_name="Python"))
    link = context.service.add_candidate_skill(
        context.candidate.id, CandidateSkillCreate(canonical_name="Python")
    )

    context.service.remove_candidate_skill(context.candidate.id, link.skill_id)

    assert context.links.items == {}
    assert len(context.skills.items) == 1


def test_remove_unknown_link_returns_404(context: SkillContext) -> None:
    with pytest.raises(NotFoundError):
        context.service.remove_candidate_skill(context.candidate.id, uuid.uuid4())
