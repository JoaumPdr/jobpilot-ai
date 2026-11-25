import json
import traceback
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from threading import Event
from time import monotonic, sleep
from unittest.mock import Mock
from uuid import UUID

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, delete, inspect, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.llm.job_analysis import (
    JobAnalysisOutput,
    JobAnalysisOutputError,
    load_job_analysis_prompt,
    parse_job_analysis,
)
from app.llm.providers import (
    FakeLLMProvider,
    LLMProvider,
    LLMProviderError,
    LLMResponse,
)
from app.models import Candidate, LLMCache
from app.schemas.matching import MatchAnalysis
from app.services import llm_cache
from app.services.llm_cache import LLMCacheError, LLMCacheService
from app.services.llm_input import JobAnalysisInput, prepare_job_analysis_input

_JOB_ID = UUID("f53bbe32-c7df-42ef-81db-abf5016cde4e")
_DESCRIPTION = "Descrição sintética da vaga de Python."
_EVIDENCE = "Trecho sintético com Python."
_RESPONSE = json.dumps(
    {
        "job_id": str(_JOB_ID),
        "matched_skills": [],
        "missing_skills": [],
        "unknown_requirements": ["Python"],
        "recommendation": "Confirmar habilidades.",
        "explanation": _EVIDENCE,
        "evidence": [],
    }
)


@pytest.fixture
def sessions(test_engine: Engine) -> Iterator[sessionmaker[Session]]:
    yield sessionmaker(bind=test_engine, autoflush=False)
    with test_engine.begin() as connection:
        connection.execute(delete(LLMCache))


@pytest.fixture
def inputs() -> JobAnalysisInput:
    return prepare_job_analysis_input(
        job_id=_JOB_ID,
        description=_DESCRIPTION,
        matching=MatchAnalysis(
            weighted_sum=Decimal(0),
            total_weight=Decimal(0),
            met=[],
            absent=[],
            unconfirmed=[],
        ),
    )


def _fake(
    *, model: str = "teste", name: str = "fake", reply: LLMResponse | None = None
) -> Mock:
    fake = FakeLLMProvider(model=model, response=reply or LLMResponse(_RESPONSE, 11, 5))
    provider = Mock(spec=LLMProvider)
    provider.name = name
    provider.model = model
    provider.complete.side_effect = fake.complete
    return provider


def _validate(response: str) -> JobAnalysisOutput:
    return parse_job_analysis(
        response, expected_job_id=_JOB_ID, prompt=load_job_analysis_prompt()
    ).analysis


