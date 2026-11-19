"""Serviço de vagas: cadastro manual com deduplicação em camadas.

POR QUÊ: o cadastro não pode gravar uma vaga duplicada em silêncio nem recusar
tudo com um erro genérico. As camadas 1 e 2 (`source`+`external_id` e
`canonical_url`) identificam a mesma vaga e viram conflito 409 com os dados da
vaga existente; a camada 3 (`fingerprint`) pode ser coincidência e vira apenas
aviso, deixando a decisão para a revisão humana da F1-T07.

O serviço não conhece HTTP: levanta `ConflictError` e o handler padroniza.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError
from app.models import Job
from app.repositories.jobs import MAX_FINGERPRINT_MATCHES
from app.schemas.jobs import DuplicateLayer, JobCreate
from app.services.normalization import (
    canonicalize_url,
    clean_text,
    job_fingerprint,
    normalize_seniority,
    normalize_work_mode,
)


class JobRepositoryProtocol(Protocol):
    """Contrato mínimo do repositório de vagas usado pelo serviço."""

    def get_by_source_external_id(
        self, source: str, external_id: str
    ) -> Job | None: ...

    def get_by_canonical_url(self, canonical_url: str) -> Job | None: ...

    def list_by_fingerprint(self, fingerprint: str) -> list[Job]: ...

    def add(self, job: Job) -> Job: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class JobService:
    """Casos de uso de vagas; por enquanto, o cadastro manual."""

    def __init__(self, jobs: JobRepositoryProtocol) -> None:
        self._jobs = jobs

    def create_manual(self, data: JobCreate) -> tuple[Job, list[Job]]:
        """Grava a vaga normalizada e devolve as duplicatas prováveis.

        Levanta `ConflictError` (409) quando a vaga já existe pelas camadas
        certas (identificador externo ou URL canônica).
        """
        canonical_url = canonicalize_url(data.url)
        # Limpa antes de calcular o fingerprint: o hash usa a forma comparável,
        # mas título/empresa exibidos também não devem ter espaços duplicados.
        title = clean_text(data.title)
        company = clean_text(data.company)
        location = clean_text(data.location) or None
        fingerprint = job_fingerprint(company, title, location)

        self._ensure_not_exact_duplicate(data, canonical_url)

        # Camada 3: só sinaliza. A vaga é criada mesmo assim porque duas vagas
        # reais podem compartilhar empresa, título e localidade.
        probable = self._jobs.list_by_fingerprint(fingerprint)

        job = Job(
            title=title,
            company=company,
            description=data.description,
            location=location,
            work_mode=normalize_work_mode(data.work_mode).value,
            seniority=normalize_seniority(data.seniority).value,
            employment_type=data.employment_type,
            salary_min=data.salary_min,
            salary_max=data.salary_max,
            currency=data.currency,
            source=data.source,
            external_id=data.external_id,
            # `url` preserva o que o usuário enviou; `canonical_url` é a forma
            # comparável usada na dedup e nas buscas.
            url=data.url,
            canonical_url=canonical_url,
            fingerprint=fingerprint,
            posted_at=data.posted_at,
        )
        self._jobs.add(job)
        try:
            self._jobs.commit()
        except IntegrityError as exc:
            # Corrida entre a checagem e o INSERT: o índice único parcial
            # `(source, external_id)` é a última linha de defesa.
            self._jobs.rollback()
            raise ConflictError(
                "Já existe uma vaga com este identificador externo.",
                details=[
                    {
                        "field": "external_id",
                        "layer": DuplicateLayer.EXTERNAL_ID.value,
                        "message": "Identificador externo já cadastrado.",
                    }
                ],
            ) from exc

        return job, probable[:MAX_FINGERPRINT_MATCHES]

    def _ensure_not_exact_duplicate(self, data: JobCreate, canonical_url: str) -> None:
        """Levanta 409 nas camadas 1 e 2, com os dados da vaga existente.

        `details` segue o formato de lista do handler de erros e inclui a
        camada, para que o cliente explique ao usuário por que a vaga não foi
        criada e qual registro já existe.
        """
        if data.external_id is not None:
            same_external_id = self._jobs.get_by_source_external_id(
                data.source, data.external_id
            )
            if same_external_id is not None:
                raise self._duplicate_conflict(
                    same_external_id,
                    DuplicateLayer.EXTERNAL_ID,
                    "Já existe uma vaga com a mesma origem e identificador externo.",
                )

        same_url = self._jobs.get_by_canonical_url(canonical_url)
        if same_url is not None:
            raise self._duplicate_conflict(
                same_url,
                DuplicateLayer.CANONICAL_URL,
                "Já existe uma vaga com a mesma URL canônica.",
            )

    def _duplicate_conflict(
        self, job: Job, layer: DuplicateLayer, message: str
    ) -> ConflictError:
        """Monta o 409 com a vaga existente e a camada que detectou a duplicata."""
        return ConflictError(
            message,
            details=[
                {
                    "job_id": str(job.id),
                    "layer": layer.value,
                    "title": job.title,
                    "company": job.company,
                    "source": job.source,
                    "canonical_url": job.canonical_url,
                }
            ],
        )
