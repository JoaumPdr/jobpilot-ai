"""Testes de API do cadastro manual de vagas."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def _payload(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "title": "Engenheira de Dados",
        "company": "Empresa X",
        "url": "https://empresa.com/vagas/123",
        "location": "São Paulo",
        "work_mode": "Remoto",
        "seniority": "Sênior",
    }
    data.update(overrides)
    return data


def _create_job(client: TestClient, **overrides: Any) -> dict[str, Any]:
    response = client.post("/jobs", json=_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def _assert_error(
    response: Any, status_code: int, error: str, with_details: bool = False
) -> dict[str, Any]:
    assert response.status_code == status_code, response.text
    body = response.json()
    assert body["error"] == error
    assert body["message"]
    assert body["request_id"] == response.headers["X-Request-ID"]
    if with_details:
        assert body["details"]
    else:
        assert "details" not in body
    return body


def test_create_job_returns_normalized_job(api_client: TestClient) -> None:
    response = api_client.post(
        "/jobs",
        json=_payload(
            title="  Engenheira   de Dados ",
            work_mode="home office",
            seniority="sr",
            url="https://Empresa.com/vagas/123/?utm_source=linkedin",
            salary_min="12000.00",
            salary_max="18000.00",
            currency="brl",
            posted_at="2026-11-10T09:00:00",
        ),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["duplicates"] == []
    job = body["job"]
    assert job["id"]
    assert job["title"] == "Engenheira de Dados"
    assert job["company"] == "Empresa X"
    assert job["location"] == "São Paulo"
    assert job["work_mode"] == "remoto"
    assert job["seniority"] == "sênior"
    assert job["source"] == "manual"
    assert job["canonical_url"] == "https://empresa.com/vagas/123"
    assert job["url"] == "https://Empresa.com/vagas/123/?utm_source=linkedin"
    assert job["fingerprint"]
    assert job["currency"] == "BRL"
    # Data sem fuso é interpretada como UTC.
    assert job["posted_at"].startswith("2026-11-10T09:00:00")
    assert job["is_archived"] is False
    assert job["duplicate_of_job_id"] is None
    assert job["collected_at"]


def test_create_job_returns_409_for_same_external_id(
    api_client: TestClient,
) -> None:
    first = _create_job(api_client, source="portal", external_id="abc-1")

    response = api_client.post(
        "/jobs",
        json=_payload(
            source="portal",
            external_id="abc-1",
            url="https://outro.com/vaga/999",
        ),
    )

    body = _assert_error(response, 409, "conflict", with_details=True)
    detail = body["details"][0]
    assert detail["layer"] == "external_id"
    assert detail["job_id"] == first["job"]["id"]


def test_create_job_returns_409_for_same_canonical_url(
    api_client: TestClient,
) -> None:
    first = _create_job(api_client)

    response = api_client.post(
        "/jobs",
        json=_payload(url="https://empresa.com/vagas/123?utm_campaign=teste"),
    )

    body = _assert_error(response, 409, "conflict", with_details=True)
    assert body["details"][0]["layer"] == "canonical_url"
    assert body["details"][0]["job_id"] == first["job"]["id"]


def test_create_job_creates_and_warns_on_probable_duplicate(
    api_client: TestClient,
) -> None:
    first = _create_job(api_client)

    response = api_client.post(
        "/jobs",
        json=_payload(
            title="ENGENHEIRA DE DADOS",
            url="https://outro.com/vagas/999",
        ),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["job"]["id"] != first["job"]["id"]
    assert body["duplicates"] == [
        {
            "job_id": first["job"]["id"],
            "title": "Engenheira de Dados",
            "company": "Empresa X",
            "source": "manual",
            "canonical_url": "https://empresa.com/vagas/123",
            "layer": "fingerprint",
        }
    ]


def test_create_job_rejects_unsupported_url_scheme(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/jobs", json=_payload(url="ftp://empresa.com/vagas/123")
    )

    body = _assert_error(response, 422, "validation_error", with_details=True)
    assert body["details"][0]["field"] == "url"


def test_create_job_rejects_inverted_salary_range(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/jobs",
        json=_payload(salary_min="20000.00", salary_max="15000.00"),
    )

    _assert_error(response, 422, "validation_error", with_details=True)


def test_create_job_rejects_invalid_currency(api_client: TestClient) -> None:
    response = api_client.post("/jobs", json=_payload(currency="reais"))

    body = _assert_error(response, 422, "validation_error", with_details=True)
    assert body["details"][0]["field"] == "currency"


def test_create_job_rejects_unknown_field(api_client: TestClient) -> None:
    response = api_client.post("/jobs", json=_payload(vaga_inexistente="x"))

    _assert_error(response, 422, "validation_error", with_details=True)
