"""Cobre cada filtro eliminatório sem banco, rede ou cálculo de score."""

import pytest

from app.matching.knockouts import KnockoutCode, evaluate_knockouts
from app.matching.skill_taxonomy import SkillTaxonomy
from app.models import CandidatePreference, Job
from app.services.skill_taxonomy import load_skill_taxonomy


@pytest.fixture(scope="module")
def taxonomy() -> SkillTaxonomy:
    """Usa os aliases da taxonomia distribuída."""
    return load_skill_taxonomy()


def test_empresa_excluida_por_nome_normalizado(taxonomy: SkillTaxonomy) -> None:
    preferences = CandidatePreference(
        knockout_rules={"exclude_companies": ["  EMPRESA   ACACIA  "]}
    )
    result = evaluate_knockouts(
        Job(company="Empresa Acácia"), preferences, taxonomy=taxonomy
    )

    assert not result.eligible
    assert [(flag.code, flag.actual) for flag in result.flags] == [
        (KnockoutCode.EXCLUDED_COMPANY, "Empresa Acácia")
    ]
    similar = evaluate_knockouts(
        Job(company="Empresa Acácia Brasil"), preferences, taxonomy=taxonomy
    )
    assert similar.eligible


def test_habilidades_excluidas_resolvem_aliases_e_deduplicam(
    taxonomy: SkillTaxonomy,
) -> None:
    preferences = CandidatePreference(
        knockout_rules={"exclude_required_skills": ["postgres", "POSTGRESQL", "SQL"]}
    )
    result = evaluate_knockouts(
        Job(company="Empresa A"),
        preferences,
        taxonomy=taxonomy,
        required_skill_names=["SQL", "postgresql", "Postgres"],
    )

    assert [(flag.code, flag.actual) for flag in result.flags] == [
        (KnockoutCode.EXCLUDED_REQUIRED_SKILL, "PostgreSQL"),
        (KnockoutCode.EXCLUDED_REQUIRED_SKILL, "SQL"),
    ]


@pytest.mark.parametrize(
    ("mode", "eligible"),
    [("híbrido", True), ("remoto", False), ("desconhecido", True), (None, True)],
)
def test_modalidade_conhecida_precisa_ser_permitida(
    taxonomy: SkillTaxonomy, mode: str | None, eligible: bool
) -> None:
    preferences = CandidatePreference(work_modes=[" HYBRID ", "presencial"])
    result = evaluate_knockouts(
        Job(company="Empresa A", work_mode=mode), preferences, taxonomy=taxonomy
    )
    assert result.eligible is eligible
    if not eligible:
        assert result.flags[0].code is KnockoutCode.WORK_MODE_MISMATCH


@pytest.mark.parametrize(
    ("actual", "preferred", "eligible"),
    [
        ("São Paulo - SP", "SAO PAULO", True),
        ("São Paulo/SP", "São Paulo, SP", True),
        ("São Paulo, RJ", "São Paulo, SP", False),
        ("Rio de Janeiro", "São Paulo", False),
        (None, "São Paulo", True),
        ("Remoto", "São Paulo", True),
        ("Não informado", "São Paulo", True),
    ],
)
def test_localizacao_compara_componentes_publicados(
    taxonomy: SkillTaxonomy, actual: str | None, preferred: str, eligible: bool
) -> None:
    preferences = CandidatePreference(locations=[preferred])
    result = evaluate_knockouts(
        Job(company="Empresa A", location=actual), preferences, taxonomy=taxonomy
    )
    assert result.eligible is eligible
    if not eligible:
        assert result.flags[0].code is KnockoutCode.LOCATION_MISMATCH


def test_preserva_dados_legados_sem_aplicar_regras_invalidas(
    taxonomy: SkillTaxonomy,
) -> None:
    preferences = CandidatePreference(
        work_modes=["modalidade não reconhecida"],
        knockout_rules={
            "exclude_companies": "Empresa A",
            "exclude_required_skills": ["Docker", False],
            "max_commute_km": 30,
        },
    )
    job = Job(company="Empresa A", work_mode="remoto")

    assert evaluate_knockouts(job, preferences, taxonomy=taxonomy).eligible
    assert evaluate_knockouts(job, None, taxonomy=taxonomy).eligible


def test_coleta_todas_as_flags_da_vaga(taxonomy: SkillTaxonomy) -> None:
    preferences = CandidatePreference(
        locations=["Recife"],
        work_modes=["remoto"],
        knockout_rules={
            "exclude_companies": ["Empresa X"],
            "exclude_required_skills": ["Docker"],
        },
    )
    job = Job(company="Empresa X", location="São Paulo", work_mode="presencial")

    result = evaluate_knockouts(
        job, preferences, taxonomy=taxonomy, required_skill_names=["Docker"]
    )

    assert not result.eligible
    assert [flag.code for flag in result.flags] == [
        KnockoutCode.EXCLUDED_COMPANY,
        KnockoutCode.EXCLUDED_REQUIRED_SKILL,
        KnockoutCode.WORK_MODE_MISMATCH,
        KnockoutCode.LOCATION_MISMATCH,
    ]
