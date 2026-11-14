"""Configuração de logging estruturado com structlog.

POR QUÊ: Usar logs estruturados (JSON) permite agregar e consultar logs em
ferramentas de observabilidade. O `request_id` é injetado em cada requisição
via middleware para rastrear uma requisição end-to-end pelos serviços.
"""

import logging
import sys

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Configura logging estruturado para a aplicação.

    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR).
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Retorna um logger estruturado para o módulo informado.

    Args:
        name: Nome do módulo (geralmente `__name__`).

    Returns:
        Instância de BoundLogger configurada.
    """
    return structlog.get_logger(name)
