"""Requisitos determinísticos extraídos das vagas.

Revision ID: 000000000005
Revises: 000000000004
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "000000000005"
down_revision: str | None = "000000000004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria a tabela de requisitos com integridade referencial e evidência."""
    op.create_table(
        "job_skills",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "job_id",
            sa.Uuid(),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "skill_id",
            sa.Uuid(),
            sa.ForeignKey("skills.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("requirement_type", sa.String(20), nullable=False),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_snippet", sa.Text(), nullable=False),
        sa.Column("extraction_method", sa.String(30), nullable=False),
        sa.UniqueConstraint("job_id", "skill_id", name="uq_job_skills_job_skill"),
        sa.CheckConstraint(
            "requirement_type IN ('obrigatorio', 'desejavel')",
            name="ck_job_skills_requirement_type",
        ),
        sa.CheckConstraint("weight >= 0", name="ck_job_skills_weight_non_negative"),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1", name="ck_job_skills_confidence"
        ),
        sa.CheckConstraint(
            "btrim(evidence_snippet) <> ''", name="ck_job_skills_evidence"
        ),
    )
    op.create_index("ix_job_skills_skill_id", "job_skills", ["skill_id"])


def downgrade() -> None:
    """Remove somente os requisitos; preserva vagas e catálogo de habilidades."""
    op.drop_table("job_skills")
