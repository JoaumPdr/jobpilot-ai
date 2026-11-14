"""Configuração da aplicação usando Pydantic Settings.

Este módulo centraliza a leitura de variáveis de ambiente e validação de configuração.
Usa `pydantic-settings` para tipagem e validação automática.

POR QUÊ: Evita espalhar `os.getenv` pelo código; garante que variáveis obrigatórias
existam no startup; fornece defaults sensatos e documentação via type hints.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do ambiente (.env)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Banco de dados
    database_url: str = Field(
        description="URL de conexão PostgreSQL (ex: postgresql+psycopg://user:pass@host:port/db)"
    )

    # Ambiente da aplicação
    app_env: str = Field(
        default="development", description="Ambiente: development, staging, production"
    )
    log_level: str = Field(
        default="INFO", description="Nível de log: DEBUG, INFO, WARNING, ERROR"
    )

    # LLM (Fase 3+)
    llm_provider: str | None = Field(
        default=None, description="Provedor LLM: openai, anthropic, etc."
    )
    llm_model: str | None = Field(default=None, description="Modelo LLM a usar")
    llm_api_key: str | None = Field(
        default=None, description="Chave da API do provedor LLM"
    )
    llm_timeout: int = Field(
        default=30, description="Timeout em segundos para chamadas LLM"
    )
    llm_max_tokens: int = Field(
        default=4096, description="Máximo de tokens por resposta LLM"
    )
    llm_budget_usd: float = Field(
        default=10.0, description="Orçamento máximo em USD por execução"
    )

    # Embeddings (Fase 2+)
    embedding_provider: str | None = Field(
        default=None, description="Provedor de embeddings"
    )
    embedding_model: str | None = Field(
        default=None, description="Modelo de embeddings"
    )
    embedding_api_key: str | None = Field(
        default=None, description="Chave da API de embeddings"
    )


# Instância global de configuração (carregada uma vez no startup)
settings = Settings()  # type: ignore[call-arg]
