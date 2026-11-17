"""vagas: lotes de importação e vagas normalizadas

Revision ID: 000000000003
Revises: 000000000002
Create Date: 2026-11-17 00:00:00.000000

POR QUÊ: cria o esquema de vagas (F1-T03). As duas tabelas formam uma unidade:
`jobs.import_batch_id` depende de `import_batches`, e a deduplicação definida no
plano (ID externo único, índices de fingerprint/URL) só faz sentido com as duas.
O `downgrade` remove na ordem inversa, mantendo upgrade/downgrade reversíveis.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "000000000003"
down_revision: str | None = "000000000002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria `import_batches`, `jobs`, seus índices e constraints."""
    op.create_table(
        "import_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "total_rows",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "inserted",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "duplicates",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "rejected",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "errors",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        # Mesmos CHECKs do modelo: o banco protege mesmo se o serviço falhar.
        sa.CheckConstraint(
            "kind IN ('csv', 'manual', 'api')",
            name="ck_import_batches_kind",
        ),
        sa.CheckConstraint(
            "total_rows >= 0 AND inserted >= 0 AND duplicates >= 0 AND rejected >= 0",
            name="ck_import_batches_counters_non_negative",
        ),
        sa.CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at",
            name="ck_import_batches_finished_after_started",
        ),
    )

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column(
            "work_mode",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'desconhecido'"),
        ),
        sa.Column(
            "seniority",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'desconhecido'"),
        ),
        sa.Column("employment_type", sa.String(length=100), nullable=True),
        sa.Column("salary_min", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("salary_max", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "collected_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "import_batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("import_batches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "duplicate_of_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="SET NULL"),
            nullable=True,
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
        sa.CheckConstraint(
            "work_mode IN ('remoto', 'híbrido', 'presencial', 'desconhecido')",
            name="ck_jobs_work_mode",
        ),
        sa.CheckConstraint(
            "seniority IN "
            "('estágio', 'júnior', 'pleno', 'sênior', 'especialista', 'desconhecido')",
            name="ck_jobs_seniority",
        ),
        sa.CheckConstraint(
            "(salary_min IS NULL OR salary_min >= 0) "
            "AND (salary_max IS NULL OR salary_max >= 0)",
            name="ck_jobs_salary_non_negative",
        ),
        sa.CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_max >= salary_min",
            name="ck_jobs_salary_range",
        ),
        sa.CheckConstraint(
            "duplicate_of_job_id IS NULL OR duplicate_of_job_id <> id",
            name="ck_jobs_duplicate_not_self",
        ),
    )

    # Unicidade só quando há ID externo (índice parcial); CSV/manual sem ID
    # externo podem se repetir sem colidir entre si.
    op.create_index(
        "uq_jobs_source_external_id",
        "jobs",
        ["source", "external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
    )
    op.create_index("ix_jobs_fingerprint", "jobs", ["fingerprint"])
    op.create_index("ix_jobs_canonical_url", "jobs", ["canonical_url"])


def downgrade() -> None:
    """Remove as tabelas de vagas na ordem inversa das dependências."""
    op.drop_index("ix_jobs_canonical_url", table_name="jobs")
    op.drop_index("ix_jobs_fingerprint", table_name="jobs")
    op.drop_index("uq_jobs_source_external_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("import_batches")
