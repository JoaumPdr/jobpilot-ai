"""Testes de API do perfil (candidato e preferências).

POR QUÊ: validar o contrato HTTP real — status, corpo, formato de erro — contra
o PostgreSQL isolado da suíte, e não apenas o serviço. Aqui também se confirma
que JSONB inválido, e-mail duplicado e recursos ausentes não vazam stack trace.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient


def _payload(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": "Ana Silva",
        "email": "ana@example.com",
        "resume_text": "Currículo em texto.",
        "headline": "Engenheira de Dados",
        "education": [
            {
                "institution": "USP",
                "degree": "Bacharelado em Computação",
                "start_date": "2018-02-01",
                "end_date": "2022-12-15",
            }
        ],
        "languages": [{"name": "Inglês", "level": "fluente"}],
    }
    data.update(overrides)
    return data


def _create(client: TestClient, **overrides: Any) -> dict[str, Any]:
    response = client.post("/candidates", json=_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def _assert_error(
    response: Any, status_code: int, error: str, with_details: bool = False
) -> None:
    assert response.status_code == status_code, response.text
    body = response.json()
    assert body["error"] == error
    assert body["message"]
    assert body["request_id"] == response.headers["X-Request-ID"]
    if with_details:
        assert body["details"]
    else:
        assert "details" not in body


# ---------------------------------------------------------------------------
# Candidato
# ---------------------------------------------------------------------------


def test_create_candidate_returns_profile(api_client: TestClient) -> None:
    body = _create(api_client, email="  ANA@Example.COM ")

    assert body["email"] == "ana@example.com"
    assert body["education"][0]["institution"] == "USP"
    assert body["languages"][0]["level"] == "fluente"
    assert body["preferences"] is None
    assert body["id"]
    assert body["created_at"] == body["updated_at"]


def test_create_candidate_rejects_duplicate_email(api_client: TestClient) -> None:
    _create(api_client)

    response = api_client.post("/candidates", json=_payload(email="ANA@example.com"))

    _assert_error(response, 409, "conflict")


def test_get_candidate_returns_preferences_after_put(
    api_client: TestClient,
) -> None:
    candidate = _create(api_client)

    put = api_client.put(
        f"/candidates/{candidate['id']}/preferences",
        json={"desired_titles": ["Engenheira de Dados"]},
    )
    assert put.status_code == 200, put.text

    response = api_client.get(f"/candidates/{candidate['id']}")

    assert response.status_code == 200
    assert response.json()["preferences"]["desired_titles"] == ["Engenheira de Dados"]


def test_get_unknown_candidate_returns_standard_404(
    api_client: TestClient,
) -> None:
    response = api_client.get(f"/candidates/{uuid.uuid4()}")

    _assert_error(response, 404, "not_found")


def test_invalid_candidate_id_returns_standard_422(
    api_client: TestClient,
) -> None:
    response = api_client.get("/candidates/nao-e-uuid")

    _assert_error(response, 422, "validation_error", with_details=True)
    assert response.json()["details"][0]["field"] == "candidate_id"


def test_patch_updates_only_sent_fields(api_client: TestClient) -> None:
    candidate = _create(api_client)

    response = api_client.patch(
        f"/candidates/{candidate['id']}",
        json={"headline": "Tech Lead"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["headline"] == "Tech Lead"
    assert body["name"] == "Ana Silva"


def test_patch_rejects_null_in_required_field(api_client: TestClient) -> None:
    candidate = _create(api_client)

    response = api_client.patch(f"/candidates/{candidate['id']}", json={"name": None})

    _assert_error(response, 422, "validation_error", with_details=True)


def test_patch_rejects_email_of_another_candidate(
    api_client: TestClient,
) -> None:
    _create(api_client)
    other = _create(api_client, name="Bruno", email="bruno@example.com")

    response = api_client.patch(
        f"/candidates/{other['id']}", json={"email": "ANA@example.com"}
    )

    _assert_error(response, 409, "conflict")


def test_create_rejects_invalid_education_jsonb(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/candidates",
        json=_payload(
            education=[
                {
                    "institution": "USP",
                    "degree": "Bacharelado",
                    "start_date": "2022-01-01",
                    "end_date": "2021-01-01",
                }
            ]
        ),
    )

    _assert_error(response, 422, "validation_error", with_details=True)
    assert response.json()["details"][0]["field"].startswith("education")


def test_create_rejects_unknown_education_field(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/candidates",
        json=_payload(
            education=[{"institution": "USP", "degree": "Bacharelado", "curso": "X"}]
        ),
    )

    _assert_error(response, 422, "validation_error", with_details=True)


def test_create_rejects_invalid_language_level(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/candidates",
        json=_payload(languages=[{"name": "Inglês", "level": "expert"}]),
    )

    _assert_error(response, 422, "validation_error", with_details=True)
    assert response.json()["details"][0]["field"].startswith("languages")


def test_delete_candidate_removes_dependents(api_client: TestClient) -> None:
    candidate = _create(api_client)
    api_client.put(
        f"/candidates/{candidate['id']}/preferences",
        json={"desired_titles": ["Engenheira de Dados"]},
    )

    response = api_client.delete(f"/candidates/{candidate['id']}")

    assert response.status_code == 204
    assert response.content == b""
    _assert_error(api_client.get(f"/candidates/{candidate['id']}"), 404, "not_found")


def test_delete_unknown_candidate_returns_404(api_client: TestClient) -> None:
    response = api_client.delete(f"/candidates/{uuid.uuid4()}")

    _assert_error(response, 404, "not_found")


# ---------------------------------------------------------------------------
# Preferências
# ---------------------------------------------------------------------------


def test_get_preferences_before_creation_returns_404(
    api_client: TestClient,
) -> None:
    candidate = _create(api_client)

    response = api_client.get(f"/candidates/{candidate['id']}/preferences")

    _assert_error(response, 404, "not_found")


def test_put_preferences_is_idempotent(api_client: TestClient) -> None:
    candidate = _create(api_client)
    url = f"/candidates/{candidate['id']}/preferences"

    first = api_client.put(
        url,
        json={
            "desired_titles": ["Engenheira de Dados"],
            "locations": ["São Paulo"],
            "work_modes": ["remoto"],
            "seniority_levels": ["pleno"],
            "min_salary": "12000.00",
            "knockout_rules": {"exclude_companies": ["Empresa X"]},
        },
    )
    second = api_client.put(url, json={"desired_titles": ["Tech Lead"]})

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json()["min_salary"] is None
    assert second.json()["desired_titles"] == ["Tech Lead"]
    assert second.json()["id"] == first.json()["id"]

    fetched = api_client.get(url)
    assert fetched.status_code == 200
    assert fetched.json()["knockout_rules"] == {}


def test_put_preferences_normalizes_lists(api_client: TestClient) -> None:
    candidate = _create(api_client)

    response = api_client.put(
        f"/candidates/{candidate['id']}/preferences",
        json={"desired_titles": ["  Engenheira de Dados  ", "", "  "]},
    )

    assert response.status_code == 200, response.text
    assert response.json()["desired_titles"] == ["Engenheira de Dados"]


def test_put_preferences_rejects_negative_salary(
    api_client: TestClient,
) -> None:
    candidate = _create(api_client)

    response = api_client.put(
        f"/candidates/{candidate['id']}/preferences",
        json={"min_salary": "-1.00"},
    )

    _assert_error(response, 422, "validation_error", with_details=True)


def test_put_preferences_unknown_candidate_returns_404(
    api_client: TestClient,
) -> None:
    response = api_client.put(
        f"/candidates/{uuid.uuid4()}/preferences", json={"desired_titles": ["X"]}
    )

    _assert_error(response, 404, "not_found")
