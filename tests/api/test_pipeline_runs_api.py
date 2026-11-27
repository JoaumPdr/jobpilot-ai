"""Exercita HTTP, grafo, persistência e análise com respostas locais sintéticas."""

import json
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.api import dependencies
from app.llm.providers import LLMProviderError, LLMResponse
from app.models import JobMatch

CSV = (
    b"title,company,description,url\n"
    b"Analista A,Equipe A,Requisitos: Python.,https://example.invalid/pipeline-a\n"
    b"Analista B,Equipe B,Requisitos: Python.,https://example.invalid/pipeline-b\n"
)


class FakeAnalysis:
    """Produz uma resposta para a vaga real do prompt e permite falhar só na primeira."""

    name = "fake"
    model = "teste-http"

    def __init__(self, *, partial: bool) -> None:
        self.partial = partial
        self.calls: list[str] = []

    def complete(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        job_id = json.loads(user_prompt)["job_id"]
        self.calls.append(job_id)
        if self.partial and len(self.calls) == 1:
            raise LLMProviderError("Falha sintética do provedor.")
        return LLMResponse(
            text=json.dumps(
                {
                    "job_id": job_id,
                    "matched_skills": [],
                    "missing_skills": [],
                    "unknown_requirements": [],
                    "evidence": [],
                    "recommendation": "Revisar.",
                    "explanation": "Resposta sintética.",
                }
            )
        )


@pytest.fixture
def form(api_client: TestClient) -> dict[str, str]:
    profile = api_client.post(
        "/candidates", json={"name": "Ana", "resume_text": "Perfil fictício."}
    )
    assert profile.status_code == 201
    candidate_id = profile.json()["id"]
    skill = api_client.post(
        f"/candidates/{candidate_id}/skills", json={"canonical_name": "Python"}
    )
    assert skill.status_code == 201
    return {"run_id": str(uuid4()), "candidate_id": candidate_id, "source": "teste"}


def post_csv(
    client: TestClient, form: dict[str, str], content: bytes = CSV, *, query: str = ""
) -> Response:
    return client.post(
        "/pipeline/runs" + query,
        data=form,
        files={"file": ("vagas.csv", content, "text/csv")},
    )


@pytest.mark.parametrize("partial", [False, True])
def test_fluxo_com_llm_consulta_e_reexecucao(
    partial: bool,
    api_client: TestClient,
    test_engine: Engine,
    form: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeAnalysis(partial=partial)
    monkeypatch.setattr(dependencies, "build_llm_provider", lambda _: provider)
    form["llm_enabled"] = "true"
    response = post_csv(api_client, form)
    assert response.status_code == 200
    result = response.json()
    assert result["run_id"] == form["run_id"]
    assert result["status"] == ("partial" if partial else "completed")
    assert result["finished_at"] is not None
    snapshot = result["state_snapshot"]
    assert snapshot["candidate_id"] == form["candidate_id"]
    assert snapshot["selected_ids"] == provider.calls
    assert len(set(provider.calls)) == 2
    assert snapshot["analyzed_ids"] == (
        provider.calls[1:] if partial else provider.calls
    )
    assert [
        item["job_id"] for item in result["recommendations_for_review"]
    ] == provider.calls
    assert result["counters"]["analyzed"] == len(snapshot["analyzed_ids"])
    assert result["errors"] == snapshot["errors"]
    if partial:
        assert result["errors"] == [
            {
                "job_id": provider.calls[0],
                "stage": "analysis",
                "error_type": "LLMProviderError",
                "attempts": 1,
            }
        ]
    else:
        assert result["errors"] == []
    with Session(test_engine) as db:
        analyzed = db.scalars(
            select(JobMatch.job_id).where(JobMatch.llm_analysis.is_not(None))
        )
        assert set(analyzed) == {UUID(value) for value in snapshot["analyzed_ids"]}
    read = api_client.get(f"/pipeline/runs/{form['run_id']}")
    assert read.status_code == 200 and read.json() == result
    assert post_csv(api_client, form).json() == result
    assert len(provider.calls) == 2
    assert (
        api_client.get(f"/candidates/{form['candidate_id']}/applications").json() == []
    )
    assert post_csv(api_client, form, CSV + b"\n").status_code == 409


def test_modo_deterministico_e_filtros_do_catalogo(
    api_client: TestClient, form: dict[str, str]
) -> None:
    result = post_csv(api_client, form, query="?q=Equipe%20B").json()
    assert result["status"] == "completed"
    assert result["counters"]["imported"] == 2
    assert result["counters"]["filtered"] == 1
    assert result["counters"]["analyzed"] == 0
    assert len(result["recommendations_for_review"]) == 1


def test_csv_invalido_permite_consultar_falha_do_lote(
    api_client: TestClient, form: dict[str, str]
) -> None:
    response = post_csv(api_client, form, b"sem,cabecalho\n")
    assert response.status_code == 422
    read = api_client.get(f"/pipeline/runs/{form['run_id']}")
    assert read.status_code == 200
    result = read.json()
    assert result["status"] == "failed"
    assert result["errors"] == [{"stage": "importar", "error_type": "InvalidDataError"}]
    assert result["recommendations_for_review"] is None


def test_entradas_invalidas_sao_recusadas_antes_de_importar(
    api_client: TestClient, form: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(dependencies, "build_llm_provider", lambda _: None)
    assert post_csv(api_client, {**form, "llm_enabled": "true"}).status_code == 422
    assert post_csv(api_client, form, query="?limit=0").status_code == 422
    assert (
        post_csv(api_client, form, query=f"?candidate_id={uuid4()}").status_code == 422
    )
    assert (
        post_csv(api_client, {**form, "candidate_id": str(uuid4())}).status_code == 404
    )
    assert api_client.get(f"/pipeline/runs/{form['run_id']}").status_code == 404
