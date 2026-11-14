"""Testes de API para o endpoint /health.

POR QUÊ: Validar que o health check responde 200 com o esquema esperado,
independentemente do estado do banco de dados (que pode não estar disponível
em ambientes de CI sem Docker).
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    """O endpoint /health deve sempre responder HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_schema():
    """O corpo da resposta deve conter status, app, version e database."""
    response = client.get("/health")
    data = response.json()

    assert "status" in data
    assert data["status"] in ("healthy", "degraded")
    assert data["app"] == "jobpilot-ai"
    assert "version" in data

    assert "database" in data
    assert "status" in data["database"]
    assert data["database"]["status"] in ("healthy", "unhealthy")


def test_health_response_headers():
    """A resposta deve incluir o cabeçalho X-Request-ID."""
    response = client.get("/health")
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"]
