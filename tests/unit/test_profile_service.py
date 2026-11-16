"""Testes unitários das regras do serviço de perfil.

POR QUÊ: as regras (e-mail único, 404, upsert de preferências) devem ser
testadas sem banco e sem HTTP. Repositórios falsos registram o que o serviço
pediu, então uma falha aqui aponta para a regra, não para o PostgreSQL.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from app.core.errors import ConflictError, NotFoundError
from app.models import Candidate, CandidatePreference
from app.schemas.profile import CandidateCreate, CandidateUpdate, PreferencesPut
from app.services.profile import ProfileService


class FakeCandidateRepository:
    """Repositório em memória com o contrato usado pelo serviço."""

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


@pytest.fixture
def service() -> tuple[
    ProfileService, FakeCandidateRepository, FakePreferenceRepository
]:
    candidates = FakeCandidateRepository()
    preferences = FakePreferenceRepository()
    return ProfileService(candidates, preferences), candidates, preferences


def _create_payload(**overrides: object) -> CandidateCreate:
    data: dict[str, object] = {
        "name": "Ana Silva",
        "email": "Ana@Example.COM",
        "resume_text": "Currículo em texto.",
    }
    data.update(overrides)
    return CandidateCreate(**data)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Candidato
# ---------------------------------------------------------------------------


def test_create_candidate_normalizes_email(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, candidates, _ = service

    candidate = profile.create_candidate(_create_payload())

    assert candidate.email == "ana@example.com"
    assert candidate.id in candidates.items
    assert candidates.commits == 1


def test_create_candidate_rejects_duplicate_email_case_insensitive(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, _, _ = service
    profile.create_candidate(_create_payload())

    with pytest.raises(ConflictError):
        profile.create_candidate(_create_payload(email="ANA@example.com"))


def test_create_candidate_allows_null_email_twice(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, _, _ = service

    profile.create_candidate(_create_payload(email=None))
    profile.create_candidate(_create_payload(email=None))


def test_get_candidate_raises_not_found(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, _, _ = service

    with pytest.raises(NotFoundError):
        profile.get_candidate(uuid.uuid4())


def test_update_candidate_changes_only_sent_fields(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, _, _ = service
    candidate = profile.create_candidate(_create_payload())

    updated = profile.update_candidate(
        candidate.id, CandidateUpdate(headline="Engenheira de Dados")
    )

    assert updated.headline == "Engenheira de Dados"
    assert updated.name == "Ana Silva"
    assert updated.email == "ana@example.com"


def test_update_candidate_clears_optional_field(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, _, _ = service
    candidate = profile.create_candidate(_create_payload(headline="Headline"))

    updated = profile.update_candidate(candidate.id, CandidateUpdate(headline=None))

    assert updated.headline is None


def test_update_candidate_rejects_email_of_other_candidate(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, _, _ = service
    profile.create_candidate(_create_payload())
    other = profile.create_candidate(
        _create_payload(name="Bruno", email="bruno@example.com")
    )

    with pytest.raises(ConflictError):
        profile.update_candidate(other.id, CandidateUpdate(email="ANA@EXAMPLE.COM"))


def test_update_candidate_raises_not_found(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, _, _ = service

    with pytest.raises(NotFoundError):
        profile.update_candidate(uuid.uuid4(), CandidateUpdate(headline="X"))


def test_delete_candidate_removes_it(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, candidates, _ = service
    candidate = profile.create_candidate(_create_payload())

    profile.delete_candidate(candidate.id)

    assert candidate.id not in candidates.items


def test_delete_candidate_raises_not_found(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, _, _ = service

    with pytest.raises(NotFoundError):
        profile.delete_candidate(uuid.uuid4())


# ---------------------------------------------------------------------------
# Preferências
# ---------------------------------------------------------------------------


def test_put_preferences_creates_then_updates_same_row(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, _, preferences = service
    candidate = profile.create_candidate(_create_payload())

    created = profile.put_preferences(
        candidate.id,
        PreferencesPut(
            desired_titles=["Engenheira de Dados"],
            min_salary=Decimal("12000.00"),
        ),
    )
    updated = profile.put_preferences(
        candidate.id,
        PreferencesPut(desired_titles=["Analista de Dados"]),
    )

    assert updated.id == created.id
    assert len(preferences.items) == 1
    assert updated.desired_titles == ["Analista de Dados"]
    # PUT substitui o conjunto inteiro: salário não enviado volta ao default.
    assert updated.min_salary is None


def test_get_preferences_raises_not_found_when_missing(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, _, _ = service
    candidate = profile.create_candidate(_create_payload())

    with pytest.raises(NotFoundError):
        profile.get_preferences(candidate.id)


def test_put_preferences_raises_not_found_for_unknown_candidate(
    service: tuple[ProfileService, FakeCandidateRepository, FakePreferenceRepository],
) -> None:
    profile, _, _ = service

    with pytest.raises(NotFoundError):
        profile.put_preferences(uuid.uuid4(), PreferencesPut())
