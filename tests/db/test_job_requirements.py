"""Valida o fluxo de requisitos com API, serviço e PostgreSQL real."""

import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, delete, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import Job, JobSkill, Skill
from app.repositories.jobs import JobRepository
from app.schemas.jobs import JobCreate
from app.services.jobs import JobService


def test_cadastro_e_importacao_persistem_requisitos(
    api_client: TestClient, test_engine: Engine
) -> None:
    existing = api_client.post("/skills", json={"canonical_name": "python"})
    assert existing.status_code == 201
    manual = api_client.post(
        "/jobs",
        json={
            "title": "Analista",
            "company": "Equipe A",
            "url": "https://example.com/manual",
            "description": "Requisitos: Python.\nDiferenciais: banco de dados relacional.",
        },
    )
    assert manual.status_code == 201

    csv = (
        b"title,company,description,url\n"
        b'Data Engineer,Team B,"Requirements: Python and SQL.",https://example.com/1\n'
        b'Analyst,Team C,"Preferred qualifications: Python.",https://example.com/2\n'
    )
    for expected_count in (2, 0):
        response = api_client.post(
            "/jobs/import", files={"file": ("requirements.csv", csv, "text/csv")}
        )
        assert response.status_code == 201
        assert response.json()["inserted"] == expected_count

    with Session(test_engine) as db:
        records = db.execute(
            select(Job.url, Skill.canonical_name, JobSkill)
            .join(JobSkill, JobSkill.job_id == Job.id)
            .join(Skill, Skill.id == JobSkill.skill_id)
        )
        stored = {(url, skill): item for url, skill, item in records}

        assert len(stored) == 5
        manual_python = stored[("https://example.com/manual", "python")]
        assert str(manual_python.skill_id) == existing.json()["id"]
        assert manual_python.requirement_type == "obrigatorio"
        assert manual_python.extraction_method == "deterministico"
        assert manual_python.weight is None
        differential = stored[("https://example.com/manual", "Relational Databases")]
        assert differential.requirement_type == "desejavel"
        assert differential.evidence_snippet == "banco de dados relacional."
        assert differential.confidence == 0.85
        assert (
            stored[("https://example.com/2", "python")].skill_id
            == manual_python.skill_id
        )


def test_reprocessa_vaga_existente_e_remove_requisitos_antigos(
    db_session: Session,
) -> None:
    job = Job(
        title="Analista",
        company="Equipe",
        description="Must know Docker.",
        source="manual",
        url="https://example.com/legacy",
        canonical_url="https://example.com/legacy",
        fingerprint="x",
    )
    db_session.add(job)
    db_session.flush()
    service = JobService(JobRepository(db_session))

    first = service.refresh_requirements(job.id)
    assert first == service.refresh_requirements(job.id)
    stored = list(db_session.scalars(select(JobSkill)))
    assert len(stored) == 1
    assert stored[0].evidence_snippet == "Must know Docker."

    job.description = "Sobre a empresa: usamos Docker."
    db_session.flush()
    assert service.refresh_requirements(job.id) == ()
    assert list(db_session.scalars(select(JobSkill))) == []
    with pytest.raises(NotFoundError):
        service.refresh_requirements(uuid.uuid4())


def test_banco_rejeita_requisitos_duplicados(db_session: Session) -> None:
    job = Job(
        title="Analista",
        company="Equipe",
        description="Requirements: Python",
        source="manual",
        url="https://example.com/unique",
        canonical_url="https://example.com/unique",
        fingerprint="y",
    )
    db_session.add(job)
    db_session.flush()
    JobService(JobRepository(db_session)).refresh_requirements(job.id)
    requirement = db_session.scalars(select(JobSkill)).one()
    db_session.add(
        JobSkill(
            job_id=job.id,
            skill_id=requirement.skill_id,
            requirement_type="desejavel",
            confidence=0.95,
            evidence_snippet="Python",
            extraction_method="deterministico",
        )
    )
    with pytest.raises(IntegrityError, match="uq_job_skills_job_skill"):
        db_session.flush()


def test_migracao_preserva_vaga_e_catalogo_no_ciclo(test_engine: Engine) -> None:
    with Session(test_engine) as db:
        job, _ = JobService(JobRepository(db)).create_manual(
            JobCreate(
                title="Analista",
                company="Equipe",
                description="Requirements: Python",
                url="https://example.com/migration",
            )
        )
        job_id = job.id
        skill_id = db.scalar(select(JobSkill.skill_id).where(JobSkill.job_id == job_id))
        assert skill_id is not None

    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.set_main_option(
        "sqlalchemy.url",
        test_engine.url.render_as_string(hide_password=False).replace("%", "%%"),
    )
    try:
        command.downgrade(config, "000000000004")
        assert not inspect(test_engine).has_table("job_skills")
        with Session(test_engine) as db:
            assert db.get(Job, job_id) is not None
            assert db.get(Skill, skill_id) is not None

        command.upgrade(config, "head")
        with Session(test_engine) as db:
            JobService(JobRepository(db)).refresh_requirements(job_id)
            assert (
                db.scalar(select(JobSkill.skill_id).where(JobSkill.job_id == job_id))
                == skill_id
            )
    finally:
        command.upgrade(config, "head")
        with Session(test_engine) as db:
            db.execute(delete(Job).where(Job.id == job_id))
            db.execute(delete(Skill).where(Skill.id == skill_id))
            db.commit()
