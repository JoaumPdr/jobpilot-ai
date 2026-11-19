"""Verifica a gestão de candidaturas e o filtro de vagas de ponta a ponta."""

from uuid import UUID

from fastapi.testclient import TestClient


def _candidate(client: TestClient, name: str) -> str:
    response = client.post(
        "/candidates",
        json={
            "name": name,
            "email": f"{name}@example.com",
            "resume_text": "Experiência com análise de dados.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _job(client: TestClient, slug: str, work_mode: str = "remoto") -> str:
    response = client.post(
        "/jobs",
        json={
            "title": "Analista de dados",
            "company": "Empresa X",
            "description": "Análise de dados.",
            "url": f"https://example.com/jobs/{slug}",
            "work_mode": work_mode,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["job"]["id"]


def _apply(client: TestClient, path: str, job_id: str) -> str:
    response = client.post(path, json={"job_id": job_id, "notes": "Contato inicial"})
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "salva"
    assert response.json()["applied_at"] is None
    return response.json()["id"]


def test_save_job_shortcut_and_application_flow(api_client: TestClient) -> None:
    candidate_id = _candidate(api_client, "ana")
    job_id = _job(api_client, "salvar")
    save_path = f"/candidates/{candidate_id}/jobs/{job_id}/save"
    collection = f"/candidates/{candidate_id}/applications"

    saved = api_client.post(save_path)
    assert saved.status_code == 201, saved.text
    application = saved.json()
    assert application["candidate_id"] == candidate_id
    assert application["job_id"] == job_id
    assert application["status"] == "salva"
    assert application["applied_at"] is None
    path = f"{collection}/{application['id']}"

    planned = api_client.patch(path, json={"status": "planejada"})
    assert planned.status_code == 200
    assert planned.json()["status"] == "planejada"
    applied = api_client.patch(path, json={"status": "aplicada"})
    assert applied.status_code == 200
    assert applied.json()["status"] == "aplicada"
    assert api_client.post(save_path).status_code == 409
    assert [row["id"] for row in api_client.get(collection).json()] == [
        application["id"]
    ]

    detail = api_client.get(path)
    assert detail.status_code == 200
    assert detail.json()["status"] == "aplicada"
    history = detail.json()["status_history"]
    assert [(row["from_status"], row["to_status"]) for row in history] == [
        (None, "salva"),
        ("salva", "planejada"),
        ("planejada", "aplicada"),
    ]
    assert applied.json()["applied_at"] == history[-1]["changed_at"]


def test_archive_job_hides_it_by_default_and_preserves_application(
    api_client: TestClient,
) -> None:
    candidate_id = _candidate(api_client, "ana")
    job_id = _job(api_client, "arquivar")
    collection = f"/candidates/{candidate_id}/applications"
    application_id = _apply(api_client, collection, job_id)

    path = f"/jobs/{job_id}/archive"
    for _ in range(2):
        archived = api_client.post(path)
        assert archived.status_code == 200, archived.text
        assert archived.json()["id"] == job_id
        assert archived.json()["is_archived"] is True

    assert api_client.get("/jobs").json()["items"] == []
    visible = api_client.get("/jobs", params={"include_archived": "true"})
    assert visible.status_code == 200
    assert [item["id"] for item in visible.json()["items"]] == [job_id]
    detail = api_client.get(f"{collection}/{application_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "salva"
    assert len(detail.json()["status_history"]) == 1


def test_job_actions_return_not_found_for_missing_references(
    api_client: TestClient,
) -> None:
    candidate_id = _candidate(api_client, "ana")
    job_id = _job(api_client, "referencia")
    missing = UUID(int=1)

    for path in (
        f"/jobs/{missing}/archive",
        f"/candidates/{missing}/jobs/{job_id}/save",
        f"/candidates/{candidate_id}/jobs/{missing}/save",
    ):
        response = api_client.post(path)
        assert response.status_code == 404
        assert response.json()["error"] == "not_found"


def test_application_history_and_notes(api_client: TestClient) -> None:
    candidate_id = _candidate(api_client, "ana")
    collection = f"/candidates/{candidate_id}/applications"
    job_id = _job(api_client, "dados")
    application_id = _apply(api_client, collection, job_id)
    path = f"{collection}/{application_id}"

    invalid = api_client.patch(path, json={"status": "aplicada", "notes": "Inválida"})
    assert invalid.status_code == 422
    assert (
        "salva" in invalid.json()["message"] and "aplicada" in invalid.json()["message"]
    )
    initial = api_client.get(path).json()
    assert initial["notes"] == "Contato inicial"
    assert len(initial["status_history"]) == 1

    planned = api_client.patch(
        path, json={"status": "planejada", "transition_note": "Revisar currículo."}
    )
    assert planned.status_code == 200
    applied = api_client.patch(path, json={"status": "aplicada"})
    assert applied.status_code == 200
    edited = api_client.patch(path, json={"notes": "Acompanhar retorno"})
    assert edited.status_code == 200
    assert edited.json()["notes"] == "Acompanhar retorno"
    cleared = api_client.patch(path, json={"notes": None})
    assert cleared.status_code == 200
    assert cleared.json()["notes"] is None

    detail = api_client.get(path)
    history = detail.json()["status_history"]
    assert detail.status_code == 200
    assert [(row["from_status"], row["to_status"], row["note"]) for row in history] == [
        (None, "salva", None),
        ("salva", "planejada", "Revisar currículo."),
        ("planejada", "aplicada", None),
    ]
    assert applied.json()["applied_at"] == history[-1]["changed_at"]
    assert [row["id"] for row in api_client.get(collection).json()] == [application_id]
    assert api_client.post(collection, json={"job_id": job_id}).status_code == 409


def test_application_endpoints_scope_reads_and_updates_by_candidate(
    api_client: TestClient,
) -> None:
    owner = _candidate(api_client, "ana")
    other = _candidate(api_client, "bia")
    application_id = _apply(
        api_client, f"/candidates/{owner}/applications", _job(api_client, "dados")
    )
    other_collection = f"/candidates/{other}/applications"
    other_path = f"{other_collection}/{application_id}"
    assert api_client.get(other_collection).json() == []
    assert api_client.get(other_path).status_code == 404
    assert api_client.patch(other_path, json={"notes": "Troca"}).status_code == 404
    missing_job = api_client.post(other_collection, json={"job_id": str(UUID(int=1))})
    assert missing_job.status_code == 404


def test_job_status_filter_combines_candidate_work_mode_and_pagination(
    api_client: TestClient,
) -> None:
    ana = _candidate(api_client, "ana")
    bia = _candidate(api_client, "bia")
    ana_collection = f"/candidates/{ana}/applications"
    first = _job(api_client, "dados-1")
    second = _job(api_client, "dados-2")
    onsite = _job(api_client, "dados-3", "presencial")
    bia_only = _job(api_client, "dados-4")

    for job in (first, second, onsite):
        application_id = _apply(api_client, ana_collection, job)
        response = api_client.patch(
            f"{ana_collection}/{application_id}", json={"status": "planejada"}
        )
        assert response.status_code == 200
    _apply(api_client, ana_collection, bia_only)
    bia_collection = f"/candidates/{bia}/applications"
    other_id = _apply(api_client, bia_collection, bia_only)
    assert (
        api_client.patch(
            f"{bia_collection}/{other_id}", json={"status": "planejada"}
        ).status_code
        == 200
    )

    filters = {
        "candidate_id": ana,
        "application_status": "planejada",
        "work_mode": "remoto",
        "limit": 1,
    }
    first_page = api_client.get("/jobs", params=filters)
    second_page = api_client.get("/jobs", params={**filters, "offset": 1})
    assert first_page.status_code == second_page.status_code == 200
    assert first_page.json()["has_more"] is True
    assert second_page.json()["has_more"] is False
    assert [
        first_page.json()["items"][0]["id"],
        second_page.json()["items"][0]["id"],
    ] == [
        second,
        first,
    ]
    assert (
        api_client.get("/jobs", params={"application_status": "planejada"}).status_code
        == 422
    )
