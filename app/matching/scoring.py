"""Calcula e explica a média ponderada de uma vaga sem banco, rede ou LLM."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.matching.job_requirements import ExtractedRequirement, RequirementType
from app.matching.knockouts import KnockoutResult
from app.matching.skill_taxonomy import SkillTaxonomy
from app.services.normalization import clean_text, comparison_text


class RelatedSkill(BaseModel):
    """Relação direcional entre uma habilidade pedida e uma equivalente parcial."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    requirement: str = Field(min_length=1)
    candidate: str = Field(min_length=1)


class ScoringConfig(BaseModel):
    """Versão e parâmetros que determinam o peso da avaliação."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    scoring_version: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*-v[1-9][0-9]*$")
    required_weight: Decimal = Field(gt=0, max_digits=12, decimal_places=6)
    preferred_weight: Decimal = Field(gt=0, max_digits=12, decimal_places=6)
    related_skills: tuple[RelatedSkill, ...] = ()


class MatchLevel(StrEnum):
    """Níveis considerados na explicação da avaliação de cada requisito."""

    EXACT = "exata"
    ALIAS = "alias"
    RELATED = "relacionada"
    ABSENT = "ausente"
    UNCONFIRMED = "nao_confirmada"


_FACTORS = {
    MatchLevel.EXACT: Decimal(1),
    MatchLevel.ALIAS: Decimal("0.7"),
    MatchLevel.RELATED: Decimal("0.7"),
    MatchLevel.ABSENT: Decimal(0),
    MatchLevel.UNCONFIRMED: None,
}


@dataclass(frozen=True)
class RequirementAssessment:
    """Explica o nível, a evidência da vaga e a habilidade correspondente."""

    requirement: ExtractedRequirement
    level: MatchLevel
    weight: Decimal
    candidate_skill: str | None = None

    @property
    def factor(self) -> Decimal | None:
        """Devolve a contribuição do nível para a média, se confirmado."""
        return _FACTORS[self.level]


@dataclass(frozen=True)
class ScoreResult:
    """Resultado versionado, com numerador, denominador e evidências."""

    scoring_version: str
    knockouts: KnockoutResult
    score: Decimal | None = None
    weighted_sum: Decimal = Decimal(0)
    total_weight: Decimal = Decimal(0)
    assessments: tuple[RequirementAssessment, ...] = ()

    @property
    def met(self) -> tuple[RequirementAssessment, ...]:
        """Devolve as correspondências com contribuição positiva."""
        return tuple(item for item in self.assessments if item.factor)

    @property
    def absent(self) -> tuple[RequirementAssessment, ...]:
        """Devolve os requisitos com ausência explicitamente confirmada."""
        return tuple(
            item for item in self.assessments if item.level == MatchLevel.ABSENT
        )

    @property
    def unconfirmed(self) -> tuple[RequirementAssessment, ...]:
        """Devolve os requisitos que ficaram fora da média por falta de confirmação."""
        return tuple(
            item for item in self.assessments if item.level == MatchLevel.UNCONFIRMED
        )


class ScoreCalculator:
    """Avalia requisitos usando a mesma taxonomia da extração de vagas."""

    def __init__(self, config: ScoringConfig, taxonomy: SkillTaxonomy) -> None:
        self._config = config
        self._taxonomy = taxonomy
        self._related: dict[str, set[str]] = {}
        for pair in config.related_skills:
            required_skill = taxonomy.lookup(pair.requirement)
            candidate_skill = taxonomy.lookup(pair.candidate)
            if (
                not required_skill
                or not candidate_skill
                or required_skill == candidate_skill
            ):
                raise ValueError(
                    f"Relação inválida na taxonomia: {pair.requirement!r} / {pair.candidate!r}."
                )
            requirement_key = comparison_text(required_skill.canonical_name)
            candidate_key = comparison_text(candidate_skill.canonical_name)
            self._related.setdefault(requirement_key, set()).add(candidate_key)

    def _canonical_key(self, name: str) -> str:
        skill = self._taxonomy.lookup(name)
        return comparison_text(skill.canonical_name if skill else name)

    def score(
        self,
        requirements: Iterable[ExtractedRequirement],
        candidate_skills: Iterable[str],
        *,
        knockouts: KnockoutResult,
        confirmed_absent: Iterable[str] = (),
    ) -> ScoreResult:
        """Calcula a média na escala de 0 a 1 para uma vaga.

        Recebe os requisitos distintos do extrator, habilidades declaradas
        no perfil e ausências verificadas pelo chamador. Uma vaga eliminada
        ou uma média sem peso confirmado devolve score igual a None.
        """
        if not knockouts.eligible:
            return ScoreResult(self._config.scoring_version, knockouts)

        by_term: dict[str, str] = {}
        by_canonical: dict[str, str] = {}
        names = {clean_text(name) for name in candidate_skills}
        for name in sorted(
            names - {""}, key=lambda name: (comparison_text(name), name)
        ):
            by_term.setdefault(comparison_text(name), name)
            by_canonical.setdefault(self._canonical_key(name), name)
        absent_keys = {self._canonical_key(name) for name in confirmed_absent}

        assessments = [
            self._assess(requirement, by_term, by_canonical, absent_keys)
            for requirement in sorted(
                requirements,
                key=lambda item: (
                    comparison_text(item.skill.canonical_name),
                    item.skill.canonical_name,
                    item.requirement_type.value,
                    item.evidence_snippet,
                ),
            )
        ]
        # Um contexto próprio mantém o cálculo independente de arredondamento
        # e precisão configurados por outros pontos da aplicação.
        with localcontext(Context(prec=28, rounding=ROUND_HALF_EVEN)):
            weighted_sum = total_weight = Decimal(0)
            for item in assessments:
                factor = item.factor
                if factor is not None:
                    weighted_sum += item.weight * factor
                    total_weight += item.weight
            score = weighted_sum / total_weight if total_weight else None

        return ScoreResult(
            scoring_version=self._config.scoring_version,
            knockouts=knockouts,
            score=score,
            weighted_sum=weighted_sum,
            total_weight=total_weight,
            assessments=tuple(assessments),
        )

    def _assess(
        self,
        requirement: ExtractedRequirement,
        by_term: dict[str, str],
        by_canonical: dict[str, str],
        absent_keys: set[str],
    ) -> RequirementAssessment:
        weight = (
            self._config.required_weight
            if requirement.requirement_type == RequirementType.REQUIRED
            else self._config.preferred_weight
        )
        name = requirement.skill.canonical_name
        key = self._canonical_key(name)
        if exact := by_term.get(comparison_text(name)):
            return RequirementAssessment(requirement, MatchLevel.EXACT, weight, exact)
        if alias := by_canonical.get(key):
            return RequirementAssessment(requirement, MatchLevel.ALIAS, weight, alias)
        if key in absent_keys:
            return RequirementAssessment(requirement, MatchLevel.ABSENT, weight)
        related_keys = self._related.get(key, set()) & by_canonical.keys()
        if related_keys:
            related = by_canonical[min(related_keys)]
            return RequirementAssessment(
                requirement, MatchLevel.RELATED, weight, related
            )
        return RequirementAssessment(requirement, MatchLevel.UNCONFIRMED, weight)
