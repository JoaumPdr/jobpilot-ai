"""Exercita o fluxo da Fase 1 pela API com PostgreSQL."""

from fastapi.testclient import TestClient


def test_profile_to_application_flow(api_client: TestClient) -> None:
    profile = api_client.post(
        "/candidates",
        json={
            "name": "Ana Silva",
            "email": "ana@example.com",
            "resume_text": "Experiência com análise de dados.",
        },
    )
    assert profile.status_code == 201, profile.text
    candidate_id = profile.json()["id"]
    candidate_path = f"/candidates/{candidate_id}"
    preferences = {"desired_titles": ["Analista de dados"]}
    saved_preferences = api_client.put(
        f"{candidate_path}/preferences", json=preferences
    )
    assert saved_preferences.status_code == 200, saved_preferences.text
    candidate = api_client.get(candidate_path)
    assert candidate.status_code == 200, candidate.text
    desired_title = candidate.json()["preferences"]["desired_titles"][0]
    assert desired_title == "Analista de dados"

    csv = (
        "title,company,description,url,work_mode\n"
        "Analista de dados,Empresa X,Relatórios,https://example.com/jobs/dados,remoto\n"
        "Analista de dados,Empresa Y,Painéis,https://example.com/jobs/paineis,presencial\n"
    )
    files = {"file": ("vagas.csv", csv.encode("utf-8"), "text/csv")}
    source = {"source": "planilha"}
    imported = api_client.post("/jobs/import", files=files, data=source)
    assert imported.status_code == 201, imported.text
    batch = imported.json()
    assert batch["inserted"] == 2
    assert batch["rejected"] == 0

    reimported = api_client.post("/jobs/import", files=files, data=source)
    assert reimported.status_code == 201, reimported.text
    assert reimported.json()["inserted"] == 0
    assert reimported.json()["duplicates"] == 2

    filters = {"q": desired_title, "work_mode": "remoto", **source}
    matching = api_client.get("/jobs", params=filters)
    assert matching.status_code == 200, matching.text
    (job,) = matching.json()["items"]
    assert job["company"] == "Empresa X"
    assert job["import_batch_id"] == batch["id"]
    job_id = job["id"]

    saved = api_client.post(f"{candidate_path}/jobs/{job_id}/save")
    assert saved.status_code == 201, saved.text
    application = saved.json()
    assert application["status"] == "salva"
    path = f"{candidate_path}/applications/{application['id']}"
    for target in ("planejada", "aplicada"):
        updated = api_client.patch(path, json={"status": target})
        assert updated.status_code == 200, updated.text
        assert updated.json()["status"] == target

    detail = api_client.get(path)
    assert detail.status_code == 200, detail.text
    history = detail.json()["status_history"]
    assert [entry["to_status"] for entry in history] == [
        "salva",
        "planejada",
        "aplicada",
    ]
    assert detail.json()["applied_at"] == history[-1]["changed_at"]
    applied_jobs = api_client.get(
        "/jobs",
        params={
            **filters,
            "candidate_id": candidate_id,
            "application_status": "aplicada",
        },
    )
    assert applied_jobs.status_code == 200, applied_jobs.text
    assert [item["id"] for item in applied_jobs.json()["items"]] == [job_id]