def test_reutiliza_analise_e_persiste_metricas_de_uma_chamada(
    sessions: sessionmaker[Session],
    inputs: JobAnalysisInput,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _fake()
    log = Mock()
    monkeypatch.setattr(llm_cache, "logger", log)

    original = LLMCacheService(provider, sessions=sessions)
    result = original.get_or_generate(inputs, validate=_validate)
    regenerated = LLMCacheService(provider, sessions=sessions)
    assert regenerated.get_or_generate(inputs, validate=_validate) == result
    provider.complete.assert_called_once_with(
        system_prompt=inputs.prompt.system_prompt, user_prompt=inputs.user_prompt
    )

    with sessions() as db:
        stored = db.scalars(select(LLMCache)).one()
        assert len(stored.cache_key) == 64
        assert stored.response == result.analysis.model_dump(mode="json")
        assert stored.prompt_version == result.prompt_version
        assert stored.created_at.tzinfo is not None
        assert (stored.tokens_in, stored.tokens_out, stored.cost_estimate) == (11, 5, 0)
        assert stored.latency_ms >= 0

    call_log, hit_log = log.info.call_args_list
    assert call_log.args == ("llm_call",)
    assert call_log.kwargs == {
        "provider": "fake",
        "model": "teste",
        "prompt_version": inputs.prompt.version,
        "status": "returned",
        "tokens_in": 11,
        "tokens_out": 5,
        "cost_estimate_usd": "0",
        "latency_ms": stored.latency_ms,
    }
    assert hit_log.args == ("llm_cache_hit",)
    rendered = str(log.info.call_args_list)
    assert all(
        item not in rendered for item in (_DESCRIPTION, _EVIDENCE, inputs.user_prompt)
    )


def test_chave_separa_entrada_prompt_versao_modelo_e_provedor(
    sessions: sessionmaker[Session], inputs: JobAnalysisInput
) -> None:
    provider = _fake()
    changed_model = _fake(model="outro modelo")
    changed_provider = _fake(name="provedor-sintetico", reply=LLMResponse(_RESPONSE))
    variants = [
        (provider, inputs),
        (provider, replace(inputs, user_prompt="outra entrada")),
        (
            provider,
            replace(inputs, prompt=replace(inputs.prompt, version="versao-teste")),
        ),
        (
            provider,
            replace(
                inputs, prompt=replace(inputs.prompt, system_prompt="outro prompt")
            ),
        ),
        (changed_model, inputs),
        (changed_provider, inputs),
    ]
    for selected, supplied in variants:
        result = LLMCacheService(selected, sessions=sessions).get_or_generate(
            supplied, validate=_validate
        )
        assert result.prompt_version == supplied.prompt.version

    assert provider.complete.call_count == 4
    changed_model.complete.assert_called_once()
    changed_provider.complete.assert_called_once()
    with sessions() as db:
        records = db.scalars(select(LLMCache)).all()
        assert len({entry.cache_key for entry in records}) == len(variants)
        unknown = next(
            entry for entry in records if entry.provider == changed_provider.name
        )
        assert (unknown.tokens_in, unknown.tokens_out, unknown.cost_estimate) == (
            None,
            None,
            None,
        )


def test_falhas_registram_metricas_e_permitem_nova_tentativa(
    sessions: sessionmaker[Session],
    inputs: JobAnalysisInput,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _fake()
    provider.complete.side_effect = [
        LLMProviderError("Falha de teste."),
        LLMResponse(_EVIDENCE, 7, 2),
        LLMResponse(_RESPONSE, 11, 5),
    ]
    log = Mock()
    monkeypatch.setattr(llm_cache, "logger", log)
    service = LLMCacheService(provider, sessions=sessions)

    with pytest.raises(LLMProviderError):
        service.get_or_generate(inputs, validate=_validate)
    with pytest.raises(JobAnalysisOutputError):
        service.get_or_generate(inputs, validate=_validate)
    with sessions() as db:
        assert db.scalars(select(LLMCache)).first() is None

    assert service.get_or_generate(inputs, validate=_validate).analysis == _validate(
        _RESPONSE
    )
    assert provider.complete.call_count == 3
    error_log, invalid_log, successful_log = log.info.call_args_list
    assert error_log.kwargs["status"] == "provider_error"
    assert error_log.kwargs["tokens_in"] is None
    assert invalid_log.kwargs["tokens_in"] == 7
    assert successful_log.kwargs["tokens_in"] == 11
    assert _EVIDENCE not in str(log.info.call_args_list)


def test_falha_de_gravacao_oculta_conteudo_do_sql(
    sessions: sessionmaker[Session], inputs: JobAnalysisInput
) -> None:
    provider = _fake(reply=LLMResponse(_RESPONSE, tokens_in=-1))
    service = LLMCacheService(provider, sessions=sessions)

    with pytest.raises(LLMCacheError, match="Falha ao acessar o cache") as error:
        service.get_or_generate(inputs, validate=_validate)

    assert _EVIDENCE not in "".join(traceback.format_exception(error.value))
    with sessions() as db:
        assert db.scalars(select(LLMCache)).first() is None


def test_consultas_concorrentes_compartilham_uma_geracao(
    test_engine: Engine, sessions: sessionmaker[Session], inputs: JobAnalysisInput
) -> None:
    entered = Event()
    finish = Event()
    provider = _fake()

    def complete(**_messages: str) -> LLMResponse:
        entered.set()
        assert finish.wait(timeout=15)
        return LLMResponse(_RESPONSE, 11, 5)

    provider.complete.side_effect = complete
    service = LLMCacheService(provider, sessions=sessions)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(service.get_or_generate, inputs, validate=_validate)
        try:
            assert entered.wait(timeout=5)
            second = executor.submit(
                service.get_or_generate, inputs, validate=_validate
            )
            waits_in_postgres = text(
                "SELECT EXISTS (SELECT 1 FROM pg_locks WHERE locktype = 'advisory' "
                "AND NOT granted AND database = "
                "(SELECT oid FROM pg_database WHERE datname = current_database()))"
            )
            with test_engine.connect() as connection:
                until = monotonic() + 5
                while not connection.scalar(waits_in_postgres):
                    assert monotonic() < until
                    sleep(0.02)
        finally:
            finish.set()
        assert first.result(timeout=5) == second.result(timeout=5)
    provider.complete.assert_called_once()


def test_migracao_cache_remove_so_o_cache_e_pode_reaplicar(
    test_engine: Engine, sessions: sessionmaker[Session]
) -> None:
    with sessions.begin() as db:
        candidate = Candidate(name="Perfil de teste", resume_text="Texto sintético")
        db.add(candidate)
        db.flush()
        candidate_id = candidate.id

    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.set_main_option(
        "sqlalchemy.url",
        test_engine.url.render_as_string(hide_password=False).replace("%", "%%"),
    )
    try:
        command.downgrade(config, "000000000006")
        inspector = inspect(test_engine)
        assert not inspector.has_table("llm_cache")
        assert inspector.has_table("job_matches")
        command.upgrade(config, "000000000007")
        assert inspect(test_engine).has_table("llm_cache")
        with sessions() as db:
            assert db.get(Candidate, candidate_id) is not None
    finally:
        command.upgrade(config, "head")
        with sessions.begin() as db:
            db.execute(delete(Candidate).where(Candidate.id == candidate_id))
