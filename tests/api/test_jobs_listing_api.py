"""Contrato e desempenho da listagem de vagas em PostgreSQL."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, insert
from sqlalchemy.orm import Session

from app.models import Job

CREATED_AT = datetime(2026, 11, 19, tzinfo=UTC)
POSTED_AT = datetime(2026, 11, 18, 12, tzinfo=UTC)


def _job(number: int, **overrides: Any) -> dict[str, Any]:
    url = f"https://example.com/jobs/{number}"
    return {
        "id": UUID(int=number),
        "title": "Engenheira de dados",
        "company": "Empresa X",
        "description": "Atuação com ETL e 100% remoto.",
        "location": "São Paulo, SP",
        "work_mode": "remoto",
        "seniority": "sênior",
        "source": "portal",
        "posted_at": POSTED_AT,
        "created_at": CREATED_AT,
        "url": url,
        "canonical_url": url,
        "fingerprint": str(number),
        **overrides,
    }


def _seed(engine: Engine, jobs: list[dict[str, Any]]) -> None:
    with Session(engine) as session:
        session.execute(insert(Job), jobs)
        session.commit()


def test_list_jobs_combines_filters_with_inclusive_time_bounds(
    api_client: TestClient, test_engine: Engine
) -> None:
    _seed(
        test_engine,
        [
            _job(1),
            _job(2, title="Analista", description=None),
            _job(3, work_mode="híbrido"),
            _job(4, location=None),
            _job(5, seniority="pleno"),
            _job(6, source="manual"),
            _job(7, posted_at=datetime(2026, 11, 18, 11, tzinfo=UTC)),
            _job(8, posted_at=datetime(2026, 11, 18, 13, tzinfo=UTC)),
            _job(9, posted_at=None),
            _job(10, is_archived=True),
            _job(11, duplicate_of_job_id=UUID(int=1)),
        ],
    )
    response = api_client.get(
        "/jobs",
        params={
            "q": " ENGENHEIRA ",
            "work_mode": "remoto",
            "location": "são paulo",
            "seniority": "sênior",
            "source": "portal",
            "posted_from": "2026-11-18T09:00:00-03:00",
            "posted_to": "2026-11-18T12:00:00Z",
        },
    )

    assert response.status_code == 200, response.text
    page = response.json()
    assert [item["id"] for item in page["items"]] == [str(UUID(int=1))]
    assert page["limit"] == 50
    assert page["offset"] == 0
    assert page["has_more"] is False


@pytest.mark.parametrize(
    ("query", "expected"),
    [("empresa x", True), ("ETL", True), ("100%", True), ("_", False)],
)
def test_list_jobs_searches_company_and_description_and_escapes_wildcards(
    api_client: TestClient, test_engine: Engine, query: str, expected: bool
) -> None:
    _seed(test_engine, [_job(1)])
    response = api_client.get("/jobs", params={"q": query})
    assert response.status_code == 200, response.text
    assert bool(response.json()["items"]) is expected


@pytest.mark.parametrize(
    ("include_archived", "include_duplicates", "expected"),
    [
        (False, False, [1]),
        (True, False, [2, 1]),
        (False, True, [3, 1]),
        (True, True, [4, 3, 2, 1]),
    ],
)
def test_list_jobs_has_independent_visibility_filters(
    api_client: TestClient,
    test_engine: Engine,
    include_archived: bool,
    include_duplicates: bool,
    expected: list[int],
) -> None:
    _seed(
        test_engine,
        [
            _job(1),
            _job(2, is_archived=True),
            _job(3, duplicate_of_job_id=UUID(int=1)),
            _job(4, is_archived=True, duplicate_of_job_id=UUID(int=1)),
        ],
    )
    response = api_client.get(
        "/jobs",
        params={
            "include_archived": str(include_archived).lower(),
            "include_duplicates": str(include_duplicates).lower(),
        },
    )
    assert response.status_code == 200, response.text
    assert [item["id"] for item in response.json()["items"]] == [
        str(UUID(int=number)) for number in expected
    ]


def test_list_jobs_paginates_with_stable_order_and_empty_page(
    api_client: TestClient, test_engine: Engine
) -> None:
    newer = datetime(2026, 11, 20, tzinfo=UTC)
    _seed(test_engine, [_job(1, created_at=newer), _job(2), _job(3), _job(4)])
    for offset, ids, has_more in [
        (0, [1, 4], True),
        (2, [3, 2], False),
        (4, [], False),
    ]:
        response = api_client.get("/jobs", params={"limit": 2, "offset": offset})
        assert response.status_code == 200, response.text
        page = response.json()
        assert [item["id"] for item in page["items"]] == [
            str(UUID(int=number)) for number in ids
        ]
        assert page["limit"] == 2
        assert page["offset"] == offset
        assert page["has_more"] is has_more


@pytest.mark.parametrize(
    "params",
    [
        {"limit": "101"},
        {"limit": "0"},
        {"offset": "-1"},
        {"offset": str(2**63)},
        {"work_mode": "inválido"},
        {"seniority": "inválido"},
        {"q": "  "},
        {"include_duplicates": "não"},
        {"posted_from": "2026-11-19T00:00:00"},
        {"posted_from": "2026-11-19T00:00:00Z", "posted_to": "2026-11-18T00:00:00Z"},
        {"status": "salva"},
    ],
)
def test_list_jobs_rejects_invalid_query(
    api_client: TestClient, params: dict[str, str]
) -> None:
    response = api_client.get("/jobs", params=params)
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["error"] == "validation_error"
    assert body["details"]
    assert body["request_id"] == response.headers["X-Request-ID"]


def test_list_jobs_under_500_ms_with_10k_jobs(
    api_client: TestClient, test_engine: Engine
) -> None:
    _seed(test_engine, [_job(number) for number in range(1, 10_001)])
    for params in ({}, {"q": "dados", "work_mode": "remoto", "offset": 9_900}):
        start = perf_counter()
        response = api_client.get("/jobs", params=params)
        elapsed = perf_counter() - start
        assert response.status_code == 200, response.text
        assert len(response.json()["items"]) == 50
        assert response.json()["has_more"] is True
        assert elapsed < 0.5, f"Listagem levou {elapsed:.3f} s com 10 mil vagas."
