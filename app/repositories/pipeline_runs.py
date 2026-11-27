"""Reserva e bloqueio do registro que coordena os efeitos de cada nó."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models import PipelineRun
from app.repositories.base import BaseRepository


class PipelineRunRepository(BaseRepository):
    """Serializa chamadas com o mesmo UUID no PostgreSQL."""

    def get(self, run_id: UUID) -> PipelineRun | None:
        """Lê o último estado confirmado sem bloquear o nó em andamento."""
        return self._db.get(PipelineRun, run_id)

    def reserve(
        self, run_id: UUID, params: dict[str, Any], snapshot: dict[str, Any]
    ) -> None:
        """Preserva o primeiro vínculo entre a chave e os parâmetros do lote."""
        self._db.execute(
            insert(PipelineRun)
            .values(
                id=run_id,
                params=params,
                state_snapshot=snapshot,
                status="running",
                started_at=datetime.now(UTC),
                counters={},
                errors=[],
            )
            .on_conflict_do_nothing(index_elements=[PipelineRun.id])
        )

    def lock(self, run_id: UUID) -> PipelineRun:
        """Espera o nó concorrente e então lê o último snapshot confirmado."""
        return self._db.scalars(
            select(PipelineRun).where(PipelineRun.id == run_id).with_for_update()
        ).one()
