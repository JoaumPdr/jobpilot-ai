"""Ponto de entrada da aplicação FastAPI.

POR QUÊ: Este arquivo monta a aplicação, registra o middleware de `request_id`
para rastreamento de requisições, configura o logging estruturado no startup
e instala um handler global de exceções para que todos os erros sigam um
formato único (JSON com `error`, `message` e `request_id`).
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import (
    applications,
    experiences,
    health,
    jobs,
    matching,
    pipeline,
    profile,
    skills,
)
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger

configure_logging(log_level=settings.log_level)
logger = get_logger(__name__)

app = FastAPI(
    title="JobPilot AI",
    description="Assistente pessoal para buscar, analisar e gerir candidaturas a vagas.",
    version="0.1.0",
)

# Handlers específicos (404/409/422 padronizados) antes do handler global 500.
register_exception_handlers(app)

app.include_router(health.router, prefix="")
app.include_router(profile.router, prefix="")
app.include_router(skills.router, prefix="")
app.include_router(experiences.router, prefix="")
app.include_router(jobs.router, prefix="")
app.include_router(applications.router, prefix="")
app.include_router(matching.router, prefix="")
app.include_router(pipeline.router)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Injeta um `request_id` único em cada requisição e nos logs estruturados.

    O `request_id` é gerado automaticamente, salvo nos `contextvars` do structlog
    para aparecer em todos os logs da requisição, e retornado no cabeçalho
    `X-Request-ID` da resposta para que o cliente possa correlacionar logs.

    Args:
        request: Requisição HTTP entrante.
        call_next: Próxima middleware ou handler de rota.

    Returns:
        Resposta HTTP com cabeçalho `X-Request-ID`.
    """
    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=request_id)

    try:
        response = await call_next(request)
    finally:
        structlog.contextvars.clear_contextvars()

    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções para formato de erro único.

    Qualquer exceção não tratada retorna HTTP 500 com corpo JSON padronizado,
    incluindo o `request_id` para correlação com os logs.

    Args:
        request: Requisição que gerou a exceção.
        exc: Exceção capturada.

    Returns:
        Resposta JSON com formato de erro padronizado.
    """
    request_id = structlog.contextvars.get_contextvars().get("request_id", "unknown")
    logger.exception(
        "unhandled_exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "Ocorreu um erro inesperado. Tente novamente mais tarde.",
            "request_id": request_id,
        },
    )


@app.on_event("startup")
def on_startup() -> None:
    """Executa ações de inicialização da aplicação."""
    logger.info(
        "application_starting",
        app_env=settings.app_env,
        log_level=settings.log_level,
    )


@app.on_event("shutdown")
def on_shutdown() -> None:
    """Executa ações de encerramento da aplicação."""
    logger.info("application_shutting_down")
