"""Testes de API das experiências profissionais do candidato."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient


def _create_candidate(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/candidates",
        json={
            "name": "Ana Silva",
            "email": "ana@example.com",
            "resume_text": "Currículo em texto.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _payload(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "company": "Empresa X",
        "role": "Engenheira de Dados",
        "start_date": "2020-01-01",
        "end_date": "2022-12-31",
        "description": "Construção de pipelines.",
        "skills_used": ["Python", "SQL"],
        "years": 3,
    }
    data.update(overrides)
    return data


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


def test_create_experience(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)

    response = api_client.post(
        f"/candidates/{candidate['id']}/experiences", json=_payload()
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["company"] == "Empresa X"
    assert body["skills_used"] == ["Python", "SQL"]
    assert body["years"] == 3


def test_create_experience_rejects_end_before_start(
    api_client: TestClient,
) -> None:
    candidate = _create_candidate(api_client)

    response = api_client.post(
        f"/candidates/{candidate['id']}/experiences",
        json=_payload(start_date="2022-01-01", end_date="2021-01-01"),
    )

    _assert_error(response, 422, "validation_error", with_details=True)


def test_create_experience_rejects_negative_years(
    api_client: TestClient,
) -> None:
    candidate = _create_candidate(api_client)

    response = api_client.post(
        f"/candidates/{candidate['id']}/experiences", json=_payload(years=-1)
    )

    _assert_error(response, 422, "validation_error", with_details=True)


def test_create_experience_unknown_candidate_returns_404(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        f"/candidates/{uuid.uuid4()}/experiences", json=_payload()
    )

    _assert_error(response, 404, "not_found")


def test_list_experiences_and_candidate_detail(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)
    api_client.post(f"/candidates/{candidate['id']}/experiences", json=_payload())

    listed = api_client.get(f"/candidates/{candidate['id']}/experiences")
    detail = api_client.get(f"/candidates/{candidate['id']}")

    assert listed.status_code == 200
    assert [item["company"] for item in listed.json()] == ["Empresa X"]
    assert [item["company"] for item in detail.json()["experiences"]] == ["Empresa X"]


def test_patch_experience_updates_only_sent_fields(
    api_client: TestClient,
) -> None:
    candidate = _create_candidate(api_client)
    experience = api_client.post(
        f"/candidates/{candidate['id']}/experiences", json=_payload()
    ).json()
    url = f"/candidates/{candidate['id']}/experiences/{experience['id']}"

    response = api_client.patch(url, json={"role": "Tech Lead"})

    assert response.status_code == 200, response.text
    assert response.json()["role"] == "Tech Lead"
    assert response.json()["company"] == "Empresa X"


def test_patch_experience_rejects_partial_invalid_date_range(
    api_client: TestClient,
) -> None:
    candidate = _create_candidate(api_client)
    experience = api_client.post(
        f"/candidates/{candidate['id']}/experiences", json=_payload()
    ).json()
    url = f"/candidates/{candidate['id']}/experiences/{experience['id']}"

    response = api_client.patch(url, json={"start_date": "2023-01-01"})

    _assert_error(response, 422, "invalid_data")


def test_patch_experience_accepts_open_end_date(
    api_client: TestClient,
) -> None:
    candidate = _create_candidate(api_client)
    experience = api_client.post(
        f"/candidates/{candidate['id']}/experiences", json=_payload()
    ).json()
    url = f"/candidates/{candidate['id']}/experiences/{experience['id']}"

    response = api_client.patch(url, json={"end_date": None})

    assert response.status_code == 200, response.text
    assert response.json()["end_date"] is None


def test_patch_experience_rejects_null_required_field(
    api_client: TestClient,
) -> None:
    candidate = _create_candidate(api_client)
    experience = api_client.post(
        f"/candidates/{candidate['id']}/experiences", json=_payload()
    ).json()

    response = api_client.patch(
        f"/candidates/{candidate['id']}/experiences/{experience['id']}",
        json={"company": None},
    )

    _assert_error(response, 422, "validation_error", with_details=True)


def test_patch_unknown_experience_returns_404(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)

    response = api_client.patch(
        f"/candidates/{candidate['id']}/experiences/{uuid.uuid4()}",
        json={"role": "Tech Lead"},
    )

    _assert_error(response, 404, "not_found")


def test_delete_experience(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)
    experience = api_client.post(
        f"/candidates/{candidate['id']}/experiences", json=_payload()
    ).json()
    url = f"/candidates/{candidate['id']}/experiences/{experience['id']}"

    response = api_client.delete(url)

    assert response.status_code == 204
    assert api_client.get(f"/candidates/{candidate['id']}/experiences").json() == []


def test_delete_unknown_experience_returns_404(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)

    response = api_client.delete(
        f"/candidates/{candidate['id']}/experiences/{uuid.uuid4()}"
    )

    _assert_error(response, 404, "not_found")
