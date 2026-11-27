"""Verifica o catálogo distribuído e a resolução determinística de termos."""

from pathlib import Path

import pytest

from app.matching.skill_taxonomy import SkillTaxonomy, TaxonomySkill
from app.services.skill_taxonomy import load_skill_taxonomy


@pytest.fixture(scope="module")
def taxonomy() -> SkillTaxonomy:
    """Carrega o arquivo real para detectar entradas inválidas ou ambíguas."""
    return load_skill_taxonomy()


def test_catalogo_tem_pelo_menos_150_habilidades(taxonomy: SkillTaxonomy) -> None:
    assert len(taxonomy.skills) >= 150
    assert len({skill.canonical_name for skill in taxonomy.skills}) == len(
        taxonomy.skills
    )
    assert len({skill.category for skill in taxonomy.skills}) >= 5


@pytest.mark.parametrize(
    ("term", "name", "category"),
    [
        ("  LogÍstica  ", None, None),
        (" BANCO  DE DADOS   RELACIONAL ", "Relational Databases", "bancos_de_dados"),
        ("relational database", "Relational Databases", "bancos_de_dados"),
        (
            "processamento de linguagem natural",
            "Natural Language Processing",
            "ia_e_ml",
        ),
        ("APRENDIZAGEM DE MÁQUINA", "Machine Learning", "ia_e_ml"),
        ("  postgres ", "PostgreSQL", "bancos_de_dados"),
        ("c", "C", "linguagens"),
        ("C++", "C++", "linguagens"),
        ("c#", "C#", "linguagens"),
        (".net", ".NET", "backend"),
        ("nodejs", "Node.js", "backend"),
        ("experiência em Python", None, None),
        (" ", None, None),
    ],
)
def test_busca_exata_por_nome_ou_alias(
    taxonomy: SkillTaxonomy, term: str, name: str | None, category: str | None
) -> None:
    skill = taxonomy.lookup(term)

    if name is None:
        assert skill is None
    else:
        assert skill is not None
        assert (skill.canonical_name, skill.category) == (name, category)


def test_relatorio_agrupa_variações_e_ignora_termos_conhecidos(
    taxonomy: SkillTaxonomy,
) -> None:
    report = taxonomy.unrecognized_terms(
        iter(["Zeta", " Ômega ", "zéta", "ALFA", "Python", "postgres", " ", "omega"])
    )

    assert list(report.items()) == [("omega", 2), ("zeta", 2), ("alfa", 1)]
    assert taxonomy.unrecognized_terms(["Python"]) == {}


def test_alias_equivalente_da_mesma_habilidade_e_aceito() -> None:
    skill = TaxonomySkill("Café", "dados", ("cafe", "CAFÉ"))

    assert SkillTaxonomy([skill]).lookup("cafe") == skill


@pytest.mark.parametrize("alias", ["CAFÉ", "COMPARAÇÃO"])
def test_colisao_entre_habilidades_invalida_catalogo(alias: str) -> None:
    first = TaxonomySkill("Café", "dados", ("comparacao",))
    second = TaxonomySkill("Teste", "qualidade", (alias,))

    with pytest.raises(ValueError, match="Café.*Teste"):
        SkillTaxonomy([first, second])


def test_nome_canonico_repetido_em_outra_categoria_e_invalido() -> None:
    with pytest.raises(ValueError, match="Café"):
        SkillTaxonomy(
            [TaxonomySkill("Café", "dados"), TaxonomySkill("cafe", "qualidade")]
        )


@pytest.mark.parametrize(
    "content",
    [
        "",
        "[dados]",
        "dados = 3",
        '[dados]\nPython = "linguagem Python"',
        "[dados]\nPython = [12]",
        '[dados]\nPython = [" "]',
        '[dados]\n" " = []',
        '[" "]\nPython = []',
    ],
)
def test_carregamento_rejeita_estrutura_invalida(tmp_path: Path, content: str) -> None:
    path = tmp_path / "skills.toml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="Taxonomia"):
        load_skill_taxonomy(path)
