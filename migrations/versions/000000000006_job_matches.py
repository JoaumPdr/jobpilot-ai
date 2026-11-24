"""Resultados de matching versionados por candidato e vaga.

Revision ID: 000000000006
Revises: 000000000005
Create Date: 2026-11-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "000000000006"
down_revision: str | None = "000000000005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria as avaliações persistidas e os índices usados pelo ranking."""
    op.create_table(
        "job_matches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "candidate_id",
            sa.Uuid(),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            sa.Uuid(),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scoring_version", sa.String(80), nullable=False),
        sa.Column("deterministic_score", sa.Numeric(), nullable=True),
        sa.Column("semantic_score", sa.Numeric(), nullable=True),
        sa.Column("match_score", sa.Numeric(), nullable=True),
        sa.Column("knockout_flags", postgresql.JSONB(), nullable=False),
        sa.Column("analysis", postgresql.JSONB(), nullable=False),
        sa.Column("llm_analysis", postgresql.JSONB(none_as_null=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "candidate_id",
            "job_id",
            "scoring_version",
            name="uq_job_matches_candidate_job_version",
        ),
        sa.CheckConstraint(
            "deterministic_score BETWEEN 0 AND 1 AND semantic_score BETWEEN 0 AND 1 "
            "AND match_score BETWEEN 0 AND 1",
            name="ck_job_matches_score_range",
        ),
    )
    op.create_index(
        "ix_job_matches_ranking",
        "job_matches",
        ["candidate_id", "scoring_version", "match_score"],
    )
    op.create_index("ix_job_matches_job_id", "job_matches", ["job_id"])


def downgrade() -> None:
    """Remove as avaliações, preservando candidatos, vagas e seus requisitos."""
    op.drop_table("job_matches")
