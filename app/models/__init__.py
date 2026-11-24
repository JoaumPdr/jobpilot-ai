"""Modelos SQLAlchemy do JobPilot AI.

POR QUÊ: importar todos os modelos aqui garante que o `metadata` da `Base`
conheça todas as tabelas e relacionamentos. O Alembic (via `migrations/env.py`)
e os testes dependem desse registro completo; esquecer um import faz o
autogenerate "não ver" a tabela e quebra o mapeamento das relações.
"""

from app.models.application import (
    Application,
    ApplicationStatus,
    ApplicationStatusHistory,
)
from app.models.base import Base
from app.models.candidate import Candidate
from app.models.experience import CandidateExperience
from app.models.import_batch import ImportBatch, ImportKind
from app.models.job import Job, Seniority, WorkMode
from app.models.job_match import JobMatch
from app.models.job_skill import JobSkill
from app.models.preferences import CandidatePreference
from app.models.skill import CandidateSkill, Skill

__all__ = [
    "Application",
    "ApplicationStatus",
    "ApplicationStatusHistory",
    "Base",
    "Candidate",
    "CandidateExperience",
    "CandidatePreference",
    "CandidateSkill",
    "ImportBatch",
    "ImportKind",
    "Job",
    "JobMatch",
    "JobSkill",
    "Seniority",
    "Skill",
    "WorkMode",
]
