"""Verifica a fórmula, a explicação e a configuração do score determinístico."""

from collections.abc import Iterator
from decimal import Decimal, localcontext
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.matching.job_requirements import (
    ExtractedRequirement,
    RequirementExtractor,
    RequirementType,
)
from app.matching.knockouts import (
    KnockoutCode,
    KnockoutFlag,
    KnockoutResult,
    evaluate_knockouts,
)
from app.matching.scoring import MatchLevel, ScoreCalculator, ScoringConfig
from app.matching.skill_taxonomy import TaxonomySkill
from app.models import CandidatePreference, Job
from app.services.scoring import load_score_calculator, load_scoring_config
from app.services.skill_taxonomy import load_skill_taxonomy


def requirement(
    name: str, kind: RequirementType = RequirementType.REQUIRED
) -> ExtractedRequirement:
    """Monta um requisito com evidência sintética."""
    return ExtractedRequirement(
        TaxonomySkill(name, "dados"), kind, 0.85, f"Exige {name}."
    )


@pytest.fixture(scope="module")
def calculator() -> ScoreCalculator:
    """Carrega o cálculo com os pesos e as relações distribuídos."""
    return load_score_calculator()


def test_calcula_formula_e_preserva_explicacao(calculator: ScoreCalculator) -> None:
    requirements = [
        requirement("Python"),
        requirement("PostgreSQL"),
        requirement("Apache Spark", RequirementType.PREFERRED),
        requirement("Docker", RequirementType.PREFERRED),
        requirement("Kubernetes"),
    ]
    result = calculator.score(
        requirements,
        ["python", "Postgres", "PySpark"],
        confirmed_absent=["docker"],
        knockouts=KnockoutResult(),
    )

    assert result.scoring_version == "deterministico-v1"
    assert result.weighted_sum == Decimal("5.8")
    assert result.total_weight == Decimal(8)
    assert result.score == Decimal("0.725")
    assert {
        item.requirement.skill.canonical_name: (item.level, item.candidate_skill)
        for item in result.met
    } == {
        "Python": (MatchLevel.EXACT, "python"),
        "PostgreSQL": (MatchLevel.ALIAS, "Postgres"),
        "Apache Spark": (MatchLevel.RELATED, "PySpark"),
    }
    assert len(result.absent) == 1
    assert result.absent[0].requirement.evidence_snippet == "Exige Docker."
    assert result.absent[0].factor == Decimal(0)
    assert len(result.unconfirmed) == 1
    assert result.unconfirmed[0].requirement == requirements[-1]
    assert result.unconfirmed[0].factor is None


def test_ordem_e_contexto_decimal_nao_mudam_o_resultado(
    calculator: ScoreCalculator,
) -> None:
    requirements = [
        requirement("PostgreSQL"),
        requirement("Python", RequirementType.PREFERRED),
    ]
    skills = ["postgre sql", "Postgres", "Python"]
    baseline = calculator.score(requirements, skills, knockouts=KnockoutResult())
    with localcontext() as context:
        context.prec = 2
        result = calculator.score(
            reversed(requirements), reversed(skills), knockouts=KnockoutResult()
        )

    assert result == baseline
    assert result.score == Decimal("0.775")


def test_ausencia_explicita_prevalece_sobre_relacao(
    calculator: ScoreCalculator,
) -> None:
    result = calculator.score(
        [requirement("Apache Spark")],
        ["PySpark"],
        confirmed_absent=["spark"],
        knockouts=KnockoutResult(),
    )

    assert result.score == Decimal(0)
    assert result.absent[0].level is MatchLevel.ABSENT


def test_relacao_configurada_tem_direcao(calculator: ScoreCalculator) -> None:
    result = calculator.score(
        [requirement("PySpark")], ["Apache Spark"], knockouts=KnockoutResult()
    )

    assert result.score is None
    assert result.unconfirmed[0].level is MatchLevel.UNCONFIRMED


@pytest.mark.parametrize("requirements", [[], [requirement("Go")]])
def test_sem_requisitos_confirmados_fica_sem_media(
    calculator: ScoreCalculator, requirements: list[ExtractedRequirement]
) -> None:
    result = calculator.score(requirements, [], knockouts=KnockoutResult())

    assert result.score is None
    assert result.total_weight == 0
    assert len(result.unconfirmed) == len(requirements)


def test_eliminatoria_interrompe_antes_de_ler_requisitos(
    calculator: ScoreCalculator,
) -> None:
    def unreadable_requirements() -> Iterator[ExtractedRequirement]:
        pytest.fail("Vaga eliminada não pode entrar na avaliação de requisitos.")
        yield requirement("Python")

    flags = KnockoutResult((KnockoutFlag(KnockoutCode.EXCLUDED_COMPANY, "Empresa X"),))
    result = calculator.score(unreadable_requirements(), [], knockouts=flags)

    assert result.score is None
    assert result.knockouts == flags
    assert result.total_weight == 0
    assert result.assessments == ()


def test_combina_extrator_eliminatorias_e_score(calculator: ScoreCalculator) -> None:
    taxonomy = load_skill_taxonomy()
    requirements = RequirementExtractor(taxonomy).extract(
        "Requisitos: Python. Diferenciais: PostgreSQL."
    )
    job = Job(company="Empresa X")
    preferences = CandidatePreference(
        knockout_rules={"exclude_required_skills": ["Postgres"]}
    )
    knockouts = evaluate_knockouts(
        job,
        preferences,
        taxonomy=taxonomy,
        required_skill_names=[
            item.skill.canonical_name
            for item in requirements
            if item.requirement_type == RequirementType.REQUIRED
        ],
    )
    result = calculator.score(requirements, ["Python"], knockouts=knockouts)

    assert result.score == Decimal(1)
    assert result.total_weight == Decimal(3)
    assert result.met[0].requirement.evidence_snippet == "Python."
    assert result.unconfirmed[0].requirement.skill.canonical_name == "PostgreSQL"


def test_carrega_pesos_alternativos_e_emite_a_versao(tmp_path: Path) -> None:
    path = tmp_path / "weights.toml"
    path.write_text(
        'scoring_version = "teste-v2"\nrequired_weight = 1\npreferred_weight = 0.5\n',
        encoding="utf-8",
    )
    calculator = ScoreCalculator(load_scoring_config(path), load_skill_taxonomy())
    result = calculator.score(
        [requirement("Python"), requirement("Docker", RequirementType.PREFERRED)],
        ["Python"],
        confirmed_absent=["Docker"],
        knockouts=KnockoutResult(),
    )

    assert result.scoring_version == "teste-v2"
    assert result.total_weight == Decimal("1.5")
    assert result.score == Decimal(2) / 3


@pytest.mark.parametrize("weight", [0, -1, "NaN"])
def test_rejeita_pesos_invalidos(weight: object) -> None:
    with pytest.raises(ValidationError, match="required_weight"):
        ScoringConfig.model_validate(
            {
                "scoring_version": "teste-v1",
                "required_weight": weight,
                "preferred_weight": 1,
            }
        )


@pytest.mark.parametrize("other_skill", ["Inexistente", "spark"])
def test_rejeita_relacoes_invalidas(other_skill: str) -> None:
    config = ScoringConfig.model_validate(
        {
            "scoring_version": "teste-v1",
            "required_weight": 3,
            "preferred_weight": 1,
            "related_skills": [
                {"requirement": "Apache Spark", "candidate": other_skill}
            ],
        }
    )
    with pytest.raises(ValueError, match="Relação"):
        ScoreCalculator(config, load_skill_taxonomy())
