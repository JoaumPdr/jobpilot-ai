"""Persistência e bloqueio por chave para o cache LLM em PostgreSQL."""

from sqlalchemy import func, select

from app.models import LLMCache
from app.repositories.base import BaseRepository


class LLMCacheRepository(BaseRepository):
    """Coordena leitores e escritores da mesma entrada até o fim da transação."""

    def lock(self, cache_key: str) -> None:
        """Adquire um bloqueio transacional identificado pelo prefixo da chave."""
        lock_id = int.from_bytes(
            bytes.fromhex(cache_key[:16]), byteorder="big", signed=True
        )
        self._db.execute(select(func.pg_advisory_xact_lock(lock_id)))

    def get(self, cache_key: str) -> LLMCache | None:
        return self._db.scalar(select(LLMCache).where(LLMCache.cache_key == cache_key))

    def add(self, entry: LLMCache) -> None:
        self._db.add(entry)
