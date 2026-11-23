"""Cobre o extrator de requisitos com descrições sintéticas e sem banco."""

import pytest

from app.matching.job_requirements import RequirementExtractor, RequirementType
from app.services.skill_taxonomy import load_skill_taxonomy


@pytest.fixture(scope="module")
def extractor() -> RequirementExtractor:
    """Usa a taxonomia distribuída para testar limites e aliases reais."""
    return RequirementExtractor(load_skill_taxonomy())


def test_extrai_secoes_e_preserva_evidencia_literal(
    extractor: RequirementExtractor,
) -> None:
    description = (
        "Responsabilidades:\n- Trabalhar com AWS.\n"
        "## Requisitos\n- Experiência com Python e PostgreSQL.\n"
        "### Diferenciais\n- Modelagem de dados e Docker.\n"
        "Benefícios:\n- Treinamento em Kubernetes."
    )

    requirements = extractor.extract(description)

    assert [
        (item.skill.canonical_name, item.requirement_type, item.evidence_snippet)
        for item in requirements
    ] == [
        ("Python", RequirementType.REQUIRED, "Experiência com Python e PostgreSQL."),
        (
            "PostgreSQL",
            RequirementType.REQUIRED,
            "Experiência com Python e PostgreSQL.",
        ),
        ("Data Modeling", RequirementType.PREFERRED, "Modelagem de dados e Docker."),
        ("Docker", RequirementType.PREFERRED, "Modelagem de dados e Docker."),
    ]
    assert all(item.confidence == 0.85 for item in requirements)
    assert all(item.evidence_snippet in description for item in requirements)


def test_classifica_ingles_com_gatilhos_e_secoes_inline(
    extractor: RequirementExtractor,
) -> None:
    requirements = extractor.extract(
        "**Required qualifications:** Python, SQL;\n"
        "Nice to have: Node.js and Postgres.\n"
        "Must know Docker; Kubernetes is a plus."
    )

    assert {
        item.skill.canonical_name: item.requirement_type for item in requirements
    } == {
        "Python": RequirementType.REQUIRED,
        "SQL": RequirementType.REQUIRED,
        "Node.js": RequirementType.PREFERRED,
        "PostgreSQL": RequirementType.PREFERRED,
        "Docker": RequirementType.REQUIRED,
        "Kubernetes": RequirementType.PREFERRED,
    }
    assert requirements[-1].confidence > requirements[0].confidence


def test_gatilho_local_e_repeticoes(extractor: RequirementExtractor) -> None:
    requirements = extractor.extract(
        "Requisitos:\n- Python é desejável; Docker.\n"
        "- Python é obrigatório.\n- SQL.\n- SQL is required.\n"
        "- PostgreSQL não é obrigatório."
    )

    assert {
        item.skill.canonical_name: (item.requirement_type, item.evidence_snippet)
        for item in requirements
    } == {
        "Python": (RequirementType.REQUIRED, "Python é obrigatório."),
        "Docker": (RequirementType.REQUIRED, "Docker."),
        "SQL": (RequirementType.REQUIRED, "SQL is required."),
    }


def test_separa_gatilhos_explicitos_e_ignora_negacao(
    extractor: RequirementExtractor,
) -> None:
    requirements = extractor.extract(
        "Python is required, Docker is preferred, Java is not required."
    )

    assert [
        (item.skill.canonical_name, item.requirement_type) for item in requirements
    ] == [("Python", RequirementType.REQUIRED), ("Docker", RequirementType.PREFERRED)]


def test_pontuacao_alias_longo_e_termos_curtos(
    extractor: RequirementExtractor,
) -> None:
    skills = extractor.extract(
        "Requirements:\n- C++, C#, C and R.\n"
        "- Must go to the office.\n- Go, .NET, JavaScript and Spark SQL.\n"
        "- Knowledge of machine learning operations."
    )

    assert [item.skill.canonical_name for item in skills] == [
        "C++",
        "C#",
        "C",
        "R",
        "Go",
        ".NET",
        "JavaScript",
        "Spark SQL",
        "MLOps",
    ]


@pytest.mark.parametrize("description", [None, "", "   ", "We use Python and AWS."])
def test_ignora_texto_sem_requisitos(
    extractor: RequirementExtractor, description: str | None
) -> None:
    assert extractor.extract(description) == ()
