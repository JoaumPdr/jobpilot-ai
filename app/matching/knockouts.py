"""Avalia restrições de candidatura antes do score, sem consultar banco ou rede."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from app.matching.skill_taxonomy import SkillTaxonomy
from app.models import CandidatePreference, Job, WorkMode
from app.services.normalization import clean_text, comparison_text, normalize_work_mode


class KnockoutRule(StrEnum):
    """Chaves operacionais do objeto de regras nas preferências."""

    EXCLUDE_COMPANIES = "exclude_companies"
    EXCLUDE_REQUIRED_SKILLS = "exclude_required_skills"


class KnockoutCode(StrEnum):
    """Códigos estáveis para explicar por que a vaga ficou fora da média."""

    EXCLUDED_COMPANY = "empresa_excluida"
    EXCLUDED_REQUIRED_SKILL = "habilidade_obrigatoria_excluida"
    WORK_MODE_MISMATCH = "modalidade_incompativel"
    LOCATION_MISMATCH = "localizacao_incompativel"


@dataclass(frozen=True)
class KnockoutFlag:
    """Motivo da exclusão e valor na vaga que ativou a regra."""

    code: KnockoutCode
    actual: str


@dataclass(frozen=True)
class KnockoutResult:
    """Resultado que o chamador verifica antes de iniciar o cálculo do score."""

    flags: tuple[KnockoutFlag, ...] = ()

    @property
    def eligible(self) -> bool:
        """Indica se a vaga pode entrar no cálculo da média."""
        return not self.flags


def parse_knockout_terms(value: object) -> tuple[str, ...] | None:
    """Lê uma lista JSON de termos não vazios ou sinaliza formato inválido."""
    if not isinstance(value, list):
        return None
    terms = tuple(clean_text(item) for item in value if isinstance(item, str))
    if len(terms) != len(value) or not all(terms):
        return None
    return terms


_LOCATION_DELIMITER = re.compile(r"[,/]| [–—-] ")
_UNKNOWN_LOCATION = {"", "desconhecido", "nao informado", "unknown", "not specified"}


def _location_parts(value: str | None) -> tuple[str, ...]:
    name = comparison_text(value)
    if name in _UNKNOWN_LOCATION or normalize_work_mode(name) != WorkMode.DESCONHECIDO:
        return ()
    return tuple(
        part for item in _LOCATION_DELIMITER.split(name) if (part := item.strip())
    )


def _locations_match(actual: tuple[str, ...], expected: tuple[str, ...]) -> bool:
    # As duas formas podem omitir cidade/UF/país a partir do ponto em que
    # acabam. Se ambas informarem UF, valores diferentes continuam distintos.
    shared = min(len(actual), len(expected))
    return actual[:shared] == expected[:shared]


def _canonical_skill(name: str, taxonomy: SkillTaxonomy) -> str:
    skill = taxonomy.lookup(name)
    return skill.canonical_name if skill else clean_text(name)


def evaluate_knockouts(
    job: Job,
    preferences: CandidatePreference | None,
    *,
    taxonomy: SkillTaxonomy,
    required_skill_names: Iterable[str] = (),
) -> KnockoutResult:
    """Aplica regras configuradas aos dados conhecidos e devolve todas as flags.

    O chamador fornece apenas os nomes de habilidades obrigatórias da vaga.
    Por exemplo, excluir "postgres" gera a flag de PostgreSQL quando a vaga
    exige essa habilidade. Listas legadas em formato inválido ficam inativas.
    """
    if preferences is None:
        return KnockoutResult()

    rules = preferences.knockout_rules or {}
    flags: list[KnockoutFlag] = []
    excluded_companies = parse_knockout_terms(rules.get(KnockoutRule.EXCLUDE_COMPANIES))
    if excluded_companies and comparison_text(job.company) in {
        comparison_text(company) for company in excluded_companies
    }:
        flags.append(KnockoutFlag(KnockoutCode.EXCLUDED_COMPANY, job.company))

    excluded_skills = parse_knockout_terms(
        rules.get(KnockoutRule.EXCLUDE_REQUIRED_SKILLS)
    )
    if excluded_skills:
        excluded_keys = {
            comparison_text(_canonical_skill(name, taxonomy))
            for name in excluded_skills
        }
        # A ordem é estável mesmo quando o banco devolve os requisitos em
        # outra ordem. Colapsar aliases evita flags repetidas da mesma skill.
        required = {_canonical_skill(name, taxonomy) for name in required_skill_names}
        seen: set[str] = set()
        for name in sorted(required, key=lambda name: (comparison_text(name), name)):
            skill_key = comparison_text(name)
            if skill_key in excluded_keys and skill_key not in seen:
                flags.append(KnockoutFlag(KnockoutCode.EXCLUDED_REQUIRED_SKILL, name))
                seen.add(skill_key)

    allowed_modes = {normalize_work_mode(mode) for mode in preferences.work_modes or ()}
    allowed_modes.discard(WorkMode.DESCONHECIDO)
    job_mode = normalize_work_mode(job.work_mode)
    if (
        allowed_modes
        and job_mode != WorkMode.DESCONHECIDO
        and job_mode not in allowed_modes
    ):
        flags.append(KnockoutFlag(KnockoutCode.WORK_MODE_MISMATCH, job_mode.value))

    allowed_locations = [
        parts
        for value in preferences.locations or ()
        if (parts := _location_parts(value))
    ]
    actual_location = _location_parts(job.location)
    if (
        actual_location
        and allowed_locations
        and not any(
            _locations_match(actual_location, expected)
            for expected in allowed_locations
        )
    ):
        flags.append(KnockoutFlag(KnockoutCode.LOCATION_MISMATCH, job.location or ""))

    return KnockoutResult(tuple(flags))
