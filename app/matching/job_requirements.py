"""Extrai requisitos de texto livre em PT/EN sem consultar banco ou rede."""

import re
from dataclasses import dataclass
from enum import StrEnum

from app.matching.skill_taxonomy import SkillTaxonomy, TaxonomySkill
from app.services.normalization import comparison_text


class RequirementType(StrEnum):
    """Classificação armazenada em job_skills."""

    REQUIRED = "obrigatorio"
    PREFERRED = "desejavel"


@dataclass(frozen=True)
class ExtractedRequirement:
    """Habilidade com classificação, confiança e evidência no texto original."""

    skill: TaxonomySkill
    requirement_type: RequirementType
    confidence: float
    evidence_snippet: str


_HEADINGS = {
    RequirementType.REQUIRED: {
        "requisitos",
        "requisitos obrigatorios",
        "requisitos minimos",
        "obrigatorios",
        "requisitos tecnicos",
        "qualificacoes",
        "qualificacoes obrigatorias",
        "qualificacoes minimas",
        "requirements",
        "required",
        "minimum requirements",
        "required qualifications",
        "minimum qualifications",
        "must have",
        "must-have",
        "technical requirements",
    },
    RequirementType.PREFERRED: {
        "diferencial",
        "diferenciais",
        "desejaveis",
        "requisitos desejaveis",
        "qualificacoes desejaveis",
        "nice to have",
        "nice-to-have",
        "desirable",
        "preferred",
        "preferred qualifications",
        "preferred skills",
        "bonus points",
    },
}
_SECTION_TYPE = {
    heading: kind for kind, headings in _HEADINGS.items() for heading in headings
}
_OTHER_SECTIONS = {
    "responsabilidades",
    "principais responsabilidades",
    "atividades",
    "beneficios",
    "sobre a empresa",
    "sobre a vaga",
    "o que oferecemos",
    "responsibilities",
    "key responsibilities",
    "duties",
    "benefits",
    "about us",
    "about the role",
    "what we offer",
    "how to apply",
    "como se candidatar",
}
_PREFERRED = re.compile(
    r"\b(?:desejave(?:l|is)|diferencia(?:l|is)|opciona(?:l|is)|"
    r"prefer(?:red|ably)|nice[- ]to[- ]have|a plus|bonus(?: points)?|"
    r"optional|desirable)\b"
)
_NEGATED = re.compile(
    r"\b(?:nao (?:e )?(?:obrigatori[oa]s?|necessari[oa]s?|exigid[oa]s?)|"
    r"not (?:strictly )?(?:required|mandatory|essential))\b"
)
_REQUIRED = re.compile(
    r"\b(?:obrigatori[oa]s?|necessari[oa]s?|exigid[oa]s?|requerid[oa]s?|"
    r"e preciso|deve (?:ter|saber|conhecer)|required|mandatory|essential|"
    r"must(?:[- ]have|[- ]know)?|need to (?:have|know))\b"
)
_BULLET = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+")
_MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+")
_SENTENCES = re.compile(r";|(?<=[.!?])\s+")
_SHORT_SKILLS = {
    "c": re.compile(r"(?<![\w+#])C(?![\w+#$])"),
    "r": re.compile(r"(?<![\w+#])R(?![\w+#$])"),
    "go": re.compile(r"(?<![\w+#])Go(?![\w+#]|\s+to\b)"),
}


def _explicit_type(text: str) -> RequirementType | None:
    if _PREFERRED.search(text):
        return RequirementType.PREFERRED
    if _REQUIRED.search(text):
        return RequirementType.REQUIRED
    return None


def _has_cue(fragment: str) -> bool:
    text = comparison_text(fragment)
    return bool(_explicit_type(text) or _NEGATED.search(text))


