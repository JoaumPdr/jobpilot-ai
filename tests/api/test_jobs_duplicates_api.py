"""Testes de API da revisão de duplicatas (F1-T07)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text


def _payload(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "title": "Engenheira de Dados",
        "company": "Empresa X",
        "url": "https://empresa.com/vagas/1",
        "location": "São Paulo",
        "work_mode": "Remoto",
        "seniority": "Sênior",
    }
    data.update(overrides)
    return data


def _create_job(client: TestClient, **overrides: Any) -> dict[str, Any]:
    response = client.post("/jobs", json=_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()["job"]


def _groups(client: TestClient, **params: Any) -> dict[str, Any]:
    response = client.get("/jobs/duplicates", params=params)
    assert response.status_code == 200, response.text
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


def test_list_fingerprint_group(api_client: TestClient) -> None:
    first = _create_job(api_client)
    second = _create_job(
        api_client,
        title="ENGENHEIRA DE DADOS",
        url="https://empresa.com/vagas/2",
    )

    body = _groups(api_client)

    assert body["scanned_jobs"] == 2
    assert body["truncated"] is False
    assert len(body["groups"]) == 1
    group = body["groups"][0]
    assert group["layer"] == "fingerprint"
    assert group["similarity"] is None
    assert group["canonical_job_id"] == first["id"]
    assert [job["id"] for job in group["jobs"]] == [first["id"], second["id"]]
    # Retrato da vaga traz o necessário para decidir, sem descrição.
    summary = group["jobs"][0]
    assert set(summary) == {
        "id",
        "title",
        "company",
        "location",
        "source",
        "canonical_url",
        "posted_at",
        "created_at",
        "duplicate_of_job_id",
    }


def test_list_similarity_group(api_client: TestClient) -> None:
    first = _create_job(api_client, title="Engenheiro de Dados Sênior")
    second = _create_job(
        api_client,
        title="Engenheiro de Dados Sr.",
        url="https://empresa.com/vagas/2",
        location="Remoto",
    )

    body = _groups(api_client, layer="similarity")

    assert len(body["groups"]) == 1
    group = body["groups"][0]
    assert group["layer"] == "similarity"
    assert group["similarity"] >= 85
    assert group["canonical_job_id"] == first["id"]
    assert [job["id"] for job in group["jobs"]] == [first["id"], second["id"]]

    # O filtro pela outra camada não devolve este grupo.
    assert _groups(api_client, layer="fingerprint")["groups"] == []


def test_confirm_hides_group_and_undo_restores_it(
    api_client: TestClient, test_engine: Engine
) -> None:
    first = _create_job(api_client)
    second = _create_job(
        api_client,
        title="ENGENHEIRA DE DADOS",
        url="https://empresa.com/vagas/2",
    )

    response = api_client.post(
        f"/jobs/{second['id']}/duplicate",
        json={"duplicate_of_job_id": first["id"]},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == second["id"]
    assert body["duplicate_of_job_id"] == first["id"]
    # Nada é apagado: a vaga continua existindo.
    assert body["title"] == "ENGENHEIRA DE DADOS"

    with test_engine.connect() as connection:
        stored = connection.execute(
            text("SELECT duplicate_of_job_id FROM jobs WHERE id = :id"),
            {"id": second["id"]},
        ).scalar_one()
    assert str(stored) == first["id"]

    after = _groups(api_client)
    assert after["groups"] == []
    assert after["scanned_jobs"] == 1

    undo = api_client.delete(f"/jobs/{second['id']}/duplicate")

    assert undo.status_code == 204
    assert undo.content == b""
    restored = _groups(api_client)
    assert len(restored["groups"]) == 1
    assert restored["groups"][0]["canonical_job_id"] == first["id"]


def test_confirm_is_idempotent(api_client: TestClient) -> None:
    first = _create_job(api_client)
    second = _create_job(
        api_client,
        title="ENGENHEIRA DE DADOS",
        url="https://empresa.com/vagas/2",
    )
    payload = {"duplicate_of_job_id": first["id"]}

    first_call = api_client.post(f"/jobs/{second['id']}/duplicate", json=payload)
    second_call = api_client.post(f"/jobs/{second['id']}/duplicate", json=payload)

    assert first_call.status_code == 200
    assert second_call.status_code == 200
    assert second_call.json()["duplicate_of_job_id"] == first["id"]


def test_confirm_rejects_self_reference(api_client: TestClient) -> None:
    job = _create_job(api_client)

    response = api_client.post(
        f"/jobs/{job['id']}/duplicate",
        json={"duplicate_of_job_id": job["id"]},
    )

    body = _assert_error(response, 422, "invalid_data", with_details=True)
    assert body["details"][0]["field"] == "duplicate_of_job_id"


def test_confirm_missing_jobs_return_404(api_client: TestClient) -> None:
    job = _create_job(api_client)
    missing = "0b7f5c9e-3a4d-4e6f-8a1b-2c3d4e5f6a7b"

    missing_job = api_client.post(
        f"/jobs/{missing}/duplicate",
        json={"duplicate_of_job_id": job["id"]},
    )
    missing_target = api_client.post(
        f"/jobs/{job['id']}/duplicate",
        json={"duplicate_of_job_id": missing},
    )

    _assert_error(missing_job, 404, "not_found", with_details=True)
    _assert_error(missing_target, 404, "not_found", with_details=True)


def test_confirm_rejects_reassigning_and_chains(api_client: TestClient) -> None:
    first = _create_job(api_client)
    second = _create_job(
        api_client,
        title="ENGENHEIRA DE DADOS",
        url="https://empresa.com/vagas/2",
    )
    third = _create_job(
        api_client,
        title="Pessoa Desenvolvedora Backend",
        url="https://empresa.com/vagas/3",
    )
    assert (
        api_client.post(
            f"/jobs/{second['id']}/duplicate",
            json={"duplicate_of_job_id": first["id"]},
        ).status_code
        == 200
    )

    reassign = api_client.post(
        f"/jobs/{second['id']}/duplicate",
        json={"duplicate_of_job_id": third["id"]},
    )
    chain = api_client.post(
        f"/jobs/{third['id']}/duplicate",
        json={"duplicate_of_job_id": second["id"]},
    )

    _assert_error(reassign, 409, "conflict", with_details=True)
    _assert_error(chain, 422, "invalid_data", with_details=True)


def test_undo_without_confirmation_is_invalid_data(api_client: TestClient) -> None:
    job = _create_job(api_client)

    response = api_client.delete(f"/jobs/{job['id']}/duplicate")

    body = _assert_error(response, 422, "invalid_data", with_details=True)
    assert body["details"][0]["field"] == "duplicate_of_job_id"


def test_list_validates_limit_and_layer(api_client: TestClient) -> None:
    invalid_limit = api_client.get("/jobs/duplicates", params={"limit": 0})
    invalid_layer = api_client.get("/jobs/duplicates", params={"layer": "external_id"})

    _assert_error(invalid_limit, 422, "validation_error", with_details=True)
    _assert_error(invalid_layer, 422, "validation_error", with_details=True)
