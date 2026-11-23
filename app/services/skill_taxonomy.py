"""Carrega o catálogo local de habilidades para os consumidores de matching.

A leitura fica no serviço. O índice e o relatório continuam testáveis sem
depender do sistema de arquivos.
"""

import tomllib
from pathlib import Path

from app.matching.skill_taxonomy import SkillTaxonomy, TaxonomySkill

_DEFAULT_CATALOG = (
    Path(__file__).resolve().parents[2] / "data" / "taxonomy" / "skills.toml"
)


def load_skill_taxonomy(path: Path = _DEFAULT_CATALOG) -> SkillTaxonomy:
    """Carrega as tabelas de categoria de um catálogo TOML em UTF-8.

    Cada tabela mapeia nomes canônicos para listas de aliases. Um erro de
    leitura levanta OSError. TOML inválido, campos vazios ou colisões levantam
    ValueError para que o chamador corrija o catálogo antes de usá-lo.
    """
    with path.open("rb") as file:
        catalog = tomllib.load(file)
    if not catalog:
        raise ValueError("Taxonomia: o catálogo está vazio.")

    skills: list[TaxonomySkill] = []
    for category, entries in catalog.items():
        if not category.strip() or not isinstance(entries, dict) or not entries:
            raise ValueError(f"Taxonomia: categoria inválida: {category!r}.")
        for name, aliases in entries.items():
            if not isinstance(aliases, list) or any(
                not isinstance(alias, str) for alias in aliases
            ):
                raise ValueError(f"Taxonomia: {name!r} deve ter uma lista de aliases.")
            skills.append(TaxonomySkill(name, category, tuple(aliases)))
    return SkillTaxonomy(skills)
