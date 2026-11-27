"""Testes unitários do serviço de vagas (sem banco)."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError
from app.schemas.jobs import JobCreate
from app.services.jobs import JobService
from tests.unit.fakes import FakeJobRepository


def _payload(**overrides: Any) -> JobCreate:
    data: dict[str, Any] = {
        "title": "Engenheira de Dados",
        "company": "Empresa X",
        "url": "https://empresa.com/vagas/123",
        "location": "São Paulo",
        "work_mode": "Remoto",
        "seniority": "Sênior",
    }
    data.update(overrides)
    return JobCreate(**data)


def _service() -> tuple[JobService, FakeJobRepository]:
    repository = FakeJobRepository()
    return JobService(repository), repository


# ---------------------------------------------------------------------------
# Normalização
# ---------------------------------------------------------------------------


def test_create_manual_stores_normalized_job() -> None:
    service, repository = _service()

    job, duplicates = service.create_manual(
        _payload(
            title="  Engenheira   de Dados ",
            company=" Empresa X ",
            location="  São   Paulo ",
            work_mode="home office",
            seniority="sr",
            url="https://Empresa.com/vagas/123/?utm_source=linkedin#topo",
            description="  Texto livre.  ",
        )
    )

    assert duplicates == []
    assert repository.commits == 1
    # Exibição preserva acentos e caixa, mas sem espaços sobrando.
    assert job.title == "Engenheira de Dados"
    assert job.company == "Empresa X"
    assert job.location == "São Paulo"
    # Enums recebem os valores internos do banco.
    assert job.work_mode == "remoto"
    assert job.seniority == "sênior"
    assert job.source == "manual"
    assert job.description == "Texto livre."
    # URL exibida intacta; a canônica perde rastreio, barra final e fragmento.
    assert job.url == "https://Empresa.com/vagas/123/?utm_source=linkedin#topo"
    assert job.canonical_url == "https://empresa.com/vagas/123"
    assert len(job.fingerprint) == 64


def test_unknown_work_mode_and_seniority_fall_back_to_desconhecido() -> None:
    service, _ = _service()

    job, _ = service.create_manual(_payload(work_mode="qualquer", seniority=None))

    assert job.work_mode == "desconhecido"
    assert job.seniority == "desconhecido"


def test_missing_location_is_none() -> None:
    service, _ = _service()

    job, _ = service.create_manual(_payload(location="   "))

    assert job.location is None


# ---------------------------------------------------------------------------
# Deduplicação
# ---------------------------------------------------------------------------


def test_same_source_and_external_id_is_conflict() -> None:
    service, repository = _service()
    first, _ = service.create_manual(_payload(source="portal", external_id="abc-1"))

    with pytest.raises(ConflictError) as exc_info:
        service.create_manual(
            _payload(
                source="portal",
                external_id="abc-1",
                url="https://outro.com/vaga/999",
            )
        )

    error = exc_info.value
    assert error.status_code == 409
    assert "identificador externo" in error.message
    assert error.details == [
        {
            "job_id": str(first.id),
            "layer": "external_id",
            "title": first.title,
            "company": first.company,
            "source": "portal",
            "canonical_url": first.canonical_url,
        }
    ]
    # Nada foi commitado na tentativa recusada.
    assert repository.commits == 1


def test_same_external_id_in_another_source_is_allowed() -> None:
    service, _ = _service()
    service.create_manual(_payload(source="portal-a", external_id="abc-1"))

    job, _ = service.create_manual(
        _payload(
            source="portal-b",
            external_id="abc-1",
            url="https://outro.com/vaga/999",
        )
    )

    assert job.external_id == "abc-1"


def test_same_canonical_url_is_conflict() -> None:
    service, _ = _service()
    first, _ = service.create_manual(_payload())

    with pytest.raises(ConflictError) as exc_info:
        service.create_manual(
            _payload(url="https://empresa.com/vagas/123?utm_campaign=teste")
        )

    assert exc_info.value.details is not None
    assert exc_info.value.details[0]["layer"] == "canonical_url"
    assert exc_info.value.details[0]["job_id"] == str(first.id)


def test_same_fingerprint_is_created_with_warning() -> None:
    service, repository = _service()
    first, _ = service.create_manual(_payload())

    job, duplicates = service.create_manual(
        _payload(
            # Grafia diferente, mesma empresa/título/local: fingerprint igual.
            title="ENGENHEIRA DE DADOS",
            url="https://outro.com/vagas/999",
        )
    )

    assert job.id != first.id
    assert repository.commits == 2
    assert duplicates == [first]


def test_different_location_does_not_warn() -> None:
    service, _ = _service()
    service.create_manual(_payload())

    _, duplicates = service.create_manual(
        _payload(url="https://outro.com/vagas/999", location="Rio de Janeiro")
    )

    assert duplicates == []


def test_integrity_error_becomes_conflict_and_rolls_back() -> None:
    service, repository = _service()
    repository.commit_error = IntegrityError("INSERT", {}, Exception("duplicado"))

    with pytest.raises(ConflictError) as exc_info:
        service.create_manual(_payload(source="portal", external_id="abc-1"))

    assert repository.rollbacks == 1
    assert exc_info.value.details is not None
    assert exc_info.value.details[0]["layer"] == "external_id"
