"""Estado compartilhado pelos nós do pipeline de análise de vagas."""

from decimal import Decimal
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StringConstraints,
    model_validator,
)

from app.schemas.jobs import JobListQuery

# Limites do funil local escolhido na avaliação da F3-T06.
LLM_MIN_SCORE = Decimal("0.80")
LLM_TOP_N = 10


class _Contract(BaseModel):
    """Rejeita campos desconhecidos para detectar divergências entre nós."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ImportedJobs(_Contract):
    """Identifica o lote persistido e as vagas vinculadas a ele."""

    batch_id: UUID
    job_ids: tuple[UUID, ...]


class ScoredJob(_Contract):
    """Preserva o score do matching, inclusive o valor nulo em vaga eliminada."""

    job_id: UUID
    score: Annotated[Decimal, Field(ge=0, le=1, allow_inf_nan=False)] | None


class ItemError(_Contract):
    """Falha final de uma vaga, sem persistir texto de exceções ou dados do perfil."""

    job_id: UUID
    stage: Literal["matching", "analysis"]
    error_type: str
    attempts: Annotated[int, Field(ge=1, le=2)]


class MatchingResult(_Contract):
    """Vincula os resultados à versão usada para consultar o matching persistido."""

    scoring_version: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
    ]
    jobs: tuple[ScoredJob, ...]

    def top_job_ids(self) -> tuple[UUID, ...]:
        """Aplica o funil avaliado na F3-T06, com desempate estável por UUID."""
        eligible = [
            (job.score, job.job_id)
            for job in self.jobs
            if job.score is not None and job.score >= LLM_MIN_SCORE
        ]
        eligible.sort(key=lambda item: (item[0].copy_negate(), item[1]))
        return tuple(job_id for _, job_id in eligible[:LLM_TOP_N])


class PipelineState(_Contract):
    """Snapshot de uma execução. Um resultado ausente indica uma etapa pendente."""

    run_id: UUID
    candidate_id: UUID
    filters: JobListQuery = Field(default_factory=JobListQuery)
    llm_enabled: StrictBool = False
    imported: ImportedJobs | None = None
    normalized_ids: tuple[UUID, ...] | None = None
    deduplicated_ids: tuple[UUID, ...] | None = None
    filtered_ids: tuple[UUID, ...] | None = None
    matching: MatchingResult | None = None
    selected_ids: Annotated[tuple[UUID, ...], Field(max_length=LLM_TOP_N)] | None = None
    analyzed_ids: tuple[UUID, ...] | None = None
    errors: tuple[ItemError, ...] = ()

    @model_validator(mode="after")
    def _validate_stages(self) -> Self:
        """Confere a origem dos IDs para impedir que um nó introduza vagas alheias."""
        if self.filters.candidate_id not in (None, self.candidate_id):
            raise ValueError("O filtro deve pertencer ao candidato da execução.")

        stages = (
            self.imported.job_ids if self.imported is not None else None,
            self.normalized_ids,
            self.deduplicated_ids,
            self.filtered_ids,
            tuple(job.job_id for job in self.matching.jobs) if self.matching else None,
            self.selected_ids,
            self.analyzed_ids,
        )
        previous: set[UUID] | None = None
        for index, ids in enumerate(stages):
            if ids is None:
                previous = None
                continue
            current = set(ids)
            if len(current) != len(ids):
                raise ValueError("A etapa contém IDs de vaga repetidos.")
            if index and (previous is None or not current.issubset(previous)):
                raise ValueError("A etapa exige vagas da etapa anterior concluída.")
            previous = current

        if self.matching is not None and self.selected_ids:
            if not self.llm_enabled:
                raise ValueError("A seleção de vagas exige análise LLM habilitada.")
            if not set(self.selected_ids).issubset(self.matching.top_job_ids()):
                raise ValueError("A seleção exige vagas do top-10 com score ≥ 0,80.")
        if self.errors:
            for stage, inputs, outputs in (
                ("matching", self.filtered_ids, stages[4]),
                ("analysis", self.selected_ids, self.analyzed_ids),
            ):
                failed = [error.job_id for error in self.errors if error.stage == stage]
                if failed and (
                    outputs is None
                    or len(set(failed)) != len(failed)
                    or not set(failed).issubset(set(inputs or ()) - set(outputs))
                ):
                    raise ValueError(
                        "A falha deve corresponder a uma vaga sem resultado na etapa."
                    )
        return self
