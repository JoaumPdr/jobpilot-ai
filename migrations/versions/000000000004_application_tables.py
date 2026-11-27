"""candidaturas: estado atual e histórico de status

Revision ID: 000000000004
Revises: 000000000003
Create Date: 2026-11-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "000000000004"
down_revision: str | None = "000000000003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Os valores pertencem a esta revisão, mesmo se o modelo evoluir depois.
_STATUS_VALUES = (
    "'salva', 'planejada', 'aplicada', 'entrevista', 'oferta', 'rejeitada', 'encerrada'"
)


def upgrade() -> None:
    """Cria as tabelas e protege as referências e os status no banco."""
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="salva"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
            "candidate_id", "job_id", name="uq_applications_candidate_job"
        ),
        sa.CheckConstraint(
            f"status IN ({_STATUS_VALUES})", name="ck_applications_status"
        ),
    )
    op.create_index("ix_applications_job_id", "applications", ["job_id"])

    op.create_table(
        "application_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(20), nullable=True),
        sa.Column("to_status", sa.String(20), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.CheckConstraint(
            f"from_status IN ({_STATUS_VALUES})",
            name="ck_application_status_history_from_status",
        ),
        sa.CheckConstraint(
            f"to_status IN ({_STATUS_VALUES})",
            name="ck_application_status_history_to_status",
        ),
    )
    op.create_index(
        "ix_application_status_history_application_changed",
        "application_status_history",
        ["application_id", "changed_at"],
    )


def downgrade() -> None:
    """Remove primeiro o histórico, que depende da candidatura."""
    op.drop_table("application_status_history")
    op.drop_table("applications")
