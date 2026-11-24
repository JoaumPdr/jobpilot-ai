"""Exercita cálculo, persistência, detalhe e ranking com PostgreSQL real."""

import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.models import Job, JobMatch


def _candidate(client: TestClient) -> str:
    response = client.post(
        "/candidates", json={"name": "Ana", "resume_text": "Perfil fictício."}
    )
    assert response.status_code == 201
    return response.json()["id"]


def _declare_skill(client: TestClient, candidate_id: str, name: str) -> None:
    response = client.post(
        f"/candidates/{candidate_id}/skills", json={"canonical_name": name}
    )
    assert response.status_code == 201


def _job(
    client: TestClient,
    slug: str,
    description: str,
    *,
    company: str = "Equipe A",
    work_mode: str = "remoto",
) -> str:
    response = client.post(
        "/jobs",
        json={
            "title": f"Analista {slug}",
            "company": company,
            "url": f"https://example.com/{slug}",
            "description": description,
            "work_mode": work_mode,
            "location": "São Paulo",
        },
    )
    assert response.status_code == 201
    return response.json()["job"]["id"]


def test_calcula_e_atualiza_a_mesma_versao_com_evidencias(
    api_client: TestClient, test_engine: Engine
) -> None:
    candidate_id = _candidate(api_client)
    _declare_skill(api_client, candidate_id, "Postgres")
    job_id = _job(
        api_client,
        "dados",
        "Requisitos: PostgreSQL e Docker. Diferenciais: Kubernetes.",
    )
    path = f"/candidates/{candidate_id}/matches/{job_id}"
    assert api_client.get(path).status_code == 404
    result = api_client.post(path, json={"confirmed_absent": ["Docker"]})
    assert result.status_code == 200
    calculated = result.json()
    assert calculated["scoring_version"] == "deterministico-v1"
    assert Decimal(calculated["match_score"]) == Decimal("0.35")
    analysis = calculated["analysis"]
    assert analysis["met"][0]["candidate_skill"] == "Postgres"
    assert analysis["met"][0]["evidence_snippet"] == "PostgreSQL e Docker."
    assert analysis["absent"][0]["skill_name"] == "Docker"
    assert analysis["unconfirmed"][0]["skill_name"] == "Kubernetes"

    again = api_client.post(path)
    assert again.status_code == 200
    assert again.json()["id"] == calculated["id"]
    assert Decimal(again.json()["match_score"]) == Decimal("0.7")
    assert api_client.get(path).json() == again.json()
    with Session(test_engine) as db:
        rows = list(
            db.scalars(select(JobMatch).where(JobMatch.job_id == uuid.UUID(job_id)))
        )
        assert len(rows) == 1


def test_ranking_filtra_paginas_e_preserva_eliminatorias(
    api_client: TestClient,
) -> None:
    candidate_id = _candidate(api_client)
    _declare_skill(api_client, candidate_id, "Python")
    prefix = f"/candidates/{candidate_id}"
    assert (
        api_client.put(
            f"{prefix}/preferences",
            json={"knockout_rules": {"exclude_companies": ["Empresa X"]}},
        ).status_code
        == 200
    )
    first = _job(api_client, "remota", "Requirements: Python.")
    second = _job(
        api_client, "presencial", "Requirements: Python.", work_mode="presencial"
    )
    lower = _job(api_client, "parcial", "Requirements: Python and Docker.")
    rejected = _job(
        api_client, "eliminada", "Requirements: Python.", company="Empresa X"
    )
    for job_id in (first, second, rejected):
        assert api_client.post(f"{prefix}/matches/{job_id}").status_code == 200
    assert (
        api_client.post(
            f"{prefix}/matches/{lower}", json={"confirmed_absent": ["Docker"]}
        ).status_code
        == 200
    )

    empty = api_client.get(
        f"{prefix}/matches", params={"scoring_version": "historico-v1"}
    )
    assert empty.json()["items"] == []
    default_items = api_client.get(f"{prefix}/matches").json()["items"]
    assert [item["job"]["id"] for item in default_items] == [
        *sorted([first, second]),
        lower,
    ]
    page = api_client.get(f"{prefix}/matches", params={"limit": 1}).json()
    assert page["has_more"] is True
    assert page["items"] == default_items[:1]
    next_page = api_client.get(
        f"{prefix}/matches", params={"limit": 1, "offset": 2}
    ).json()
    assert next_page["has_more"] is False
    assert next_page["items"] == default_items[2:]
    filtered = api_client.get(
        f"{prefix}/matches", params={"work_mode": "remoto", "min_score": "0.8"}
    ).json()
    assert [item["job"]["id"] for item in filtered["items"]] == [first]
    assert (
        api_client.get(f"{prefix}/matches", params={"min_score": "1.1"}).status_code
        == 422
    )

    expanded = api_client.get(f"{prefix}/matches", params={"include_unscored": True})
    blocked = expanded.json()["items"][-1]
    assert blocked["job"]["id"] == rejected
    assert blocked["match_score"] is None
    assert blocked["knockout_flags"] == [
        {"code": "empresa_excluida", "actual": "Empresa X"}
    ]
    assert api_client.post(f"/jobs/{first}/archive").status_code == 200
    assert [
        item["job"]["id"]
        for item in api_client.get(f"{prefix}/matches").json()["items"]
    ] == [second, lower]


def test_calcula_vaga_legada_e_preserva_outra_versao(
    api_client: TestClient, test_engine: Engine
) -> None:
    candidate_id = _candidate(api_client)
    _declare_skill(api_client, candidate_id, "SQL")
    with Session(test_engine) as db:
        job = Job(
            title="Analista",
            company="Equipe",
            description="Requisitos: SQL.",
            source="manual",
            url="https://example.com/legada",
            canonical_url="https://example.com/legada",
            fingerprint="x",
        )
        db.add(job)
        db.flush()
        job_id = str(job.id)
        db.add(
            JobMatch(
                candidate_id=uuid.UUID(candidate_id),
                job_id=job.id,
                scoring_version="historico-v1",
                deterministic_score=Decimal("0.5"),
                match_score=Decimal("0.5"),
                knockout_flags=[],
                analysis={
                    "weighted_sum": "1.5",
                    "total_weight": "3",
                    "met": [],
                    "absent": [],
                    "unconfirmed": [],
                },
            )
        )
        db.commit()

    prefix = f"/candidates/{candidate_id}/matches"
    current = api_client.post(f"{prefix}/{job_id}")
    assert current.status_code == 200
    assert Decimal(current.json()["match_score"]) == 1
    past = api_client.get(
        f"{prefix}/{job_id}", params={"scoring_version": "historico-v1"}
    )
    assert past.status_code == 200
    assert Decimal(past.json()["match_score"]) == Decimal("0.5")
    assert api_client.get(f"{prefix}/{uuid.uuid4()}").status_code == 404
    assert api_client.post(f"{prefix}/{uuid.uuid4()}").status_code == 404
    assert api_client.get(f"/candidates/{uuid.uuid4()}/matches").status_code == 404
