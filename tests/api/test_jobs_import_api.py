"""Testes de API da importação CSV."""

from __future__ import annotations

import time
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

HEADER = (
    "title,company,description,url,location,work_mode,seniority,source,"
    "external_id,salary_min,salary_max,currency,posted_at"
)


def _row(**overrides: Any) -> str:
    values: dict[str, str] = {
        "title": "Engenheira de Dados",
        "company": "Empresa X",
        "description": "Descrição A",
        "url": "https://empresa.com/vagas/1",
        "location": "São Paulo",
        "work_mode": "home office",
        "seniority": "Sênior",
        "source": "portal-a",
        "external_id": "ext-1",
        "salary_min": "12000.00",
        "salary_max": "18000.00",
        "currency": "brl",
        "posted_at": "2026-11-10T09:00:00Z",
    }
    values.update(overrides)
    return ",".join(values.values())


def _csv(*rows: str) -> bytes:
    return ("\n".join((HEADER, *rows)) + "\n").encode("utf-8")


def _upload(
    client: TestClient,
    content: bytes,
    *,
    filename: str = "vagas.csv",
    source: str | None = None,
) -> Any:
    data = {"source": source} if source is not None else None
    return client.post(
        "/jobs/import",
        files={"file": (filename, content, "text/csv")},
        data=data,
    )


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


def test_import_csv_returns_batch_report(
    api_client: TestClient, test_engine: Engine
) -> None:
    row_a = _row()
    row_b = _row(
        title="Analista de Dados",
        company="Empresa Y",
        url="https://empresa.com/vagas/2",
        external_id="ext-2",
    )

    response = _upload(api_client, _csv(row_a, row_b), source="planilha")

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["total_rows"] == 2
    assert body["inserted"] == 2
    assert body["duplicates"] == 0
    assert body["rejected"] == 0
    assert body["errors"] == []
    assert body["kind"] == "csv"
    assert body["filename"] == "vagas.csv"
    assert body["source"] == "planilha"
    assert body["finished_at"]

    # O lote e o vínculo das vagas ficaram gravados no banco.
    with test_engine.connect() as connection:
        batch = connection.execute(
            text(
                "SELECT total_rows, inserted, duplicates, rejected, finished_at "
                "FROM import_batches WHERE id = :id"
            ),
            {"id": body["id"]},
        ).one()
        linked = connection.execute(
            text("SELECT count(*) FROM jobs WHERE import_batch_id = :id"),
            {"id": body["id"]},
        ).scalar_one()
    assert batch.total_rows == 2
    assert batch.inserted == 2
    assert batch.finished_at is not None
    assert linked == 2


def test_import_csv_reports_invalid_line_without_aborting(
    api_client: TestClient,
) -> None:
    good = _row()
    bad = _row(title="Vaga quebrada", url="ftp://empresa.com/vagas/9", external_id="")

    response = _upload(api_client, _csv(good, bad))

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["total_rows"] == 2
    assert body["inserted"] == 1
    assert body["rejected"] == 1
    assert len(body["errors"]) == 1
    assert body["errors"][0]["row"] == 3
    assert body["errors"][0]["field"] == "url"


def test_reimporting_same_csv_inserts_nothing(api_client: TestClient) -> None:
    content = _csv(_row())

    first = _upload(api_client, content)
    second = _upload(api_client, content)

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["inserted"] == 1
    assert second.json()["inserted"] == 0
    assert second.json()["duplicates"] == 1
    assert second.json()["rejected"] == 0


def test_import_csv_rejects_file_with_incomplete_header(
    api_client: TestClient,
) -> None:
    content = b"title,company,url\nDev,Empresa,https://empresa.com/vagas/6\n"

    response = _upload(api_client, content)

    body = _assert_error(response, 422, "invalid_data", with_details=True)
    assert "description" in body["details"][0]["message"]


def test_import_csv_rejects_non_utf8_file(api_client: TestClient) -> None:
    content = (
        "title,company,description,url\nVaga,Empresa,Descrição,https://x.com/1"
    ).encode("latin-1")

    response = _upload(api_client, content)

    body = _assert_error(response, 422, "invalid_data", with_details=True)
    assert "UTF-8" in body["message"]


def test_import_5000_rows_within_30_seconds(api_client: TestClient) -> None:
    rows = [
        _row(
            title=f"Vaga {index}",
            url=f"https://empresa.com/vagas/{index}",
            external_id=f"ext-{index}",
        )
        for index in range(5000)
    ]
    content = _csv(*rows)

    started = time.perf_counter()
    response = _upload(api_client, content)
    elapsed = time.perf_counter() - started

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["total_rows"] == 5000
    assert body["inserted"] == 5000
    assert body["rejected"] == 0
    # RNF-09: importar 5 mil linhas em menos de 30 s.
    assert elapsed < 30, f"Importação demorou {elapsed:.1f}s (limite: 30 s)."
