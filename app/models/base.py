"""Base declarativa dos modelos SQLAlchemy.

POR QUÊ: Usar UUID como tipo de chave primária em todas as tabelas garante
identificadores únicos globalmente, facilita fusão de dados de diferentes
fontes e evita vazamento de informações sequenciais (ex.: contar registros
por IDs incrementais).

Decisão registrada em docs/adr/0010-tipo-de-id-uuid.md.
"""

from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Classe base para todos os modelos SQLAlchemy.

    Fornece:
    - `id` como UUID (chave primária, gerada automaticamente)
    - `__tablename__` derivado automaticamente do nome da classe (snake_case)
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Gera nome da tabela a partir do nome da classe (snake_case).

        Exemplo: CandidateProfile -> candidate_profile
        """
        name = cls.__name__
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i != 0:
                result.append("_")
            result.append(char.lower())
        return "".join(result)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
