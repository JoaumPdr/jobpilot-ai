"""Testes unitários da revisão de duplicatas (camadas 3 e 4), sem banco."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from app.core.errors import ConflictError, InvalidDataError, NotFoundError
from app.models import Job
from app.schemas.dedup import DuplicateReviewLayer
from app.services.job_dedup import JobDedupService
from app.services.normalization import canonicalize_url, job_fingerprint
from tests.unit.fakes import FakeJobRepository


def _make(
    repository: FakeJobRepository,
    *,
    title: str,
    company: str = "Empresa X",
    location: str = "São Paulo",
    day: int = 1,
    **overrides: Any,
) -> Job:
    """Cria e registra uma vaga com URL/fingerprint coerentes com os campos."""
    suffix = uuid.uuid4().hex
    url = overrides.pop("url", f"https://empresa.com/vagas/{suffix}")
    job = Job(
        title=title,
        company=company,
        description="Descrição.",
        location=location,
        work_mode="remoto",
        seniority="sênior",
        source="manual",
        url=url,
        canonical_url=canonicalize_url(url),
        fingerprint=job_fingerprint(company, title, location),
        created_at=datetime(2026, 11, day, 12, tzinfo=UTC),
        is_archived=overrides.pop("is_archived", False),
        **overrides,
    )
    return repository.add(job)


def _service() -> tuple[JobDedupService, FakeJobRepository]:
    repository = FakeJobRepository()
    return JobDedupService(repository), repository


# ---------------------------------------------------------------------------
# Camada 3: fingerprint
# ---------------------------------------------------------------------------


def test_fingerprint_group_uses_oldest_as_canonical() -> None:
    service, repository = _service()
    older = _make(repository, title="Engenheira de Dados", day=1)
    newer = _make(repository, title="ENGENHEIRA DE DADOS", day=2)

    scan = service.list_groups()

    assert scan.scanned_jobs == 2
    assert scan.truncated is False
    assert len(scan.groups) == 1
    group = scan.groups[0]
    assert group.layer is DuplicateReviewLayer.FINGERPRINT
    assert group.similarity is None
    assert group.canonical_job_id == older.id
    assert [job.id for job in group.jobs] == [older.id, newer.id]


# ---------------------------------------------------------------------------
# Camada 4: similaridade textual
# ---------------------------------------------------------------------------


def test_similar_titles_in_same_company_form_similarity_group() -> None:
    service, repository = _service()
    older = _make(repository, title="Engenheiro de Dados Sênior", day=1)
    newer = _make(
        repository,
        title="Engenheiro de Dados Sr.",
        location="Remoto",
        day=2,
    )

    scan = service.list_groups()

    assert len(scan.groups) == 1
    group = scan.groups[0]
    assert group.layer is DuplicateReviewLayer.SIMILARITY
    assert group.similarity is not None
    assert group.similarity >= 85
    assert group.canonical_job_id == older.id
    assert [job.id for job in group.jobs] == [older.id, newer.id]


def test_similar_titles_in_different_companies_are_not_grouped() -> None:
    service, repository = _service()
    _make(repository, title="Engenheiro de Dados", company="Empresa X", day=1)
    _make(
        repository,
        title="Engenheiro de Dados",
        company="Empresa Y",
        location="Remoto",
        day=2,
    )

    assert service.list_groups().groups == []


def test_dissimilar_titles_in_same_company_are_not_grouped() -> None:
    service, repository = _service()
    _make(repository, title="Desenvolvedor Python", day=1)
    _make(repository, title="Designer Gráfico", location="Remoto", day=2)

    assert service.list_groups().groups == []


def test_job_is_not_reused_in_two_groups() -> None:
    service, repository = _service()
    # As duas primeiras formam o grupo de fingerprint (mesmo trio; URL difere).
    _make(repository, title="Engenheiro de Dados", day=1)
    _make(repository, title="Engenheiro de Dados", day=2)
    # Esta é parecida com a primeira, mas ela já foi agrupada acima.
    _make(repository, title="Engenheiro de Dados Sênior", location="Remoto", day=3)

    scan = service.list_groups()

    assert len(scan.groups) == 1
    assert scan.groups[0].layer is DuplicateReviewLayer.FINGERPRINT


# ---------------------------------------------------------------------------
# Universo, filtro e limites
# ---------------------------------------------------------------------------


def test_marked_duplicates_and_archived_jobs_are_ignored() -> None:
    service, repository = _service()
    original = _make(repository, title="Engenheiro de Dados", day=1)
    _make(
        repository,
        title="Engenheiro de Dados",
        location="Remoto",
        day=2,
        duplicate_of_job_id=original.id,
    )
    _make(
        repository,
        title="Engenheiro de Dados",
        location="Curitiba",
        day=3,
        is_archived=True,
    )

    scan = service.list_groups()

    assert scan.scanned_jobs == 1
    assert scan.groups == []


def test_groups_are_sorted_by_most_recent_job() -> None:
    service, repository = _service()
    _make(repository, title="Analista de Dados", day=1)
    _make(repository, title="Analista de Dados", location="Remoto", day=2)
    _make(repository, title="Engenheiro de Dados", day=5)
    _make(repository, title="Engenheiro de Dados", location="Remoto", day=6)

    scan = service.list_groups()

    assert [group.jobs[-1].title for group in scan.groups] == [
        "Engenheiro de Dados",
        "Analista de Dados",
    ]


def test_layer_filter_keeps_only_the_requested_criterion() -> None:
    service, repository = _service()
    _make(repository, title="Analista de Dados", day=1)
    _make(repository, title="Analista de Dados", day=2)
    _make(repository, title="Engenheiro de Dados Sênior", company="Empresa Y", day=3)
    _make(
        repository,
        title="Engenheiro de Dados Sr.",
        company="Empresa Y",
        location="Remoto",
        day=4,
    )

    scan = service.list_groups(layer=DuplicateReviewLayer.SIMILARITY)

    assert len(scan.groups) == 1
    assert scan.groups[0].layer is DuplicateReviewLayer.SIMILARITY
    assert scan.groups[0].jobs[0].company == "Empresa Y"


def test_limit_caps_groups_and_scan_reports_truncation() -> None:
    service, repository = _service()
    service.MAX_SCAN = 2
    _make(repository, title="Analista de Dados", day=1)
    _make(repository, title="Analista de Dados", location="Remoto", day=2)
    _make(repository, title="Engenheiro de Dados", day=3)

    scan = service.list_groups(limit=50)

    assert scan.truncated is True
    assert scan.scanned_jobs == 2
    assert len(scan.groups) == 1

    capped = service.list_groups(limit=1)
    assert len(capped.groups) == 1


# ---------------------------------------------------------------------------
# Confirmação
# ---------------------------------------------------------------------------


def _pair() -> tuple[JobDedupService, FakeJobRepository, Job, Job]:
    service, repository = _service()
    original = _make(repository, title="Engenheira de Dados", day=1)
    duplicate = _make(repository, title="Engenheira de Dados", location="Remoto", day=2)
    return service, repository, original, duplicate


def test_confirm_marks_duplicate_and_commits() -> None:
    service, repository, original, duplicate = _pair()

    result = service.confirm_duplicate(duplicate.id, original.id)

    assert result is duplicate
    assert duplicate.duplicate_of_job_id == original.id
    assert repository.commits == 1


def test_confirm_is_idempotent_for_the_same_target() -> None:
    service, repository, original, duplicate = _pair()
    service.confirm_duplicate(duplicate.id, original.id)

    service.confirm_duplicate(duplicate.id, original.id)

    assert duplicate.duplicate_of_job_id == original.id
    assert repository.commits == 1


def test_confirm_rejects_self_reference() -> None:
    service, repository, original, _ = _pair()

    with pytest.raises(InvalidDataError) as exc_info:
        service.confirm_duplicate(original.id, original.id)

    assert exc_info.value.status_code == 422
    assert repository.commits == 0


def test_confirm_missing_job_is_404() -> None:
    service, _, _, _ = _pair()

    with pytest.raises(NotFoundError):
        service.confirm_duplicate(uuid.uuid4(), uuid.uuid4())


def test_confirm_with_missing_target_is_404() -> None:
    service, _, original, _ = _pair()

    with pytest.raises(NotFoundError):
        service.confirm_duplicate(original.id, uuid.uuid4())


def test_confirm_rejects_already_marked_job() -> None:
    service, repository, original, duplicate = _pair()
    other = _make(repository, title="Outra vaga", day=3)
    service.confirm_duplicate(duplicate.id, original.id)

    with pytest.raises(ConflictError) as exc_info:
        service.confirm_duplicate(duplicate.id, other.id)

    assert exc_info.value.status_code == 409
    assert duplicate.duplicate_of_job_id == original.id


def test_confirm_rejects_chain_to_an_already_marked_job() -> None:
    service, repository, original, duplicate = _pair()
    service.confirm_duplicate(duplicate.id, original.id)
    third = _make(repository, title="Terceira vaga", day=4)

    with pytest.raises(InvalidDataError) as exc_info:
        service.confirm_duplicate(third.id, duplicate.id)

    assert exc_info.value.status_code == 422
    assert third.duplicate_of_job_id is None


# ---------------------------------------------------------------------------
# Desfazer
# ---------------------------------------------------------------------------


def test_undo_clears_mark_and_commits() -> None:
    service, repository, original, duplicate = _pair()
    service.confirm_duplicate(duplicate.id, original.id)

    service.undo_duplicate(duplicate.id)

    assert duplicate.duplicate_of_job_id is None
    assert repository.commits == 2


def test_undo_on_unmarked_job_is_invalid_data() -> None:
    service, repository, original, _ = _pair()

    with pytest.raises(InvalidDataError) as exc_info:
        service.undo_duplicate(original.id)

    assert exc_info.value.status_code == 422
    assert repository.commits == 0


def test_undo_missing_job_is_404() -> None:
    service, _, _, _ = _pair()

    with pytest.raises(NotFoundError):
        service.undo_duplicate(uuid.uuid4())
