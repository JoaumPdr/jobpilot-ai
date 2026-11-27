"""Testes de constraint do esquema do perfil (F1-T01).

POR QUÊ: unicidade, FKs, CASCADE e CHECKs são regras que o banco precisa
garantir mesmo se a camada de serviço falhar. Aqui validamos o comportamento
real do PostgreSQL, não apenas o metadata do SQLAlchemy.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Candidate,
    CandidateExperience,
    CandidatePreference,
    CandidateSkill,
    Skill,
)


def _candidate(**overrides: object) -> Candidate:
    """Candidato mínimo válido, com campos sobrescritos quando necessário."""
    data: dict[str, object] = {
        "name": "Ana Silva",
        "email": "ana@example.com",
        "resume_text": "Currículo em texto.",
    }
    data.update(overrides)
    return Candidate(**data)  # type: ignore[arg-type]


def _skill(name: str = "Python") -> Skill:
    return Skill(canonical_name=name)


def _count(session: Session, model: type[object]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


# ---------------------------------------------------------------------------
# Candidato: e-mail
# ---------------------------------------------------------------------------


def test_email_is_normalized_before_saving(db_session: Session) -> None:
    """Espaços e maiúsculas viram minúsculas na escrita."""
    candidate = _candidate(email="  Joao@Email.COM ")
    db_session.add(candidate)
    db_session.flush()

    assert candidate.email == "joao@email.com"


def test_email_is_unique_case_insensitive(db_session: Session) -> None:
    """'joao@' e 'JOAO@' colidem no índice funcional lower(email)."""
    db_session.add(_candidate(email="joao@email.com"))
    db_session.flush()

    db_session.add(_candidate(email="JOAO@EMAIL.COM"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_email_null_is_allowed_for_multiple_candidates(db_session: Session) -> None:
    """E-mail é opcional; vários NULL não colidem no índice único."""
    db_session.add_all([_candidate(email=None), _candidate(email=None)])
    db_session.flush()

    assert _count(db_session, Candidate) == 2


# ---------------------------------------------------------------------------
# Unicidades (1:1 e pares)
# ---------------------------------------------------------------------------


def test_candidate_preference_is_one_to_one(db_session: Session) -> None:
    """Um candidato não pode ter duas linhas de preferência."""
    candidate = _candidate()
    db_session.add(candidate)
    db_session.flush()

    db_session.add(CandidatePreference(candidate_id=candidate.id))
    db_session.flush()

    db_session.add(CandidatePreference(candidate_id=candidate.id))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_skill_canonical_name_is_unique(db_session: Session) -> None:
    """O catálogo não aceita duas habilidades com o mesmo nome canônico."""
    db_session.add(_skill("SQL"))
    db_session.flush()

    db_session.add(_skill("SQL"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_candidate_skill_pair_is_unique(db_session: Session) -> None:
    """O mesmo candidato não declara a mesma habilidade duas vezes."""
    candidate = _candidate()
    skill = _skill()
    db_session.add_all([candidate, skill])
    db_session.flush()

    db_session.add(CandidateSkill(candidate_id=candidate.id, skill_id=skill.id))
    db_session.flush()

    db_session.add(CandidateSkill(candidate_id=candidate.id, skill_id=skill.id))
    with pytest.raises(IntegrityError):
        db_session.flush()


# ---------------------------------------------------------------------------
# Chaves estrangeiras e CASCADE
# ---------------------------------------------------------------------------


def test_candidate_skill_requires_existing_candidate(db_session: Session) -> None:
    """FK impede vínculo de habilidade com candidato inexistente."""
    skill = _skill()
    db_session.add(skill)
    db_session.flush()

    db_session.add(CandidateSkill(candidate_id=uuid.uuid4(), skill_id=skill.id))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_experience_requires_existing_candidate(db_session: Session) -> None:
    """FK impede experiência órfã."""
    db_session.add(
        CandidateExperience(
            candidate_id=uuid.uuid4(),
            company="Empresa",
            role="Dev",
            start_date=date(2020, 1, 1),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_deleting_candidate_cascades_and_keeps_skill_catalog(
    db_session: Session,
) -> None:
    """ON DELETE CASCADE remove dependentes, mas preserva o catálogo de skills.

    O DELETE via Core (`delete(...)`) força o CASCADE do banco, e não apenas o
    cascade do ORM — que é o comportamento que queremos garantir.
    """
    candidate = _candidate()
    skill = _skill()
    db_session.add_all([candidate, skill])
    db_session.flush()

    db_session.add(CandidatePreference(candidate_id=candidate.id))
    db_session.add(CandidateSkill(candidate_id=candidate.id, skill_id=skill.id))
    db_session.add(
        CandidateExperience(
            candidate_id=candidate.id,
            company="Empresa",
            role="Dev",
            start_date=date(2020, 1, 1),
        )
    )
    db_session.flush()

    db_session.execute(delete(Candidate).where(Candidate.id == candidate.id))
    db_session.flush()

    assert _count(db_session, CandidatePreference) == 0
    assert _count(db_session, CandidateSkill) == 0
    assert _count(db_session, CandidateExperience) == 0
    assert _count(db_session, Skill) == 1


# ---------------------------------------------------------------------------
# CHECKs
# ---------------------------------------------------------------------------


def test_skill_level_accepts_null_as_unknown(db_session: Session) -> None:
    """NULL significa nível desconhecido/não informado."""
    candidate = _candidate()
    skill = _skill()
    db_session.add_all([candidate, skill])
    db_session.flush()

    db_session.add(
        CandidateSkill(candidate_id=candidate.id, skill_id=skill.id, level=None)
    )
    db_session.flush()

    assert _count(db_session, CandidateSkill) == 1


def test_skill_level_accepts_known_values(db_session: Session) -> None:
    """Os três níveis previstos são aceitos."""
    candidate = _candidate()
    levels = ("iniciante", "intermediário", "avançado")
    skills = [_skill(f"Skill {index}") for index in range(len(levels))]
    db_session.add_all([candidate, *skills])
    db_session.flush()

    for level, skill in zip(levels, skills, strict=True):
        db_session.add(
            CandidateSkill(candidate_id=candidate.id, skill_id=skill.id, level=level)
        )
    db_session.flush()

    assert _count(db_session, CandidateSkill) == 3


def test_skill_level_rejects_unknown_value(db_session: Session) -> None:
    """Valor fora da lista é barrado pelo CHECK."""
    candidate = _candidate()
    skill = _skill()
    db_session.add_all([candidate, skill])
    db_session.flush()

    db_session.add(
        CandidateSkill(candidate_id=candidate.id, skill_id=skill.id, level="expert")
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_experience_rejects_end_before_start(db_session: Session) -> None:
    """end_date não pode ser anterior a start_date."""
    candidate = _candidate()
    db_session.add(candidate)
    db_session.flush()

    db_session.add(
        CandidateExperience(
            candidate_id=candidate.id,
            company="Empresa",
            role="Dev",
            start_date=date(2022, 1, 1),
            end_date=date(2021, 12, 31),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_experience_allows_open_ended_end_date(db_session: Session) -> None:
    """end_date NULL representa o vínculo atual."""
    candidate = _candidate()
    db_session.add(candidate)
    db_session.flush()

    db_session.add(
        CandidateExperience(
            candidate_id=candidate.id,
            company="Empresa",
            role="Dev",
            start_date=date(2022, 1, 1),
            end_date=None,
        )
    )
    db_session.flush()

    assert _count(db_session, CandidateExperience) == 1


def test_experience_rejects_negative_years(db_session: Session) -> None:
    """Anos de experiência na função não podem ser negativos."""
    candidate = _candidate()
    db_session.add(candidate)
    db_session.flush()

    db_session.add(
        CandidateExperience(
            candidate_id=candidate.id,
            company="Empresa",
            role="Dev",
            start_date=date(2022, 1, 1),
            years=-1,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_candidate_skill_rejects_negative_years(db_session: Session) -> None:
    """Anos usando a habilidade também não podem ser negativos."""
    candidate = _candidate()
    skill = _skill()
    db_session.add_all([candidate, skill])
    db_session.flush()

    db_session.add(
        CandidateSkill(candidate_id=candidate.id, skill_id=skill.id, years=-1)
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_min_salary_keeps_two_decimal_places(db_session: Session) -> None:
    """Numeric(12,2) preserva o valor monetário com duas casas."""
    candidate = _candidate()
    db_session.add(candidate)
    db_session.flush()

    preference = CandidatePreference(
        candidate_id=candidate.id, min_salary=Decimal("1234.56")
    )
    db_session.add(preference)
    db_session.flush()
    db_session.refresh(preference)

    assert preference.min_salary == Decimal("1234.56")
