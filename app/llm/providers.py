"""Contrato de geração e seleção do provedor LLM configurado."""

import http.client
import json
import time
from dataclasses import dataclass, field
from typing import ClassVar, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import Settings


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Texto em bruto e uso de tokens quando o provedor o informa."""

    text: str = field(repr=False)
    tokens_in: int | None = None
    tokens_out: int | None = None


class LLMProvider(Protocol):
    """Gera uma resposta a partir de instruções e dados separados."""

    @property
    def name(self) -> str: ...

    @property
    def model(self) -> str: ...

    def complete(self, *, system_prompt: str, user_prompt: str) -> LLMResponse: ...


class LLMProviderError(RuntimeError):
    """Falha do provedor com mensagem segura para diagnóstico."""


class _TransientError(LLMProviderError):
    """Falha que admite outra tentativa."""


@dataclass(frozen=True, slots=True)
class FakeLLMProvider:
    """Devolve a resposta configurada sem acessar a rede."""

    name: ClassVar[str] = "fake"
    model: str = "fake"
    response: LLMResponse = LLMResponse(text="{}")

    def complete(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        return self.response


class _OllamaMessage(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str


class _OllamaResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    done: bool
    message: _OllamaMessage
    prompt_eval_count: int | None = Field(default=None, ge=0)
    eval_count: int | None = Field(default=None, ge=0)


@dataclass(frozen=True, slots=True)
class OllamaProvider:
    """Adaptador para a API de chat do Ollama na máquina local."""

    name: ClassVar[str] = "ollama"
    model: str
    port: int
    timeout: int
    max_tokens: int
    retries: int

    def complete(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {"num_predict": self.max_tokens},
            }
        )
        for attempt in range(self.retries):
            try:
                return self._request(body)
            except _TransientError:
                # O teto mantém a espera previsível mesmo com várias tentativas.
                time.sleep(min(0.25 * 2**attempt, 2.0))
        return self._request(body)

    def _request(self, body: str) -> LLMResponse:
        # A conexão direta impede que proxies ou redirecionamentos encaminhem o prompt.
        connection = http.client.HTTPConnection(
            "127.0.0.1", self.port, timeout=self.timeout
        )
        try:
            connection.request(
                "POST",
                "/api/chat",
                body=body,
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            if response.status in {408, 429, 500, 502, 503, 504}:
                raise _TransientError(
                    f"Falha temporária do Ollama (HTTP {response.status})."
                )
            if response.status != 200:
                raise LLMProviderError(
                    f"Ollama recusou a chamada (HTTP {response.status})."
                )
            raw = response.read()
        except TimeoutError:
            raise _TransientError("Ollama excedeu o timeout de rede.") from None
        except OSError:
            raise _TransientError("Conexão com o Ollama local indisponível.") from None
        except http.client.HTTPException:
            raise LLMProviderError("Falha no protocolo HTTP do Ollama.") from None
        finally:
            connection.close()

        try:
            result = _OllamaResponse.model_validate_json(raw)
        except ValidationError:
            # O servidor pode devolver dados do prompt em uma resposta malformada.
            raise LLMProviderError("Ollama retornou uma resposta inválida.") from None

        if not result.done:
            raise LLMProviderError("Ollama retornou uma resposta incompleta.")
        return LLMResponse(
            result.message.content, result.prompt_eval_count, result.eval_count
        )


def build_llm_provider(config: Settings) -> LLMProvider | None:
    """Resolve o provedor a partir das configurações sem conectar ao servidor."""
    provider = (config.llm_provider or "").strip().lower()
    model = (config.llm_model or "").strip()
    if not provider:
        return None
    if provider == "fake":
        return FakeLLMProvider(model=model or "fake")
    if provider != "ollama":
        raise ValueError("LLM_PROVIDER deve ser fake ou ollama.")
    if not model:
        raise ValueError("LLM_MODEL é obrigatório quando LLM_PROVIDER=ollama.")
    return OllamaProvider(
        model=model,
        port=config.llm_ollama_port,
        timeout=config.llm_timeout,
        max_tokens=config.llm_max_tokens,
        retries=config.llm_retries,
    )