def _clauses(line: str) -> list[str]:
    clauses: list[str] = []
    for sentence in _SENTENCES.split(line):
        # Uma vírgula em uma lista ("Python, SQL required") mantém o gatilho
        # para os dois termos. Duas classificações explícitas abrem cláusulas.
        start = 0
        previous_comma = 0
        has_left_cue = False
        commas = list(re.finditer(",", sentence))
        for index, comma in enumerate(commas):
            stop = (
                commas[index + 1].start() if index + 1 < len(commas) else len(sentence)
            )
            has_left_cue = has_left_cue or _has_cue(
                sentence[previous_comma : comma.start()]
            )
            if has_left_cue and _has_cue(sentence[comma.end() : stop]):
                clauses.append(sentence[start : comma.start()].strip())
                start = comma.end()
                has_left_cue = False
            previous_comma = comma.end()
        if clause := sentence[start:].strip():
            clauses.append(clause)
    return clauses


def _classified_fragments(
    description: str,
) -> list[tuple[str, RequirementType, float]]:
    fragments: list[tuple[str, RequirementType, float]] = []
    section: RequirementType | None = None
    for line in description.splitlines():
        heading_markup = _MARKDOWN_HEADING.match(line.lstrip())
        line = _MARKDOWN_HEADING.sub("", line.lstrip())
        line = _BULLET.sub("", line).strip()
        for fragment in _clauses(line):
            label, colon, content = fragment.partition(":")
            heading = comparison_text(label.strip("*_ "))
            if heading in _SECTION_TYPE:
                section = _SECTION_TYPE[heading]
                fragment = content.strip("*_ ") if colon else ""
            elif heading in _OTHER_SECTIONS or heading_markup:
                section = None
                fragment = content.strip("*_ ") if colon else ""
            elif colon and not content.strip("*_ "):
                section = None
                fragment = ""
            heading_markup = None

            if fragment:
                normalized = comparison_text(fragment)
                explicit = _explicit_type(normalized)
                # Uma negativa isolada ("SQL não é obrigatório") não é
                # evidência de que a empresa considera SQL um diferencial.
                if (
                    _NEGATED.search(normalized)
                    and explicit != RequirementType.PREFERRED
                ):
                    continue
                if kind := explicit or section:
                    fragments.append((fragment, kind, 0.95 if explicit else 0.85))
    return fragments


class RequirementExtractor:
    """Compila os aliases uma vez e extrai evidências de várias descrições."""

    def __init__(self, taxonomy: SkillTaxonomy) -> None:
        self._skills = {
            comparison_text(term): skill
            for skill in taxonomy.skills
            for term in (skill.canonical_name, *skill.aliases)
        }
        # O alias mais longo começa no mesmo ponto do menor. Isso evita
        # extrair Spark de "Spark SQL" e C de "C++".
        names = sorted(self._skills, key=lambda name: (-len(name), name))
        alternatives = "|".join(re.escape(name) for name in names)
        self._pattern = (
            re.compile(rf"(?<![\w+#])(?:{alternatives})(?![\w+#])") if names else None
        )

    def extract(self, description: str | None) -> tuple[ExtractedRequirement, ...]:
        """Resolve habilidades e conserva a evidência mais forte por habilidade.

        Um requisito obrigatório prevalece sobre um diferencial repetido. Em
        tipos iguais, um gatilho explícito prevalece sobre o título da seção.
        """
        if not description or self._pattern is None:
            return ()

        matches: dict[str, ExtractedRequirement] = {}
        for snippet, kind, confidence in _classified_fragments(description):
            for match in self._pattern.finditer(comparison_text(snippet)):
                alias = match.group()
                if alias in _SHORT_SKILLS and not _SHORT_SKILLS[alias].search(snippet):
                    continue
                skill = self._skills[alias]
                previous = matches.get(skill.canonical_name)
                priority = kind is RequirementType.REQUIRED, confidence
                if previous is None or priority > (
                    previous.requirement_type is RequirementType.REQUIRED,
                    previous.confidence,
                ):
                    matches[skill.canonical_name] = ExtractedRequirement(
                        skill, kind, confidence, snippet
                    )
        return tuple(matches.values())
