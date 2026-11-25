"""Reutiliza análises validadas e mede chamadas ao provedor."""

import json
from collections.abc import Callable
from decimal import Decimal
from hashlib import sha256
from time import perf_counter_ns

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.llm.job_analysis import JobAnalysisOutput, VersionedJobAnalysis
from app.llm.providers import LLMProvider, LLMResponse
from app.models import LLMCache
from app.repositories.llm_cache import LLMCacheRepository
from app.services.llm_input import JobAnalysisInput

logger = get_logger(__name__)


class LLMCacheError(RuntimeError):
    """Falha de persistência com mensagem segura para os logs."""


class LLMCacheService:
    """Gera uma análise no primeiro acesso e reutiliza o resultado validado."""

    def __init__(
        self, provider: LLMProvider, *, sessions: sessionmaker[Session] = SessionLocal
    ) -> None:
        self._provider = provider
        self._sessions = sessions

    def get_or_generate(
        self,
        inputs: JobAnalysisInput,
        *,
        validate: Callable[[str], JobAnalysisOutput],
    ) -> VersionedJobAnalysis:
        """Revalida resultados reutilizados e grava somente após a validação da saída."""
        cache_key = self._cache_key(inputs)
        version = inputs.prompt.version
        try:
            # A sessão própria libera o bloqueio sem confirmar os dados do chamador.
            with self._sessions.begin() as db:
                cache = LLMCacheRepository(db)
                cache.lock(cache_key)
                stored = cache.get(cache_key)
                if stored is not None:
                    analysis = validate(json.dumps(stored.response, ensure_ascii=False))
                    logger.info(
                        "llm_cache_hit",
                        provider=self._provider.name,
                        model=self._provider.model,
                        prompt_version=version,
                    )
                else:
                    reply, cost, latency_ms = self._complete(inputs)
                    analysis = validate(reply.text)
                    cache.add(
                        LLMCache(
                            cache_key=cache_key,
                            provider=self._provider.name,
                            model=self._provider.model,
                            prompt_version=version,
                            response=analysis.model_dump(mode="json"),
                            tokens_in=reply.tokens_in,
                            tokens_out=reply.tokens_out,
                            cost_estimate=cost,
                            latency_ms=latency_ms,
                        )
                    )
        except SQLAlchemyError:
            # Exceções do driver podem incluir parâmetros SQL com trechos da resposta.
            raise LLMCacheError("Falha ao acessar o cache de análises LLM.") from None

        return VersionedJobAnalysis(prompt_version=version, analysis=analysis)

    def _cache_key(self, inputs: JobAnalysisInput) -> str:
        material = json.dumps(
            (
                self._provider.name,
                self._provider.model,
                inputs.prompt.version,
                inputs.prompt.system_prompt,
                inputs.user_prompt,
            ),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return sha256(material.encode("utf-8")).hexdigest()

    def _complete(
        self, inputs: JobAnalysisInput
    ) -> tuple[LLMResponse, Decimal | None, int]:
        # Os provedores locais não cobram por chamada. Ausência de tarifa é desconhecida.
        cost = Decimal(0) if self._provider.name in {"fake", "ollama"} else None
        reply: LLMResponse | None = None
        start = perf_counter_ns()
        try:
            reply = self._provider.complete(
                system_prompt=inputs.prompt.system_prompt,
                user_prompt=inputs.user_prompt,
            )
        finally:
            latency_ms = (perf_counter_ns() - start) // 1_000_000
            logger.info(
                "llm_call",
                provider=self._provider.name,
                model=self._provider.model,
                prompt_version=inputs.prompt.version,
                status="returned" if reply is not None else "provider_error",
                tokens_in=reply.tokens_in if reply is not None else None,
                tokens_out=reply.tokens_out if reply is not None else None,
                cost_estimate_usd=str(cost) if cost is not None else None,
                latency_ms=latency_ms,
            )
        return reply, cost, latency_ms
