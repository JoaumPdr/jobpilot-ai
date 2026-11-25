"""Análises LLM validadas e métricas da geração que as produziu."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LLMCache(Base):
    """Resultado reutilizável para uma combinação de entrada e provedor."""

    __tablename__ = "llm_cache"

    cache_key: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(nullable=False)
    model: Mapped[str] = mapped_column(nullable=False)
    prompt_version: Mapped[str] = mapped_column(nullable=False)
    response: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    tokens_in: Mapped[int | None]
    tokens_out: Mapped[int | None]
    cost_estimate: Mapped[Decimal | None] = mapped_column(Numeric())
    latency_ms: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("cache_key", name="uq_llm_cache_key"),
        CheckConstraint(
            "tokens_in >= 0 AND tokens_out >= 0 AND cost_estimate >= 0 AND latency_ms >= 0",
            name="ck_llm_cache_nonnegative_metrics",
        ),
        CheckConstraint(
            "jsonb_typeof(response) = 'object'", name="ck_llm_cache_response_object"
        ),
    )
