"""Schemas Pydantic da aplicação."""

from app.schemas.experiences import (
    ExperienceCreate,
    ExperienceRead,
    ExperienceUpdate,
)
from app.schemas.profile import (
    CandidateCreate,
    CandidateRead,
    CandidateUpdate,
    EducationEntry,
    LanguageEntry,
    LanguageLevel,
    PreferencesPut,
    PreferencesRead,
)
from app.schemas.skills import (
    CandidateSkillCreate,
    CandidateSkillRead,
    CandidateSkillUpdate,
    SkillCreate,
    SkillLevel,
    SkillRead,
)

__all__ = [
    "CandidateCreate",
    "CandidateRead",
    "CandidateSkillCreate",
    "CandidateSkillRead",
    "CandidateSkillUpdate",
    "CandidateUpdate",
    "EducationEntry",
    "ExperienceCreate",
    "ExperienceRead",
    "ExperienceUpdate",
    "LanguageEntry",
    "LanguageLevel",
    "PreferencesPut",
    "PreferencesRead",
    "SkillCreate",
    "SkillLevel",
    "SkillRead",
]
