"""Executa lotes solicitados pela API e consulta seus registros duráveis."""

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from app.core.errors import InvalidDataError, NotFoundError
from app.llm.providers import LLMProvider
from app.orchestration.persistence import run_persisted_pipeline
from app.orchestration.state import PipelineState
from app.repositories.pipeline_runs import PipelineRunRepository
from app.repositories.profile import CandidateRepository
from app.schemas.jobs import JobListQuery
from app.schemas.pipeline_runs import PipelineRunRead
from app.services.job_import import MAX_CSV_BYTES


class PipelineRunService:
    """Usa o mesmo banco da requisição para os commits independentes de cada nó."""

    def __init__(
        self,
        sessions: sessionmaker[Session],
        provider_factory: Callable[[], LLMProvider | None],
    ) -> None:
        self._sessions = sessions
        self._provider_factory = provider_factory

    def get(self, run_id: UUID) -> PipelineRunRead:
        """Lê uma execução pelo UUID ou levanta NotFoundError."""
        with self._sessions() as db:
            run = PipelineRunRepository(db).get(run_id)
            if run is None:
                raise NotFoundError("Execução do pipeline não encontrada.")
            return PipelineRunRead.model_validate(run, from_attributes=True)

    def execute(
        self,
        run_id: UUID,
        candidate_id: UUID,
        *,
        content: bytes,
        filename: str | None,
        source: str | None,
        filters: JobListQuery,
        llm_enabled: bool,
    ) -> PipelineRunRead:
        """Processa ou retoma o CSV e devolve a mesma representação oferecida pela consulta."""
        if len(content) > MAX_CSV_BYTES:
            raise InvalidDataError("O CSV excede o limite de 5 MB.")
        if filename and (len(filename) > 255 or "\x00" in filename):
            raise InvalidDataError("Nome do arquivo inválido.")
        if b"\x00" in content or (source and "\x00" in source):
            raise InvalidDataError(
                "O CSV e a origem devem conter texto sem caracteres nulos."
            )
        if filters.candidate_id not in (None, candidate_id):
            raise InvalidDataError("O filtro deve pertencer ao candidato da execução.")
        with self._sessions() as db:
            if not CandidateRepository(db).exists(candidate_id):
                raise NotFoundError("Candidato não encontrado.")
        provider = self._provider_factory() if llm_enabled else None
        if llm_enabled and provider is None:
            raise InvalidDataError("A análise exige um provedor LLM configurado.")
        state = PipelineState(
            run_id=run_id,
            candidate_id=candidate_id,
            filters=filters,
            llm_enabled=llm_enabled,
        )
        run_persisted_pipeline(
            state,
            content=content,
            filename=filename,
            source=source,
            provider=provider,
            sessions=self._sessions,
        )
        return self.get(run_id)
