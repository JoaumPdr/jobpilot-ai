"""Execuções do pipeline com snapshot e auditoria por run_id."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "000000000008"
down_revision = "000000000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Cria o registro de execução independente dos lotes já existentes."""
    op.create_table(
        "pipeline_runs",
        sa.Column("run_id", sa.Uuid(), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("params", JSONB(), nullable=False),
        sa.Column("counters", JSONB(), nullable=False),
        sa.Column("errors", JSONB(), nullable=False),
        sa.Column("state_snapshot", JSONB(), nullable=False),
        sa.CheckConstraint(
            "status IN ('running', 'failed', 'partial', 'completed')",
            name="ck_pipeline_runs_status",
        ),
    )


def downgrade() -> None:
    """Remove os registros de execução e preserva os dados das vagas."""
    op.drop_table("pipeline_runs")
