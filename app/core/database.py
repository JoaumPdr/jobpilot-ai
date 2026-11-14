"""Configuração de banco de dados e sessão SQLAlchemy.

POR QUÊ: Centraliza a criação da engine e da fábrica de sessões, garantindo
que toda a aplicação use a mesma configuração de conexão. A sessão é
fornecida via dependency do FastAPI (ou middleware) para garantir fechamento
correto após cada requisição.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Engine síncrona (psycopg driver)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

# Fábrica de sessões síncronas
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """Retorna uma nova sessão SQLAlchemy.

    O chamador é responsável por fechar a sessão após o uso.
    Em rotas FastAPI, usar como dependency com `yield` para fechamento
    automático (ver app/main.py).

    Returns:
        Instância de Session pronta para uso.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
