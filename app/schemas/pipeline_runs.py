"""Resposta HTTP compartilhada pela execução e pela consulta do pipeline."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

from app.orchestration.state import ItemError, PipelineState, ScoredJob


class PipelineStageError(BaseModel):
    """Falha do lote. O texto original da exceção permanece fora da resposta."""

    stage: str
    error_type: str


class PipelineRunRead(BaseModel):
    """Última etapa confirmada de uma execução, inclusive durante a retomada."""

    run_id: UUID = Field(validation_alias="id")
    status: Literal["running", "completed", "partial", "failed"]
    started_at: datetime
    finished_at: datetime | None
    counters: dict[str, int]
    errors: list[ItemError | PipelineStageError]
    state_snapshot: PipelineState

    @computed_field
    @property
    def recommendations_for_review(self) -> tuple[ScoredJob, ...] | None:
        """Apresenta o ranking do snapshot usando a regra de revisão da F4-T06."""
        return self.state_snapshot.recommendations_for_review
