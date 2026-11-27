"""Confere as garantias de candidaturas no PostgreSQL migrado."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Application,
    ApplicationStatus,
    ApplicationStatusHistory,
    Candidate,
    Job,
)


def _job(number: int) -> Job:
    url = f"https://example.com/vagas/{number}"
    return Job(
        title="Analista de Dados",
        company="Empresa X",
        source="manual",
        url=url,
        canonical_url=url,
        fingerprint="a" * 64,
    )


@pytest.fixture
def application(db_session: Session) -> Application:
    result = Application(
        candidate=Candidate(name="Pessoa", resume_text=""), job=_job(1)
    )
    db_session.add(result)
    db_session.flush()
    return result


def test_application_defaults_and_initial_history(
    db_session: Session, application: Application
) -> None:
    history = ApplicationStatusHistory(
        application=application, to_status=ApplicationStatus.SALVA
    )
    db_session.add(history)
    db_session.flush()
    db_session.refresh(application)
    db_session.refresh(history)

    assert application.status == ApplicationStatus.SALVA
    assert application.applied_at is None
    assert application.notes is None
    assert application.created_at.utcoffset() is not None
    assert application.created_at == application.updated_at
    assert application.status_history == [history]
    assert history.application_id == application.id
    assert history.from_status is None
    assert history.to_status == ApplicationStatus.SALVA
    assert history.changed_at.utcoffset() is not None


def test_application_pair_is_unique(
    db_session: Session, application: Application
) -> None:
    db_session.add(
        Application(candidate_id=application.candidate_id, job_id=application.job_id)
    )
    with pytest.raises(IntegrityError, match="uq_applications_candidate_job"):
        db_session.flush()


def test_application_can_share_only_one_side_of_pair(
    db_session: Session, application: Application
) -> None:
    db_session.add_all(
        [
            Application(candidate=application.candidate, job=_job(2)),
            Application(
                candidate=Candidate(name="Outra pessoa", resume_text=""),
                job=application.job,
            ),
        ]
    )
    db_session.flush()
    assert len(db_session.scalars(select(Application)).all()) == 3


@pytest.mark.parametrize("field", ["candidate_id", "job_id"])
def test_application_requires_existing_references(
    db_session: Session, application: Application, field: str
) -> None:
    setattr(application, field, uuid4())
    with pytest.raises(IntegrityError, match=f"applications_{field}_fkey"):
        db_session.flush()


def test_history_requires_existing_application(db_session: Session) -> None:
    db_session.add(ApplicationStatusHistory(application_id=uuid4(), to_status="salva"))
    with pytest.raises(
        IntegrityError, match="application_status_history_application_id_fkey"
    ):
        db_session.flush()


def test_invalid_application_status_is_rejected(
    db_session: Session, application: Application
) -> None:
    application.status = "inexistente"
    with pytest.raises(IntegrityError, match="ck_applications_status"):
        db_session.flush()


@pytest.mark.parametrize("field", ["from_status", "to_status"])
def test_invalid_history_status_is_rejected(
    db_session: Session, application: Application, field: str
) -> None:
    history = ApplicationStatusHistory(application=application, to_status="planejada")
    setattr(history, field, "inexistente")
    db_session.add(history)
    with pytest.raises(IntegrityError, match=f"ck_application_status_history_{field}"):
        db_session.flush()


def test_all_status_values_can_be_persisted(
    db_session: Session, application: Application
) -> None:
    applied_at = datetime(2026, 11, 19, 12, tzinfo=UTC)
    application.applied_at = applied_at
    application.notes = "Anotação da candidatura"
    for status in ApplicationStatus:
        db_session.add(
            ApplicationStatusHistory(
                application=application,
                from_status=application.status,
                to_status=status,
                note="Anotação do histórico",
            )
        )
        application.status = status
        db_session.flush()

    db_session.refresh(application)
    assert application.applied_at == applied_at
    assert application.notes == "Anotação da candidatura"
    assert {event.to_status for event in application.status_history} == set(
        ApplicationStatus
    )
    assert {event.note for event in application.status_history} == {
        "Anotação do histórico"
    }


@pytest.mark.parametrize("parent", [Application, Candidate])
def test_history_is_deleted_with_owning_record(
    db_session: Session, application: Application, parent: type[Application | Candidate]
) -> None:
    db_session.add(ApplicationStatusHistory(application=application, to_status="salva"))
    db_session.flush()
    parent_id = application.id if parent is Application else application.candidate_id
    db_session.execute(delete(parent).where(parent.id == parent_id))

    assert db_session.scalar(select(ApplicationStatusHistory.id)) is None
    assert db_session.scalar(select(Application.id)) is None
    assert db_session.scalar(select(Job.id)) == application.job_id


def test_job_with_application_can_be_archived_but_not_deleted(
    db_session: Session, application: Application
) -> None:
    application.job.is_archived = True
    db_session.flush()
    assert db_session.scalar(select(Application.id)) == application.id

    with pytest.raises(IntegrityError, match="applications_job_id_fkey"):
        db_session.execute(delete(Job).where(Job.id == application.job_id))
