"""Rota de health check.

POR QUÊ: Este endpoint é o ponto de entrada para monitoramento e verificações
de saúde da aplicação. Ele não depende de SQLAlchemy (será introduzido na
F0-T05); usa psycopg diretamente para validar a conexão com o banco.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from psycopg import OperationalError, connect

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


def _psycopg_url(sqlalchemy_url: str) -> str:
    """Converte URL SQLAlchemy para formato aceito pelo psycopg v3.

    POR QUÊ: SQLAlchemy usa o prefixo ``postgresql+psycopg://``, mas o psycopg
    v3 espera apenas ``postgresql://``. Essa conversão permite reusar a mesma
    variável de ambiente para ambos.

    Args:
        sqlalchemy_url: URL no formato SQLAlchemy (ex: postgresql+psycopg://...).

    Returns:
        URL no formato psycopg (ex: postgresql://...).
    """
    return sqlalchemy_url.replace("postgresql+psycopg://", "postgresql://", 1)


def _check_database() -> dict[str, Any]:
    """Tenta estabelecer conexão com o banco de dados.

    Returns:
        Dicionário com status da conexão e, em caso de falha, o erro.
    """
    try:
        conn = connect(_psycopg_url(settings.database_url), connect_timeout=2)
        conn.close()
        return {"status": "healthy"}
    except OperationalError as exc:
        logger.warning("database_unavailable", error=str(exc))
        return {"status": "unhealthy", "error": "database_connection_failed"}
    except Exception as exc:  # noqa: BLE001 - qualquer falha de conexão é reportada
        logger.warning("database_unexpected_error", error=str(exc))
        return {"status": "unhealthy", "error": "unexpected_error"}


@router.get("/health", tags=["health"])
def health() -> dict[str, Any]:
    """Retorna o status de saúde da aplicação e do banco de dados.

    Retorna HTTP 200 independentemente do estado do banco, incluindo um
    campo `database.status` que indica se a conexão está saudável.

    Returns:
        Dicionário com status da aplicação e do banco.
    """
    database = _check_database()
    overall = "healthy" if database.get("status") == "healthy" else "degraded"

    return {
        "status": overall,
        "app": "jobpilot-ai",
        "version": "0.1.0",
        "database": database,
    }
