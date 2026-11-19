"""Repositório de vagas: consultas de deduplicação e escrita.

POR QUÊ: as três primeiras camadas da dedup (`PLANO.md` §6.3) são consultas
simples, mas o serviço não deve montar `select` — assim ele fica testável com um
dublê em memória e a otimização (índice, limite, ordenação) mora em um só lugar.
"""

from __future__ import annotations

from sqlalchemy import select

from app.models import Job
from app.repositories.base import BaseRepository

# Limite defensivo do aviso: se houver dezenas de vagas com o mesmo trio
# empresa/título/local, o cliente não precisa receber todas para decidir.
MAX_FINGERPRINT_MATCHES = 10


class JobRepository(BaseRepository):
    """Consultas e escritas de `jobs`."""

    def get_by_source_external_id(self, source: str, external_id: str) -> Job | None:
        """Camada 1: mesma origem e mesmo identificador externo = duplicata certa."""
        stmt = select(Job).where(
            Job.source == source,
            Job.external_id == external_id,
        )
        return self._db.scalar(stmt)

    def get_by_canonical_url(self, canonical_url: str) -> Job | None:
        """Camada 2: mesma URL canônica = duplicata quase certa.

        Devolve a vaga mais antiga quando houver mais de uma (cenário possível
        porque o banco não tem índice único em `canonical_url`).
        """
        stmt = (
            select(Job)
            .where(Job.canonical_url == canonical_url)
            .order_by(Job.created_at)
            .limit(1)
        )
        return self._db.scalar(stmt)

    def list_by_fingerprint(self, fingerprint: str) -> list[Job]:
        """Camada 3: mesmo fingerprint = duplicata provável (apenas sinaliza)."""
        stmt = (
            select(Job)
            .where(Job.fingerprint == fingerprint)
            .order_by(Job.created_at)
            .limit(MAX_FINGERPRINT_MATCHES)
        )
        return list(self._db.scalars(stmt))

    def add(self, job: Job) -> Job:
        """Adiciona a vaga à sessão."""
        self._db.add(job)
        return job
