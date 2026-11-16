"""Fixtures de banco para os testes de integração (PostgreSQL real).

POR QUÊ: testar constraints (UNIQUE, FK, CHECK, CASCADE) só é confiável no
mesmo banco usado em produção. O banco de teste é **isolado** do banco de
desenvolvimento: a fixture deriva `jobpilot_test` de `DATABASE_URL` (ou usa
`TEST_DATABASE_URL`) e **aborta** se o alvo não terminar em `_test`, para
ninguém rodar a suíte contra o banco de dev por acidente.

Ciclo por sessão de testes: recria o banco, aplica `alembic upgrade head`,
roda os testes e remove o banco no fim.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session

from app.core.config import settings

ROOT = Path(__file__).resolve().parents[2]
# Aceita apenas nomes simples para poder interpolar com segurança no DDL
# (CREATE/DROP DATABASE não aceitam parâmetros vinculados).
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_]+$")


def _resolve_test_url() -> URL:
    """Obtém a URL do banco de teste e valida o isolamento.

    Prioridade: `TEST_DATABASE_URL`; senão `DATABASE_URL` com sufixo `_test`.
    Levanta `RuntimeError` se o alvo for o banco de desenvolvimento, para que
    a suíte falhe antes de tocar em dados reais.
    """
    dev_url = make_url(settings.database_url)
    explicit = os.getenv("TEST_DATABASE_URL")

    if explicit:
        test_url = make_url(explicit)
    else:
        test_url = dev_url.set(database=f"{dev_url.database}_test")

    test_db = test_url.database or ""
    if not _SAFE_IDENTIFIER.fullmatch(test_db):
        raise RuntimeError(
            f"Nome de banco de teste inválido: {test_db!r}. "
            "Use apenas letras, números e underscore."
        )
    if test_db == dev_url.database:
        raise RuntimeError(
            "TEST_DATABASE_URL aponta para o banco de desenvolvimento "
            f"({test_db!r}). Use um banco separado terminado em '_test'."
        )
    if not test_db.endswith("_test"):
        raise RuntimeError(
            f"O banco de teste deve terminar em '_test' (recebido: {test_db!r})."
        )
    return test_url


def _admin_engine(test_url: URL) -> Engine:
    """Engine no banco `postgres` para criar/remover o banco de teste."""
    return create_engine(
        test_url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )


def _recreate_database(test_url: URL) -> None:
    """Remove e recria o banco de teste, sem conexões pendentes."""
    db_name = test_url.database
    admin = _admin_engine(test_url)
    try:
        with admin.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :db AND pid <> pg_backend_pid()"
                ),
                {"db": db_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
            connection.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        admin.dispose()


def _drop_database(test_url: URL) -> None:
    """Remove o banco de teste ao fim da sessão de testes."""
    db_name = test_url.database
    admin = _admin_engine(test_url)
    try:
        with admin.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :db AND pid <> pg_backend_pid()"
                ),
                {"db": db_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
    finally:
        admin.dispose()


def _upgrade_schema(test_url: URL) -> None:
    """Aplica todas as migrações no banco de teste (mesmo código de produção)."""
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option(
        "sqlalchemy.url", test_url.render_as_string(hide_password=False)
    )
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    """Engine conectada ao banco de teste dedicado, com schema migrado."""
    test_url = _resolve_test_url()
    _recreate_database(test_url)
    _upgrade_schema(test_url)

    engine = create_engine(test_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()
        _drop_database(test_url)


@pytest.fixture
def db_session(test_engine: Engine) -> Iterator[Session]:
    """Sessão dentro de uma transação revertida ao fim de cada teste.

    Assim cada teste começa com o banco vazio, sem precisar recriar o schema.
    """
    with test_engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection)
        try:
            yield session
        finally:
            session.close()
            # Após um IntegrityError esperado, a transação pode já ter sido
            # desassociada pela sessão; rollback só se ainda estiver ativa.
            if transaction.is_active:
                transaction.rollback()
