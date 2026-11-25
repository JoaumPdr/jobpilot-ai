import json
import traceback
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.llm import providers
from app.llm.providers import (
    FakeLLMProvider,
    LLMProvider,
    LLMProviderError,
    LLMResponse,
    OllamaProvider,
    build_llm_provider,
)


def test_troca_de_provedor_por_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for field in Settings.model_fields:
        if field.startswith("llm_"):
            monkeypatch.delenv(field.upper(), raising=False)

    env = tmp_path / ".env"
    env.write_text(
        "DATABASE_URL=postgresql://localhost/jobpilot_test\n", encoding="utf-8"
    )
    assert build_llm_provider(Settings(_env_file=env)) is None

    with env.open("a", encoding="utf-8") as file:
        file.write("LLM_PROVIDER=fake\n")
    fake = build_llm_provider(Settings(_env_file=env))
    assert isinstance(fake, FakeLLMProvider)
    assert fake.complete(system_prompt="", user_prompt="").text == "{}"

    with env.open("a", encoding="utf-8") as file:
        file.write(
            "LLM_PROVIDER=ollama\nLLM_MODEL=modelo-local\nLLM_OLLAMA_PORT=12000\n"
            "LLM_TIMEOUT=12\nLLM_MAX_TOKENS=80\nLLM_RETRIES=1\nLLM_BUDGET_USD=0\n"
            "LLM_API_KEY=chave-sintetica\n"
        )
    config = Settings(_env_file=env)
    ollama = build_llm_provider(config)
    assert ollama == OllamaProvider(
        model="modelo-local", port=12000, timeout=12, max_tokens=80, retries=1
    )
    assert config.llm_budget_usd == 0
    assert "chave-sintetica" not in repr(config)
    assert "chave-sintetica" not in config.model_dump_json()


@pytest.mark.parametrize(
    ("provider", "message"),
    [("inexistente", "LLM_PROVIDER"), ("ollama", "LLM_MODEL")],
)
def test_fabrica_rejeita_provedor_ou_modelo_invalido(
    provider: str, message: str
) -> None:
    config = Settings(
        _env_file=None,
        database_url="postgresql://localhost/jobpilot_test",
        llm_provider=provider,
        llm_model=" ",
    )
    with pytest.raises(ValueError, match=message):
        build_llm_provider(config)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("llm_timeout", 0),
        ("llm_max_tokens", 0),
        ("llm_budget_usd", -1),
        ("llm_budget_usd", float("inf")),
        ("llm_retries", -1),
        ("llm_retries", 6),
        ("llm_ollama_port", 0),
        ("llm_ollama_port", 65536),
    ],
)
def test_rejeita_limites_invalidos(field: str, value: float) -> None:
    with pytest.raises(ValidationError, match=field):
        Settings.model_validate(
            {"database_url": "postgresql://localhost/jobpilot_test", field: value}
        )


def test_falso_devolve_resposta_configurada() -> None:
    response = LLMResponse("texto sintético", tokens_in=3, tokens_out=2)
    provider: LLMProvider = FakeLLMProvider(response=response)
    assert provider.name == provider.model == "fake"
    assert provider.complete(system_prompt="instrução", user_prompt="dados") == response
    assert "texto sintético" not in repr(response)


@pytest.fixture
def ollama() -> OllamaProvider:
    return OllamaProvider(
        model="teste", port=12000, timeout=7, max_tokens=23, retries=2
    )


@pytest.fixture
def transport(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock()
    monkeypatch.setattr(providers.http.client, "HTTPConnection", mock)
    return mock


def _response(status: int = 200, body: bytes = b"") -> Mock:
    response = Mock(status=status)
    response.read.return_value = body
    return response


def test_ollama_envia_pedidos_separados_e_retorna_uso(
    ollama: OllamaProvider, transport: Mock
) -> None:
    connection = transport.return_value
    connection.getresponse.return_value = _response(
        body=b'{"message":{"content":"resultado"},"done":true,"prompt_eval_count":9,"eval_count":2}'
    )
    result = ollama.complete(system_prompt="instruções", user_prompt="dados")

    transport.assert_called_once_with("127.0.0.1", 12000, timeout=7)
    args, kwargs = connection.request.call_args
    assert args == ("POST", "/api/chat")
    assert kwargs["headers"] == {"Content-Type": "application/json"}
    assert json.loads(kwargs["body"]) == {
        "model": "teste",
        "messages": [
            {"role": "system", "content": "instruções"},
            {"role": "user", "content": "dados"},
        ],
        "stream": False,
        "options": {"num_predict": 23},
    }
    assert result == LLMResponse("resultado", tokens_in=9, tokens_out=2)
    connection.close.assert_called_once_with()


def test_ollama_repete_apenas_ate_o_limite(
    ollama: OllamaProvider, transport: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    sleep = Mock()
    monkeypatch.setattr(providers.time, "sleep", sleep)
    connection = transport.return_value
    unavailable = _response(status=503)
    connection.getresponse.side_effect = [TimeoutError(), unavailable, unavailable]

    with pytest.raises(LLMProviderError, match="503"):
        ollama.complete(system_prompt="", user_prompt="")

    assert connection.request.call_count == connection.close.call_count == 3
    assert [call.args for call in sleep.call_args_list] == [(0.25,), (0.5,)]
    unavailable.read.assert_not_called()


def test_ollama_pode_recuperar_apos_falha_transitoria(
    ollama: OllamaProvider, transport: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    sleep = Mock()
    monkeypatch.setattr(providers.time, "sleep", sleep)
    transport.return_value.getresponse.side_effect = [
        ConnectionRefusedError(),
        _response(body=b'{"message":{"content":"ok"},"done":true}'),
    ]
    assert ollama.complete(system_prompt="", user_prompt="") == LLMResponse("ok")
    sleep.assert_called_once_with(0.25)


@pytest.mark.parametrize(
    ("status", "body", "message"),
    [
        (302, b"dados-sinteticos", "302"),
        (400, b"dados-sinteticos", "400"),
        (200, b"dados-sinteticos", "inválida"),
        (200, b'{"message":{"content":"ok"},"done":false}', "incompleta"),
        (200, b'{"message":{"content":123},"done":true}', "inválida"),
        (200, b'{"message":{"content":"ok"},"done":true,"eval_count":-1}', "inválida"),
    ],
)
def test_ollama_nao_repete_erro_definitivo_nem_expoe_dados(
    ollama: OllamaProvider,
    transport: Mock,
    status: int,
    body: bytes,
    message: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    connection = transport.return_value
    response = _response(status, body)
    connection.getresponse.return_value = response
    system_prompt = "chave-sintetica"
    user_prompt = "dados-sinteticos"

    with pytest.raises(LLMProviderError, match=message) as error:
        ollama.complete(system_prompt=system_prompt, user_prompt=user_prompt)

    error_output = "".join(traceback.format_exception(error.value)) + caplog.text
    assert system_prompt not in error_output
    assert user_prompt not in error_output
    if status != 200:
        response.read.assert_not_called()
    connection.request.assert_called_once()
    connection.close.assert_called_once()
