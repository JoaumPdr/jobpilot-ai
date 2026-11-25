"""Cache das análises LLM e métricas de geração.

Revision ID: 000000000007
Revises: 000000000006
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "000000000007"
down_revision: str | None = "000000000006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria o cache e protege a unicidade e as métricas de cada resultado."""
    op.create_table(
        "llm_cache",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("cache_key", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("prompt_version", sa.String(), nullable=False),
        sa.Column("response", postgresql.JSONB(), nullable=False),
        sa.Column("tokens_in", sa.Integer()),
        sa.Column("tokens_out", sa.Integer()),
        sa.Column("cost_estimate", sa.Numeric()),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("cache_key", name="uq_llm_cache_key"),
        sa.CheckConstraint(
            "tokens_in >= 0 AND tokens_out >= 0 AND cost_estimate >= 0 AND latency_ms >= 0",
            name="ck_llm_cache_nonnegative_metrics",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(response) = 'object'", name="ck_llm_cache_response_object"
        ),
    )


def downgrade() -> None:
    """Remove o cache sem afetar as tabelas de vagas e de matching."""
    op.drop_table("llm_cache")
