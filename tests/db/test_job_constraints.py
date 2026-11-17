"""Testes de constraint do esquema de vagas (F1-T03).

POR QUÊ: unicidade parcial, FKs com `SET NULL`, CHECKs de enum e faixa de
salário são regras que o banco precisa garantir mesmo se a camada de serviço
falhar. Assim como no perfil, validamos o PostgreSQL real, não só o metadata.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ImportBatch, Job


def _job(**overrides: object) -> Job:
    """Vaga mínima válida (já normalizada), com campos sobrescritos."""
    data: dict[str, object] = {
        "title": "Engenheira de Dados",
        "company": "Empresa X",
        "source": "manual",
        "url": "https://example.com/vagas/1",
        "canonical_url": "https://example.com/vagas/1",
        # 64 caracteres = SHA-256 em hexadecimal; o cálculo é da F1-T04.
        "fingerprint": "a" * 64,
    }
    data.update(overrides)
    return Job(**data)  # type: ignore[arg-type]


def _batch(**overrides: object) -> ImportBatch:
    """Lote mínimo válido."""
    data: dict[str, object] = {"source": "manual", "kind": "manual"}
    data.update(overrides)
    return ImportBatch(**data)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Unicidade (source, external_id)
# ---------------------------------------------------------------------------


def test_source_external_id_is_unique_when_present(db_session: Session) -> None:
    """Mesma fonte + mesmo ID externo não pode repetir."""
    db_session.add(_job(external_id="123"))
    db_session.flush()

    db_session.add(_job(external_id="123", url="https://example.com/vagas/2"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_multiple_null_external_ids_are_allowed(db_session: Session) -> None:
    """CSV/manual sem ID externo não colidem entre si."""
    db_session.add_all([_job(), _job(url="https://example.com/vagas/2")])
    db_session.flush()

    assert db_session.scalar(select(func.count()).select_from(Job)) == 2


def test_same_external_id_is_allowed_across_sources(db_session: Session) -> None:
    """O par é único por fonte: o mesmo ID em portais diferentes é válido."""
    db_session.add_all(
        [
            _job(source="portal-a", external_id="123"),
            _job(source="portal-b", external_id="123"),
        ]
    )
    db_session.flush()

    assert db_session.scalar(select(func.count()).select_from(Job)) == 2


# ---------------------------------------------------------------------------
# CHECKs de enum e salário
# ---------------------------------------------------------------------------


def test_work_mode_and_seniority_default_to_unknown(db_session: Session) -> None:
    """Sem normalização explícita, a vaga assume 'desconhecido'."""
    job = _job()
    db_session.add(job)
    db_session.flush()
    db_session.refresh(job)

    assert job.work_mode == "desconhecido"
    assert job.seniority == "desconhecido"


def test_known_work_mode_and_seniority_are_accepted(db_session: Session) -> None:
    """Os valores acentuados do plano são aceitos."""
    job = _job(work_mode="híbrido", seniority="sênior")
    db_session.add(job)
    db_session.flush()

    assert job.work_mode == "híbrido"
    assert job.seniority == "sênior"


@pytest.mark.parametrize("field", ["work_mode", "seniority"])
def test_invalid_enum_value_is_rejected(db_session: Session, field: str) -> None:
    """Valor fora da lista do CHECK é rejeitado pelo banco."""
    db_session.add(_job(**{field: "inventado"}))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_negative_salary_is_rejected(db_session: Session) -> None:
    """Salário nunca é negativo."""
    db_session.add(_job(salary_min=-1))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_salary_max_below_min_is_rejected(db_session: Session) -> None:
    """A faixa salarial precisa ser coerente quando as duas pontas existem."""
    db_session.add(_job(salary_min=10000, salary_max=9000))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_valid_salary_range_is_accepted(db_session: Session) -> None:
    """Faixa coerente e moeda ISO são aceitas."""
    job = _job(salary_min=8000, salary_max=12000, currency="BRL")
    db_session.add(job)
    db_session.flush()

    assert job.salary_min == 8000


# ---------------------------------------------------------------------------
# FKs e SET NULL
# ---------------------------------------------------------------------------


def test_duplicate_of_itself_is_rejected(db_session: Session) -> None:
    """Uma vaga não pode ser duplicata de si mesma."""
    job = _job()
    db_session.add(job)
    db_session.flush()

    job.duplicate_of_job_id = job.id
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_deleting_original_job_clears_duplicate_pointer(db_session: Session) -> None:
    """Apagar a vaga original deixa a duplicata sem ponteiro (SET NULL)."""
    original = _job()
    duplicate = _job(url="https://example.com/vagas/2")
    db_session.add_all([original, duplicate])
    db_session.flush()
    duplicate.duplicate_of_job_id = original.id
    db_session.flush()

    db_session.delete(original)
    db_session.flush()
    db_session.expire_all()

    assert db_session.get(Job, duplicate.id).duplicate_of_job_id is None  # type: ignore[union-attr]


def test_unknown_import_batch_is_rejected(db_session: Session) -> None:
    """A FK para o lote precisa existir."""
    db_session.add(_job(import_batch_id=uuid.uuid4()))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_deleting_batch_keeps_jobs_and_clears_reference(
    db_session: Session,
) -> None:
    """Apagar o lote não apaga vagas; só limpa o vínculo."""
    batch = _batch()
    db_session.add(batch)
    db_session.flush()
    job = _job(import_batch_id=batch.id)
    db_session.add(job)
    db_session.flush()

    db_session.delete(batch)
    db_session.flush()
    db_session.expire_all()

    stored = db_session.get(Job, job.id)
    assert stored is not None
    assert stored.import_batch_id is None


# ---------------------------------------------------------------------------
# Lotes de importação
# ---------------------------------------------------------------------------


def test_batch_counters_and_errors_default_to_zero(db_session: Session) -> None:
    """O lote nasce zerado e sem erros."""
    batch = _batch()
    db_session.add(batch)
    db_session.flush()
    db_session.refresh(batch)

    assert (batch.total_rows, batch.inserted, batch.duplicates, batch.rejected) == (
        0,
        0,
        0,
        0,
    )
    assert batch.errors == []


def test_invalid_batch_kind_is_rejected(db_session: Session) -> None:
    """Só csv/manual/api identificam a origem do lote."""
    db_session.add(_batch(kind="planilha"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_negative_batch_counter_is_rejected(db_session: Session) -> None:
    """Contadores do relatório nunca são negativos."""
    db_session.add(_batch(rejected=-1))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_finished_before_started_is_rejected(db_session: Session) -> None:
    """O lote não termina antes de começar."""
    started = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)
    db_session.add(
        _batch(started_at=started, finished_at=started - timedelta(minutes=1))
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


# ---------------------------------------------------------------------------
# Índices
# ---------------------------------------------------------------------------


def test_job_indexes_exist(db_session: Session) -> None:
    """A dedup depende dos índices de fingerprint e URL canônica."""
    rows = db_session.execute(
        text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'jobs'")
    ).all()
    indexes = {name: definition for name, definition in rows}

    assert "ix_jobs_fingerprint" in indexes
    assert "ix_jobs_canonical_url" in indexes
    assert "uq_jobs_source_external_id" in indexes
    # O único de ID externo é parcial: não vale para NULL.
    assert "WHERE" in indexes["uq_jobs_source_external_id"]
