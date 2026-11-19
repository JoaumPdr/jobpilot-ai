"""Testes unitários do serviço de experiências (sem banco e sem HTTP)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import NamedTuple

import pytest

from app.core.errors import InvalidDataError, NotFoundError
from app.models import Candidate
from app.schemas.experiences import ExperienceCreate, ExperienceUpdate
from app.services.experiences import ExperienceService
from tests.unit.fakes import FakeCandidateRepository, FakeExperienceRepository


class ExperienceContext(NamedTuple):
    service: ExperienceService
    candidates: FakeCandidateRepository
    experiences: FakeExperienceRepository
    candidate: Candidate


@pytest.fixture
def context() -> ExperienceContext:
    candidates = FakeCandidateRepository()
    experiences = FakeExperienceRepository()
    candidate = Candidate(
        name="Ana Silva",
        email="ana@example.com",
        resume_text="Currículo em texto.",
    )
    candidates.add(candidate)
    return ExperienceContext(
        ExperienceService(candidates, experiences), candidates, experiences, candidate
    )


def _payload(**overrides: object) -> ExperienceCreate:
    data: dict[str, object] = {
        "company": "Empresa X",
        "role": "Engenheira de Dados",
        "start_date": date(2020, 1, 1),
        "end_date": date(2022, 12, 31),
    }
    data.update(overrides)
    return ExperienceCreate(**data)  # type: ignore[arg-type]


def test_create_experience(context: ExperienceContext) -> None:
    experience = context.service.create_experience(
        context.candidate.id, _payload(skills_used=["Python"])
    )

    assert experience.company == "Empresa X"
    assert experience.skills_used == ["Python"]
    assert experience.id in context.experiences.items


def test_create_experience_rejects_unknown_candidate(
    context: ExperienceContext,
) -> None:
    with pytest.raises(NotFoundError):
        context.service.create_experience(uuid.uuid4(), _payload())


def test_list_experiences_filters_by_candidate(
    context: ExperienceContext,
) -> None:
    other = Candidate(name="Bruno", resume_text="Outro currículo.")
    context.candidates.add(other)
    context.service.create_experience(context.candidate.id, _payload())
    context.service.create_experience(
        other.id, _payload(company="Empresa Y", role="Analista")
    )

    assert [
        item.company for item in context.service.list_experiences(context.candidate.id)
    ] == ["Empresa X"]


def test_update_experience_with_invalid_date_range(
    context: ExperienceContext,
) -> None:
    experience = context.service.create_experience(context.candidate.id, _payload())

    with pytest.raises(InvalidDataError):
        context.service.update_experience(
            context.candidate.id,
            experience.id,
            ExperienceUpdate(start_date=date(2023, 1, 1)),
        )


def test_update_experience_accepts_open_end_date(
    context: ExperienceContext,
) -> None:
    experience = context.service.create_experience(context.candidate.id, _payload())

    updated = context.service.update_experience(
        context.candidate.id, experience.id, ExperienceUpdate(end_date=None)
    )

    assert updated.end_date is None


def test_update_experience_raises_not_found(
    context: ExperienceContext,
) -> None:
    with pytest.raises(NotFoundError):
        context.service.update_experience(
            context.candidate.id, uuid.uuid4(), ExperienceUpdate(role="Tech Lead")
        )


def test_delete_experience(context: ExperienceContext) -> None:
    experience = context.service.create_experience(context.candidate.id, _payload())

    context.service.delete_experience(context.candidate.id, experience.id)

    assert experience.id not in context.experiences.items


def test_delete_experience_raises_not_found(
    context: ExperienceContext,
) -> None:
    with pytest.raises(NotFoundError):
        context.service.delete_experience(context.candidate.id, uuid.uuid4())
