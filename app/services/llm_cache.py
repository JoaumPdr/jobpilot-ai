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
from app.llm.job_analysis import (
    JobAnalysisOutput,
    JobAnalysisOutputError,
    JobAnalysisPrompt,
    VersionedJobAnalysis,
)
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
        repair: JobAnalysisPrompt | None = None,
    ) -> VersionedJobAnalysis:
        """Revalida resultados reutilizados e grava somente após a validação da saída."""
        cache_key = self._cache_key(inputs, repair=repair)
        version = inputs.prompt.version
        try:
            # A sessão própria libera o bloqueio sem confirmar os dados do chamador.
            with self._sessions.begin() as db:
                cache = LLMCacheRepository(db)
                cache.lock(cache_key)
                stored = cache.get(cache_key)
                if stored is not None:
                    analysis = validate(json.dumps(stored.response, ensure_ascii=False))
                    version = stored.prompt_version
                    logger.info(
                        "llm_cache_hit",
                        provider=self._provider.name,
                        model=self._provider.model,
                        prompt_version=version,
                    )
                else:
                    reply, cost, latency_ms = self._complete(inputs)
                    try:
                        analysis = validate(reply.text)
                    except JobAnalysisOutputError:
                        if repair is None:
                            raise
                        version = repair.version
                        repair_input = JobAnalysisInput(repair, inputs.user_prompt)
                        reply, cost, latency_ms = self._complete(repair_input)
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

    def _cache_key(
        self, inputs: JobAnalysisInput, *, repair: JobAnalysisPrompt | None
    ) -> str:
        parts = (
            self._provider.name,
            self._provider.model,
            inputs.prompt.version,
            inputs.prompt.system_prompt,
            inputs.user_prompt,
        )
        if repair is not None:
            parts += (repair.version, repair.system_prompt)
        material = json.dumps(
            parts,
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
