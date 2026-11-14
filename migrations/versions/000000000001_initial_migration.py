"""initial migration

Revision ID: 000000000001
Revises: 
Create Date: 2026-11-13 23:30:00.000000

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "000000000001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Nenhuma tabela ainda — migração inicial apenas marca o ponto de partida."""


def downgrade() -> None:
    """Não há nada para reverter na migração inicial."""
