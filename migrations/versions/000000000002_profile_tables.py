"""perfil: candidato, preferências, habilidades e experiências

Revision ID: 000000000002
Revises: 000000000001
Create Date: 2026-11-16 00:00:00.000000

POR QUÊ: cria o esquema do perfil (F1-T01). É uma migração única porque as
cinco tabelas formam uma unidade: as FKs dependem de `candidates` e `skills`,
e os testes de constraint validam exatamente este conjunto. O `downgrade`
remove na ordem inversa, mantendo upgrade/downgrade reversíveis.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "000000000002"
down_revision: str | None = "000000000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria as tabelas do perfil e suas constraints/índices."""
    op.create_table(
        "candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=False),
        sa.Column("headline", sa.String(length=200), nullable=True),
        sa.Column(
            "education",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "languages",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    # Unicidade case-insensitive do e-mail, sem depender da extensão CITEXT.
    op.create_index(
        "uq_candidates_email_lower",
        "candidates",
        [sa.text("lower(email)")],
        unique=True,
    )

    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column(
            "aliases",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.UniqueConstraint("canonical_name", name="uq_skills_canonical_name"),
    )

    op.create_table(
        "candidate_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "desired_titles",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "locations",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "work_modes",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "seniority_levels",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("min_salary", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "knockout_rules",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "candidate_id", name="uq_candidate_preferences_candidate_id"
        ),
    )

    op.create_table(
        "candidate_experiences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "skills_used",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("years", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_candidate_experiences_date_range",
        ),
        sa.CheckConstraint(
            "years IS NULL OR years >= 0",
            name="ck_candidate_experiences_years_non_negative",
        ),
    )
    op.create_index(
        "ix_candidate_experiences_candidate_id",
        "candidate_experiences",
        ["candidate_id"],
    )

    op.create_table(
        "candidate_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("level", sa.String(length=20), nullable=True),
        sa.Column("years", sa.Integer(), nullable=True),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "candidate_id",
            "skill_id",
            name="uq_candidate_skills_candidate_skill",
        ),
        sa.CheckConstraint(
            "level IS NULL OR level IN ('iniciante', 'intermediário', 'avançado')",
            name="ck_candidate_skills_level",
        ),
        sa.CheckConstraint(
            "years IS NULL OR years >= 0",
            name="ck_candidate_skills_years_non_negative",
        ),
    )
    op.create_index("ix_candidate_skills_skill_id", "candidate_skills", ["skill_id"])


def downgrade() -> None:
    """Remove o esquema do perfil na ordem inversa das dependências."""
    op.drop_index("ix_candidate_skills_skill_id", table_name="candidate_skills")
    op.drop_table("candidate_skills")
    op.drop_index(
        "ix_candidate_experiences_candidate_id",
        table_name="candidate_experiences",
    )
    op.drop_table("candidate_experiences")
    op.drop_table("candidate_preferences")
    op.drop_table("skills")
    op.drop_index("uq_candidates_email_lower", table_name="candidates")
    op.drop_table("candidates")
