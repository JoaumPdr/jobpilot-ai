"""Repositório de vagas: listagem, consultas de deduplicação e escrita.

POR QUÊ: as três primeiras camadas da dedup (`PLANO.md` §6.3) são consultas
simples, mas o serviço não deve montar `select` — assim ele fica testável com um
dublê em memória e a otimização (índice, limite, ordenação) mora em um só lugar.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import or_, select, tuple_

from app.models import Job
from app.repositories.base import BaseRepository
from app.schemas.jobs import JobListQuery

# Limite defensivo do aviso: se houver dezenas de vagas com o mesmo trio
# empresa/título/local, o cliente não precisa receber todas para decidir.
MAX_FINGERPRINT_MATCHES = 10


class JobRepository(BaseRepository):
    """Consultas e escritas de `jobs`."""

    def list_page(self, query: JobListQuery) -> list[Job]:
        """Busca até um item adicional na mesma consulta que lê a página."""
        stmt = select(Job)
        if query.q is not None:
            # Escapar % e _ permite buscar esses caracteres como texto.
            stmt = stmt.where(
                or_(
                    Job.title.icontains(query.q, autoescape=True),
                    Job.company.icontains(query.q, autoescape=True),
                    Job.description.icontains(query.q, autoescape=True),
                )
            )
        if query.work_mode is not None:
            stmt = stmt.where(Job.work_mode == query.work_mode.value)
        if query.location is not None:
            stmt = stmt.where(Job.location.icontains(query.location, autoescape=True))
        if query.seniority is not None:
            stmt = stmt.where(Job.seniority == query.seniority.value)
        if query.source is not None:
            stmt = stmt.where(Job.source == query.source)
        if query.posted_from is not None:
            stmt = stmt.where(Job.posted_at >= query.posted_from)
        if query.posted_to is not None:
            stmt = stmt.where(Job.posted_at <= query.posted_to)
        if not query.include_archived:
            stmt = stmt.where(Job.is_archived.is_(False))
        if not query.include_duplicates:
            stmt = stmt.where(Job.duplicate_of_job_id.is_(None))

        # O UUID desempata vagas do mesmo lote, que podem ter a mesma data.
        stmt = stmt.order_by(Job.created_at.desc(), Job.id.desc())
        return list(self._db.scalars(stmt.offset(query.offset).limit(query.limit + 1)))

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

    def get(self, job_id: uuid.UUID) -> Job | None:
        """Busca pelo identificador, sem carregar relações."""
        return self._db.get(Job, job_id)

    def list_dedup_scan(self, *, limit: int) -> list[Job]:
        """Vagas que ainda podem ser revisadas, da mais antiga para a mais nova.

        Arquivadas e já confirmadas como duplicata ficam de fora: a revisão só
        interessa ao que ainda não teve decisão.
        """
        stmt = (
            select(Job)
            .where(Job.is_archived.is_(False), Job.duplicate_of_job_id.is_(None))
            .order_by(Job.created_at, Job.id)
            .limit(limit)
        )
        return list(self._db.scalars(stmt))

    def find_existing_canonical_urls(self, urls: Sequence[str]) -> set[str]:
        """Camada 2 em bloco: quais URLs canônicas já existem no catálogo.

        POR QUÊ: a importação CSV pré-carrega as chaves de um bloco de linhas
        em **uma** consulta, em vez de uma por linha (RNF-09).
        """
        if not urls:
            return set()
        stmt = select(Job.canonical_url).where(Job.canonical_url.in_(urls))
        return {url for url in self._db.scalars(stmt) if url is not None}

    def find_existing_external_ids(
        self, keys: Sequence[tuple[str, str]]
    ) -> set[tuple[str, str]]:
        """Camada 1 em bloco: pares `(source, external_id)` já existentes."""
        if not keys:
            return set()
        stmt = select(Job.source, Job.external_id).where(
            tuple_(Job.source, Job.external_id).in_(keys)
        )
        return {(source, external_id) for source, external_id in self._db.execute(stmt)}

    def add(self, job: Job) -> Job:
        """Adiciona a vaga à sessão."""
        self._db.add(job)
        return job
