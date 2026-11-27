"""Testes unitários da importação CSV (sem banco)."""

from __future__ import annotations

import csv
import io
from datetime import UTC
from typing import Any

import pytest

from app.core.errors import InvalidDataError
from app.services.job_import import JobImportService
from app.services.jobs import JobService
from tests.unit.fakes import FakeImportBatchRepository, FakeJobRepository

HEADER = (
    "title,company,description,url,location,work_mode,seniority,source,"
    "external_id,salary_min,salary_max,currency,posted_at"
)


def _row(**overrides: Any) -> str:
    """Monta uma linha com as 13 colunas do modelo, na ordem do cabeçalho."""
    values: dict[str, str] = {
        "title": "Engenheira de Dados",
        "company": "Empresa X",
        "description": "Descrição A",
        "url": "https://empresa.com/vagas/1",
        "location": "São Paulo",
        "work_mode": "home office",
        "seniority": "Sênior",
        "source": "portal-a",
        "external_id": "ext-1",
        "salary_min": "12000.00",
        "salary_max": "18000.00",
        "currency": "brl",
        "posted_at": "2026-11-10T09:00:00Z",
    }
    values.update(overrides)
    # `csv.writer` cuida de aspas quando o valor tem vírgula (preços em pt-BR).
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="").writerow(values.values())
    return buffer.getvalue()


def _csv(*rows: str) -> bytes:
    return ("\n".join((HEADER, *rows)) + "\n").encode("utf-8")


def _service() -> tuple[JobImportService, FakeJobRepository, FakeImportBatchRepository]:
    jobs = FakeJobRepository()
    batches = FakeImportBatchRepository()
    return (
        JobImportService(JobService(jobs), jobs, batches),
        jobs,
        batches,
    )


ROW_A = _row()
ROW_B = _row(
    title="Analista de Dados",
    company="Empresa Y",
    description="Descrição B",
    url="https://empresa.com/vagas/2",
    location="Remoto",
    work_mode="remoto",
    seniority="Pleno",
    external_id="ext-2",
    salary_min="8000.00",
    salary_max="10000.00",
    currency="BRL",
    posted_at="2026-11-11",
)


# ---------------------------------------------------------------------------
# Lote válido
# ---------------------------------------------------------------------------


def test_import_valid_csv_fills_batch_and_jobs() -> None:
    service, jobs, batches = _service()

    batch = service.import_csv(
        filename="vagas.csv", content=_csv(ROW_A, ROW_B), source="portal-x"
    )

    assert batch.total_rows == 2
    assert batch.inserted == 2
    assert batch.duplicates == 0
    assert batch.rejected == 0
    assert batch.errors == []
    assert batch.filename == "vagas.csv"
    assert batch.kind == "csv"
    assert batch.finished_at is not None
    # `source` da linha vence o fallback do formulário.
    assert batch.source == "portal-x"
    assert batches.commits == 1

    inserted = list(jobs.items.values())
    assert {job.source for job in inserted} == {"portal-a"}
    assert all(job.import_batch_id == batch.id for job in inserted)

    first = next(job for job in inserted if job.title == "Engenheira de Dados")
    assert first.work_mode == "remoto"
    assert first.seniority == "sênior"
    assert first.currency == "BRL"
    assert first.canonical_url == "https://empresa.com/vagas/1"
    assert first.posted_at is not None
    assert first.posted_at.tzinfo == UTC

    second = next(job for job in inserted if job.title == "Analista de Dados")
    # Data sem hora/fuso é interpretada como UTC pelo schema.
    assert second.posted_at is not None
    assert second.posted_at.tzinfo == UTC


def test_source_falls_back_to_form_then_csv() -> None:
    row_without_source = _row(
        url="https://empresa.com/vagas/3",
        location="Remoto",
        work_mode="",
        seniority="",
        source="",
        external_id="",
        salary_min="",
        salary_max="",
        currency="",
        posted_at="",
    )

    service, jobs, _ = _service()
    batch = service.import_csv(
        filename="vagas.csv", content=_csv(row_without_source), source="planilha"
    )

    assert batch.inserted == 1
    assert next(iter(jobs.items.values())).source == "planilha"

    service2, jobs2, _ = _service()
    batch2 = service2.import_csv(filename="vagas.csv", content=_csv(row_without_source))

    assert batch2.inserted == 1
    assert batch2.source == "csv"
    assert next(iter(jobs2.items.values())).source == "csv"


# ---------------------------------------------------------------------------
# Linha inválida
# ---------------------------------------------------------------------------


