"""Revisão de duplicatas: camadas 3 e 4 com decisão humana.

POR QUÊ: o cadastro e a importação já resolvem as duplicatas certas (camadas 1
e 2) na escrita. O que sobra são **possíveis** duplicatas: mesmo fingerprint
(camada 3) ou títulos muito parecidos na mesma empresa (camada 4). Este serviço
agrupa esses casos para o usuário revisar e só grava a decisão — em
`duplicate_of_job_id` — quando ele confirma. Nada é apagado automaticamente e
nada é mesclado: a vaga marcada continua existindo, apenas aponta para a
original.

A varredura é limitada (`MAX_SCAN`) para não varrer o catálogo inteiro a cada
requisição; o resultado informa quando o limite foi atingido (`truncated`).
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol

from app.core.errors import ConflictError, InvalidDataError, NotFoundError
from app.models import Job
from app.schemas.dedup import DuplicateReviewLayer
from app.services.normalization import comparison_text
from app.services.similarity import SIMILARITY_THRESHOLD, title_similarity


class JobDedupRepositoryProtocol(Protocol):
    """Contrato mínimo do repositório de vagas para a revisão."""

    def get(self, job_id: uuid.UUID) -> Job | None: ...

    def list_dedup_scan(self, *, limit: int) -> list[Job]: ...

    def commit(self) -> None: ...


@dataclass(frozen=True)
class DuplicateGroup:
    """Grupo de vagas suspeitas, já ordenado da mais antiga para a mais nova."""

    layer: DuplicateReviewLayer
    similarity: float | None
    jobs: list[Job]

    @property
    def canonical_job_id(self) -> uuid.UUID:
        """Vaga mais antiga do grupo: referência sugerida para a confirmação."""
        return self.jobs[0].id


@dataclass(frozen=True)
class DuplicateScan:
    """Resultado da varredura com o alcance usado."""

    groups: list[DuplicateGroup]
    scanned_jobs: int
    truncated: bool


class JobDedupService:
    """Agrupa possíveis duplicatas e registra/desfaz a confirmação humana."""

    # Teto de vagas comparadas por chamada. A revisão é local e single-user; o
    # limite mantém a resposta previsível e o campo `truncated` avisa o cliente.
    MAX_SCAN = 5000

    def __init__(self, jobs: JobDedupRepositoryProtocol) -> None:
        self._jobs = jobs

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def list_groups(
        self,
        *,
        layer: DuplicateReviewLayer | None = None,
        limit: int = 50,
    ) -> DuplicateScan:
        """Agrupa duplicatas prováveis, opcionalmente filtrando por camada.

        `MAX_SCAN + 1` vagas são pedidas ao banco para saber se houve corte sem
        uma consulta extra de contagem.
        """
        fetched = self._jobs.list_dedup_scan(limit=self.MAX_SCAN + 1)
        truncated = len(fetched) > self.MAX_SCAN
        jobs = fetched[: self.MAX_SCAN]

        groups = self._group(jobs)
        if layer is not None:
            groups = [group for group in groups if group.layer == layer]
        # Mais recentes primeiro: a duplicata que acabou de entrar é a mais
        # provável de ainda não ter sido revisada.
        groups.sort(
            key=lambda group: (
                -max(job.created_at.timestamp() for job in group.jobs),
                str(group.canonical_job_id),
            )
        )
        return DuplicateScan(
            groups=groups[:limit],
            scanned_jobs=len(jobs),
            truncated=truncated,
        )

    # ------------------------------------------------------------------
    # Decisão humana
    # ------------------------------------------------------------------

    def confirm_duplicate(
        self, job_id: uuid.UUID, duplicate_of_job_id: uuid.UUID
    ) -> Job:
        """Marca `job_id` como duplicata de `duplicate_of_job_id`.

        Repetir a mesma confirmação é idempotente. Apontar para outra vaga sem
        antes desfazer é conflito (409): evita trocar a referência por engano e
        mantém o histórico previsível.
        """
        if job_id == duplicate_of_job_id:
            raise InvalidDataError(
                "Uma vaga não pode ser duplicata de si mesma.",
                details=[
                    {
                        "field": "duplicate_of_job_id",
                        "message": "Informe a vaga original, diferente desta.",
                    }
                ],
            )

        job = self._require_job(job_id)
        target = self._require_job(duplicate_of_job_id)

        if job.duplicate_of_job_id == target.id:
            return job

        if job.duplicate_of_job_id is not None:
            raise ConflictError(
                "Esta vaga já está marcada como duplicata de outra.",
                details=[
                    {
                        "field": "duplicate_of_job_id",
                        "job_id": str(job.duplicate_of_job_id),
                        "message": "Desfaça a marcação atual antes de apontar para outra vaga.",
                    }
                ],
            )

        if target.duplicate_of_job_id is not None:
            # Cadeias dificultariam a leitura ("duplicata de duplicata") e a
            # decisão na tela de revisão, que é sempre contra a vaga original.
            raise InvalidDataError(
                "A vaga de referência já é duplicata de outra; confirme na vaga original.",
                details=[
                    {
                        "field": "duplicate_of_job_id",
                        "job_id": str(target.duplicate_of_job_id),
                        "message": "Confirme a duplicata apontando para a vaga principal.",
                    }
                ],
            )

        job.duplicate_of_job_id = target.id
        self._jobs.commit()
        return job

    def undo_duplicate(self, job_id: uuid.UUID) -> None:
        """Remove a marcação de duplicata, devolvendo a vaga à revisão."""
        job = self._require_job(job_id)
        if job.duplicate_of_job_id is None:
            raise InvalidDataError(
                "Esta vaga não está marcada como duplicata.",
                details=[
                    {
                        "field": "duplicate_of_job_id",
                        "message": "Só é possível desfazer uma marcação existente.",
                    }
                ],
            )
        job.duplicate_of_job_id = None
        self._jobs.commit()

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _require_job(self, job_id: uuid.UUID) -> Job:
        """Busca a vaga ou levanta 404 com o identificador no detalhe."""
        job = self._jobs.get(job_id)
        if job is None:
            raise NotFoundError(
                "Vaga não encontrada.",
                details=[
                    {
                        "field": "job_id",
                        "job_id": str(job_id),
                        "message": "Nenhuma vaga com este identificador.",
                    }
                ],
            )
        return job

    def _group(self, jobs: list[Job]) -> list[DuplicateGroup]:
        """Monta os grupos das camadas 3 e 4, sem repetir uma vaga em dois grupos."""
        ordered = sorted(jobs, key=lambda job: (job.created_at, str(job.id)))
        groups: list[DuplicateGroup] = []
        assigned: set[uuid.UUID] = set()

        by_fingerprint: dict[str, list[Job]] = defaultdict(list)
        for job in ordered:
            by_fingerprint[job.fingerprint].append(job)
        for bucket in by_fingerprint.values():
            if len(bucket) < 2:
                continue
            groups.append(
                DuplicateGroup(
                    layer=DuplicateReviewLayer.FINGERPRINT,
                    similarity=None,
                    jobs=bucket,
                )
            )
            assigned.update(job.id for job in bucket)

        # Camada 4: só faz sentido comparar títulos da mesma empresa — vagas de
        # empresas diferentes com título parecido são cargos distintos.
        by_company: dict[str, list[Job]] = defaultdict(list)
        for job in ordered:
            if job.id in assigned:
                continue
            by_company[comparison_text(job.company)].append(job)

        for bucket in by_company.values():
            if len(bucket) < 2:
                continue
            for index, job in enumerate(bucket):
                if job.id in assigned:
                    continue
                match, score = self._best_similar(job, bucket[:index], assigned)
                if match is None:
                    continue
                groups.append(
                    DuplicateGroup(
                        layer=DuplicateReviewLayer.SIMILARITY,
                        similarity=round(score, 1),
                        jobs=[match, job],
                    )
                )
                assigned.update({match.id, job.id})

        return groups

    def _best_similar(
        self,
        job: Job,
        candidates: list[Job],
        assigned: set[uuid.UUID],
    ) -> tuple[Job | None, float]:
        """Melhor candidato anterior (mais antigo) acima do limiar da camada 4."""
        best: Job | None = None
        best_score = 0.0
        for other in candidates:
            if other.id in assigned:
                continue
            # Mesma URL seria camada 2 (bloqueada na escrita); se existir em
            # dados antigos, não é uma "possível" duplicata — é certa.
            if other.canonical_url == job.canonical_url:
                continue
            score = title_similarity(job.title, other.title)
            if score >= SIMILARITY_THRESHOLD and score > best_score:
                best, best_score = other, score
        return best, best_score
