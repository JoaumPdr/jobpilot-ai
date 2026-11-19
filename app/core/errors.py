"""Exceções de domínio e handlers de erro padronizados.

POR QUÊ: o cliente precisa de um formato único de erro (`error`, `message`,
`request_id` e, quando útil, `details`). Sem isso, cada rota inventaria um
formato e a depuração dependeria de ler o código.

As exceções de domínio não importam FastAPI: o serviço levanta
`NotFoundError`/`ConflictError` e só os handlers conhecem HTTP.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_ERROR_CODE_BY_STATUS = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    415: "unsupported_media_type",
    422: "validation_error",
}


def _request_id() -> str:
    """Recupera o `request_id` do contexto do structlog (middleware)."""
    return str(structlog.contextvars.get_contextvars().get("request_id", "unknown"))


def _error_content(
    error: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Monta o corpo de erro padrão, omitindo `details` quando vazio."""
    content: dict[str, Any] = {
        "error": error,
        "message": message,
        "request_id": _request_id(),
    }
    if details:
        content["details"] = details
    return content


class DomainError(Exception):
    """Erro de regra de negócio, traduzido em HTTP pelos handlers."""

    status_code: int = 500
    error: str = "internal_error"
    default_message: str = "Erro inesperado."

    def __init__(
        self,
        message: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


class NotFoundError(DomainError):
    """Recurso inexistente → HTTP 404."""

    status_code = 404
    error = "not_found"
    default_message = "Recurso não encontrado."


class ConflictError(DomainError):
    """Violação de unicidade/estado → HTTP 409."""

    status_code = 409
    error = "conflict"
    default_message = "Conflito com o estado atual do recurso."


class InvalidDataError(DomainError):
    """Regra de consistência que só pode ser checada com o estado atual → 422."""

    status_code = 422
    error = "invalid_data"
    default_message = "Dados inconsistentes com o estado atual do recurso."


def register_exception_handlers(app: FastAPI) -> None:
    """Registra os handlers de erro padronizados na aplicação."""

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        """Converte uma exceção de domínio no formato de erro padrão."""
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_content(exc.error, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Converte erros do Pydantic em 422 com a lista de campos inválidos."""
        details: list[dict[str, Any]] = []
        for error in exc.errors():
            location = [
                str(part)
                for part in error.get("loc", ())
                if part not in ("body", "query", "path", "header")
            ]
            details.append(
                {
                    "field": ".".join(location) or "body",
                    "message": error.get("msg", "Valor inválido."),
                    "type": error.get("type", "value_error"),
                }
            )
        return JSONResponse(
            status_code=422,
            content=_error_content(
                "validation_error",
                "Dados inválidos na requisição.",
                details,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Padroniza também os erros HTTP levantados pelo próprio FastAPI."""
        code = _ERROR_CODE_BY_STATUS.get(exc.status_code, "http_error")
        detail = exc.detail if isinstance(exc.detail, str) else "Erro HTTP."
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_content(code, detail),
            headers=getattr(exc, "headers", None),
        )