def test_invalid_row_does_not_abort_batch() -> None:
    service, jobs, _ = _service()
    bad_row = _row(
        title="Vaga quebrada",
        url="ftp://empresa.com/vagas/9",
        source="portal-a",
        external_id="",
    )

    batch = service.import_csv(
        filename="vagas.csv", content=_csv(ROW_A, bad_row, ROW_B)
    )

    assert batch.total_rows == 3
    assert batch.inserted == 2
    assert batch.rejected == 1
    assert batch.duplicates == 0
    assert len(jobs.items) == 2
    error = batch.errors[0]
    assert error["row"] == 3  # header = 1, ROW_A = 2, bad_row = 3
    assert error["field"] == "url"
    assert "URL inválida" in error["message"]


def test_missing_required_field_is_reported_per_line() -> None:
    service, jobs, _ = _service()
    row_without_title = _row(title="")

    batch = service.import_csv(filename="vagas.csv", content=_csv(row_without_title))

    assert batch.inserted == 0
    assert batch.rejected == 1
    assert jobs.items == {}
    assert batch.errors[0]["field"] == "title"
    assert "obrigatória" in batch.errors[0]["message"]


def test_invalid_salary_is_rejected_with_field_name() -> None:
    service, _, _ = _service()
    row_bad_salary = _row(salary_min="12.000,00", salary_max="")

    batch = service.import_csv(filename="vagas.csv", content=_csv(row_bad_salary))

    assert batch.inserted == 0
    assert batch.rejected == 1
    assert batch.errors[0]["field"] == "salary_min"
    assert "salary_min" in batch.errors[0]["message"]


# ---------------------------------------------------------------------------
# Deduplicação e idempotência
# ---------------------------------------------------------------------------


def test_duplicate_url_inside_same_file_counts_once() -> None:
    service, jobs, _ = _service()
    repeated = _row(title="Engenheira II", external_id="ext-9")

    batch = service.import_csv(filename="vagas.csv", content=_csv(ROW_A, repeated))

    assert batch.total_rows == 2
    assert batch.inserted == 1
    assert batch.duplicates == 1
    assert batch.rejected == 0
    assert len(jobs.items) == 1


def test_reimporting_same_file_inserts_nothing() -> None:
    service, jobs, _ = _service()
    content = _csv(ROW_A, ROW_B)

    first = service.import_csv(filename="vagas.csv", content=content)
    second = service.import_csv(filename="vagas.csv", content=content)

    assert first.inserted == 2
    assert second.inserted == 0
    assert second.duplicates == 2
    assert second.rejected == 0
    assert len(jobs.items) == 2


# ---------------------------------------------------------------------------
# Arquivo inteiro inválido
# ---------------------------------------------------------------------------


def test_missing_required_column_rejects_file_without_batch() -> None:
    service, _, batches = _service()
    content = b"title,company,url\nDev,Empresa,https://empresa.com/vagas/6\n"

    with pytest.raises(InvalidDataError) as exc_info:
        service.import_csv(filename="vagas.csv", content=content)

    assert exc_info.value.status_code == 422
    assert exc_info.value.details is not None
    assert "description" in exc_info.value.details[0]["message"]
    assert batches.items == {}
    assert batches.commits == 0


def test_empty_file_is_rejected() -> None:
    service, _, batches = _service()

    with pytest.raises(InvalidDataError):
        service.import_csv(filename="vazio.csv", content=b"")

    assert batches.items == {}


def test_non_utf8_file_is_rejected() -> None:
    service, _, _ = _service()
    content = (
        "title,company,description,url\nVaga,Empresa,Descrição,https://x.com/1"
    ).encode("latin-1")

    with pytest.raises(InvalidDataError) as exc_info:
        service.import_csv(filename="latin1.csv", content=content)

    assert "UTF-8" in exc_info.value.message


def test_file_above_size_limit_is_rejected() -> None:
    service, _, _ = _service()

    with pytest.raises(InvalidDataError) as exc_info:
        service.import_csv(filename="grande.csv", content=b"a" * (5 * 1024 * 1024 + 1))

    assert "5 MB" in exc_info.value.message


def test_header_names_are_case_and_space_insensitive() -> None:
    service, jobs, _ = _service()
    content = (
        " Title , COMPANY ,description,URL\n"
        "Dev,Empresa,Descrição,https://empresa.com/vagas/7\n"
    ).encode()

    batch = service.import_csv(filename="vagas.csv", content=content)

    assert batch.inserted == 1
    assert next(iter(jobs.items.values())).title == "Dev"
