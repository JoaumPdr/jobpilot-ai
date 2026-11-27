"""Testes de API do catálogo de habilidades e do vínculo candidato/skill."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient


def _create_candidate(client: TestClient, name: str = "Ana Silva") -> dict[str, Any]:
    response = client.post(
        "/candidates",
        json={
            "name": name,
            "email": f"{name.split()[0].lower()}@example.com",
            "resume_text": "Currículo em texto.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_skill(client: TestClient, name: str = "Python") -> dict[str, Any]:
    response = client.post("/skills", json={"canonical_name": name})
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
# Catálogo
# ---------------------------------------------------------------------------


def test_create_skill_returns_catalog_entry(api_client: TestClient) -> None:
    response = api_client.post(
        "/skills",
        json={
            "canonical_name": "  Python  ",
            "category": "linguagem",
            "aliases": ["py", " python3 "],
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["canonical_name"] == "Python"
    assert body["aliases"] == ["py", "python3"]
    assert body["id"]


def test_create_skill_rejects_duplicate_name_case_insensitive(
    api_client: TestClient,
) -> None:
    _create_skill(api_client, "Python")

    response = api_client.post("/skills", json={"canonical_name": "python"})

    _assert_error(response, 409, "conflict")


def test_list_skills_filters_by_name(api_client: TestClient) -> None:
    _create_skill(api_client, "Python")
    _create_skill(api_client, "SQL")
    _create_skill(api_client, "PySpark")

    response = api_client.get("/skills", params={"q": "py"})

    assert response.status_code == 200
    assert [skill["canonical_name"] for skill in response.json()] == [
        "PySpark",
        "Python",
    ]


# ---------------------------------------------------------------------------
# Vínculo candidato/skill
# ---------------------------------------------------------------------------


def test_add_skill_by_canonical_name_creates_catalog_entry(
    api_client: TestClient,
) -> None:
    candidate = _create_candidate(api_client)

    response = api_client.post(
        f"/candidates/{candidate['id']}/skills",
        json={"canonical_name": "Python", "level": "intermediário", "years": 3},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["skill"]["canonical_name"] == "Python"
    assert body["level"] == "intermediário"
    assert body["years"] == 3
    assert len(api_client.get("/skills").json()) == 1


def test_add_skill_by_id(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)
    skill = _create_skill(api_client, "SQL")

    response = api_client.post(
        f"/candidates/{candidate['id']}/skills",
        json={"skill_id": skill["id"], "level": "avançado"},
    )

    assert response.status_code == 201, response.text
    assert response.json()["skill_id"] == skill["id"]


def test_add_skill_rejects_unknown_skill_id(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)

    response = api_client.post(
        f"/candidates/{candidate['id']}/skills",
        json={"skill_id": str(uuid.uuid4())},
    )

    _assert_error(response, 404, "not_found")


def test_add_skill_rejects_duplicate_pair(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)
    api_client.post(
        f"/candidates/{candidate['id']}/skills",
        json={"canonical_name": "Python"},
    )

    response = api_client.post(
        f"/candidates/{candidate['id']}/skills",
        json={"canonical_name": "python"},
    )

    _assert_error(response, 409, "conflict")


def test_add_skill_requires_exactly_one_reference(
    api_client: TestClient,
) -> None:
    candidate = _create_candidate(api_client)

    response = api_client.post(
        f"/candidates/{candidate['id']}/skills", json={"level": "iniciante"}
    )

    _assert_error(response, 422, "validation_error", with_details=True)


def test_add_skill_rejects_invalid_level(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)

    response = api_client.post(
        f"/candidates/{candidate['id']}/skills",
        json={"canonical_name": "Python", "level": "expert"},
    )

    _assert_error(response, 422, "validation_error", with_details=True)


def test_add_skill_rejects_negative_years(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)

    response = api_client.post(
        f"/candidates/{candidate['id']}/skills",
        json={"canonical_name": "Python", "years": -1},
    )

    _assert_error(response, 422, "validation_error", with_details=True)


def test_list_candidate_skills(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)
    api_client.post(
        f"/candidates/{candidate['id']}/skills",
        json={"canonical_name": "Python"},
    )

    response = api_client.get(f"/candidates/{candidate['id']}/skills")

    assert response.status_code == 200
    assert [item["skill"]["canonical_name"] for item in response.json()] == ["Python"]


def test_list_candidate_skills_unknown_candidate_returns_404(
    api_client: TestClient,
) -> None:
    response = api_client.get(f"/candidates/{uuid.uuid4()}/skills")

    _assert_error(response, 404, "not_found")


def test_patch_skill_link_and_clear_level(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)
    link = api_client.post(
        f"/candidates/{candidate['id']}/skills",
        json={"canonical_name": "Python", "level": "iniciante", "years": 1},
    ).json()
    url = f"/candidates/{candidate['id']}/skills/{link['skill_id']}"

    updated = api_client.patch(url, json={"years": 5})
    cleared = api_client.patch(url, json={"level": None})

    assert updated.status_code == 200, updated.text
    assert updated.json()["years"] == 5
    assert updated.json()["level"] == "iniciante"
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["level"] is None


def test_patch_unknown_skill_link_returns_404(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)

    response = api_client.patch(
        f"/candidates/{candidate['id']}/skills/{uuid.uuid4()}", json={"years": 2}
    )

    _assert_error(response, 404, "not_found")


def test_delete_skill_link_keeps_catalog(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)
    link = api_client.post(
        f"/candidates/{candidate['id']}/skills",
        json={"canonical_name": "Python"},
    ).json()

    response = api_client.delete(
        f"/candidates/{candidate['id']}/skills/{link['skill_id']}"
    )

    assert response.status_code == 204
    assert api_client.get(f"/candidates/{candidate['id']}/skills").json() == []
    assert len(api_client.get("/skills").json()) == 1


def test_get_candidate_includes_skills(api_client: TestClient) -> None:
    candidate = _create_candidate(api_client)
    api_client.post(
        f"/candidates/{candidate['id']}/skills",
        json={"canonical_name": "Python"},
    )

    response = api_client.get(f"/candidates/{candidate['id']}")

    assert response.status_code == 200
    assert [item["skill"]["canonical_name"] for item in response.json()["skills"]] == [
        "Python"
    ]
    assert response.json()["experiences"] == []
