"""Dependências FastAPI compartilhadas pelas rotas do perfil.

POR QUÊ: concentrar a montagem dos serviços evita duplicação entre os routers
de candidato, habilidades e experiências, e mantém as rotas finas.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.imports import ImportBatchRepository
from app.repositories.jobs import JobRepository
from app.repositories.profile import (
    CandidateRepository,
    CandidateSkillRepository,
    ExperienceRepository,
    PreferenceRepository,
    SkillRepository,
)
from app.services.experiences import ExperienceService
from app.services.job_dedup import JobDedupService
from app.services.job_import import JobImportService
from app.services.jobs import JobService
from app.services.profile import ProfileService
from app.services.skills import SkillService

DbSession = Annotated[Session, Depends(get_db)]


def get_profile_service(db: DbSession) -> ProfileService:
    """Monta o serviço de candidato/preferências com a sessão da requisição."""
    return ProfileService(CandidateRepository(db), PreferenceRepository(db))


def get_skill_service(db: DbSession) -> SkillService:
    """Monta o serviço de habilidades com a sessão da requisição."""
    return SkillService(
        CandidateRepository(db),
        SkillRepository(db),
        CandidateSkillRepository(db),
    )


def get_experience_service(db: DbSession) -> ExperienceService:
    """Monta o serviço de experiências com a sessão da requisição."""
    return ExperienceService(CandidateRepository(db), ExperienceRepository(db))


def get_job_service(db: DbSession) -> JobService:
    """Monta o serviço de vagas com a sessão da requisição."""
    return JobService(JobRepository(db))


def get_job_import_service(db: DbSession) -> JobImportService:
    """Monta o importador CSV compartilhando a mesma sessão para tudo."""
    jobs_repository = JobRepository(db)
    return JobImportService(
        JobService(jobs_repository), jobs_repository, ImportBatchRepository(db)
    )


def get_job_dedup_service(db: DbSession) -> JobDedupService:
    """Monta o serviço de revisão de duplicatas com a sessão da requisição."""
    return JobDedupService(JobRepository(db))


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
SkillServiceDep = Annotated[SkillService, Depends(get_skill_service)]
ExperienceServiceDep = Annotated[ExperienceService, Depends(get_experience_service)]
JobServiceDep = Annotated[JobService, Depends(get_job_service)]
JobImportServiceDep = Annotated[JobImportService, Depends(get_job_import_service)]
JobDedupServiceDep = Annotated[JobDedupService, Depends(get_job_dedup_service)]
