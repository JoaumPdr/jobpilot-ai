"""Testes unitários da validação Pydantic dos schemas de perfil.

POR QUÊ: as regras de forma dos JSONB e dos payloads precisam falhar antes de
chegar ao banco. Aqui não há FastAPI nem PostgreSQL: só o contrato dos schemas.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.profile import (
    CandidateCreate,
    CandidateUpdate,
    EducationEntry,
    LanguageEntry,
    LanguageLevel,
    PreferencesPut,
)


def _candidate(**overrides: object) -> CandidateCreate:
    data: dict[str, object] = {
        "name": "Ana Silva",
        "email": "ana@example.com",
        "resume_text": "Currículo em texto.",
    }
    data.update(overrides)
    return CandidateCreate(**data)  # type: ignore[arg-type]


def test_email_is_trimmed_and_lowercased() -> None:
    candidate = _candidate(email="  Ana@Example.COM ")

    assert candidate.email == "ana@example.com"


@pytest.mark.parametrize("email", ["sem-arroba", "a@b", "@example.com", ""])
def test_invalid_email_is_rejected(email: str) -> None:
    # String vazia é normalizada para None (e-mail opcional), então só as
    # demais devem falhar.
    if email == "":
        assert _candidate(email=email).email is None
        return

    with pytest.raises(ValidationError):
        _candidate(email=email)


def test_candidate_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        _candidate(curriculo="campo que não existe")


def test_education_requires_institution_and_degree() -> None:
    with pytest.raises(ValidationError):
        EducationEntry(institution="USP")


def test_education_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        EducationEntry(
            institution="USP",
            degree="Bacharelado",
            curso="campo que não existe",
        )


def test_education_rejects_end_before_start() -> None:
    with pytest.raises(ValidationError):
        EducationEntry(
            institution="USP",
            degree="Bacharelado",
            start_date=date(2020, 1, 1),
            end_date=date(2019, 12, 31),
        )


def test_education_allows_open_end_date() -> None:
    entry = EducationEntry(
        institution="USP",
        degree="Bacharelado",
        start_date=date(2020, 1, 1),
    )

    assert entry.end_date is None


def test_education_serializes_dates_as_iso_strings() -> None:
    entry = EducationEntry(
        institution="USP",
        degree="Bacharelado",
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
    )

    assert entry.model_dump(mode="json")["start_date"] == "2020-01-01"


def test_language_level_accepts_known_values() -> None:
    entry = LanguageEntry(name="Inglês", level=LanguageLevel.FLUENTE)

    assert entry.model_dump(mode="json")["level"] == "fluente"


def test_language_level_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError):
        LanguageEntry(name="Inglês", level="expert")  # type: ignore[arg-type]


def test_candidate_update_rejects_explicit_null_in_required_field() -> None:
    with pytest.raises(ValidationError):
        CandidateUpdate.model_validate({"name": None})


def test_candidate_update_rejects_explicit_null_for_lists() -> None:
    with pytest.raises(ValidationError):
        CandidateUpdate.model_validate({"education": None})


def test_preferences_normalize_lists() -> None:
    preferences = PreferencesPut(
        desired_titles=["  Engenheira de Dados  ", "", "   "],
        locations=[" São Paulo "],
    )

    assert preferences.desired_titles == ["Engenheira de Dados"]
    assert preferences.locations == ["São Paulo"]


def test_preferences_reject_negative_salary() -> None:
    with pytest.raises(ValidationError):
        PreferencesPut(min_salary=Decimal("-0.01"))


def test_preferences_accept_knockout_rules_as_object() -> None:
    preferences = PreferencesPut(
        knockout_rules={"exclude_companies": ["Empresa X"], "max_commute_km": 30}
    )

    assert preferences.knockout_rules["max_commute_km"] == 30


@pytest.mark.parametrize(
    ("rule", "value"),
    [
        ("exclude_companies", None),
        ("exclude_companies", ["Empresa A", 42]),
        ("exclude_required_skills", [" "]),
        ("exclude_required_skills", {"name": "PostgreSQL"}),
    ],
)
def test_preferences_reject_malformed_knockout_lists(rule: str, value: object) -> None:
    with pytest.raises(ValidationError, match=rule):
        PreferencesPut(knockout_rules={rule: value})
