"""Dependências FastAPI compartilhadas pelas rotas do perfil.

POR QUÊ: concentrar a montagem dos serviços evita duplicação entre os routers
de candidato, habilidades e experiências, e mantém as rotas finas.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.profile import (
    CandidateRepository,
    CandidateSkillRepository,
    ExperienceRepository,
    PreferenceRepository,
    SkillRepository,
)
from app.services.experiences import ExperienceService
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


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
SkillServiceDep = Annotated[SkillService, Depends(get_skill_service)]
ExperienceServiceDep = Annotated[ExperienceService, Depends(get_experience_service)]
