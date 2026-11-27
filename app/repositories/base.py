"""Base dos repositórios SQLAlchemy.

POR QUÊ: o controle de transação (`commit`/`rollback`) é igual em todos os
repositórios. Extrair aqui evita duplicar o mesmo bloco em cada arquivo e
permite que o serviço chame a transação sem conhecer detalhes do ORM.
"""

from __future__ import annotations

from sqlalchemy.orm import Session


class BaseRepository:
    """Base com o controle de transação usado pelos serviços."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def commit(self) -> None:
        """Confirma a transação corrente."""
        self._db.commit()

    def rollback(self) -> None:
        """Descarta a transação corrente (após erro de integridade)."""
        self._db.rollback()
