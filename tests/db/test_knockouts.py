"""Valida regras do perfil e requisitos reais lidos para os eliminatórios."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.matching.knockouts import KnockoutCode
from app.repositories.jobs import JobRepository
from app.repositories.profile import PreferenceRepository
from app.services.jobs import JobService


def test_avalia_preferencias_e_requisitos_persistidos(
    api_client: TestClient, test_engine: Engine
) -> None:
    candidate = api_client.post(
        "/candidates", json={"name": "Ana", "resume_text": "Texto fictício."}
    )
    assert candidate.status_code == 201
    candidate_id = uuid.UUID(candidate.json()["id"])
    preference_url = f"/candidates/{candidate_id}/preferences"
    preferences = api_client.put(
        preference_url,
        json={
            "work_modes": ["remote"],
            "knockout_rules": {
                "exclude_required_skills": ["  postgres ", "Docker"],
                "max_commute_km": 30,
            },
        },
    )
    assert preferences.status_code == 200
    assert preferences.json()["knockout_rules"] == {
        "exclude_required_skills": ["postgres", "Docker"],
        "max_commute_km": 30,
    }
    invalid = api_client.put(
        preference_url, json={"knockout_rules": {"exclude_companies": "Empresa A"}}
    )
    assert invalid.status_code == 422
    assert api_client.get(preference_url).json() == preferences.json()

    created = api_client.post(
        "/jobs",
        json={
            "title": "Analista",
            "company": "Empresa A",
            "url": "https://example.com/matching",
            "work_mode": "remoto",
            "description": "Requirements: PostgreSQL. Nice to have: Docker.",
        },
    )
    assert created.status_code == 201
    job_id = uuid.UUID(created.json()["job"]["id"])

    with Session(test_engine) as db:
        stored = PreferenceRepository(db).get(candidate_id)
        assert stored is not None
        service = JobService(JobRepository(db))
        result = service.evaluate_knockouts(job_id, stored)
        assert not result.eligible
        assert [(flag.code, flag.actual) for flag in result.flags] == [
            (KnockoutCode.EXCLUDED_REQUIRED_SKILL, "PostgreSQL")
        ]
        assert service.evaluate_knockouts(job_id, None).eligible
        with pytest.raises(NotFoundError):
            service.evaluate_knockouts(uuid.uuid4(), stored)
