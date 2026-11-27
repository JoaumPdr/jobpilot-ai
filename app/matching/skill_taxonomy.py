"""Índice determinístico de habilidades usado pelas regras de matching."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from app.services.normalization import comparison_text


@dataclass(frozen=True)
class TaxonomySkill:
    """Habilidade do catálogo com nome de exibição, categoria e aliases."""

    canonical_name: str
    category: str
    aliases: tuple[str, ...] = ()


class SkillTaxonomy:
    """Resolve nomes e aliases inteiros a partir de um catálogo já carregado."""

    def __init__(self, skills: Iterable[TaxonomySkill]) -> None:
        self._skills = tuple(skills)
        self._by_term: dict[str, TaxonomySkill] = {}
        for skill in self._skills:
            for term in (skill.canonical_name, *skill.aliases):
                key = comparison_text(term)
                if not key:
                    raise ValueError(
                        f"Taxonomia: termo vazio em {skill.canonical_name!r}."
                    )
                previous = self._by_term.setdefault(key, skill)
                # Um alias ambíguo tornaria o resultado dependente da ordem
                # das entradas do catálogo.
                if previous != skill:
                    raise ValueError(
                        f"Taxonomia: {term!r} é ambíguo entre "
                        f"{previous.canonical_name!r} e {skill.canonical_name!r}."
                    )

    @property
    def skills(self) -> tuple[TaxonomySkill, ...]:
        """Devolve as habilidades canônicas na ordem do catálogo."""
        return self._skills

    def lookup(self, term: str) -> TaxonomySkill | None:
        """Resolve um termo inteiro ou devolve None se ele for desconhecido."""
        return self._by_term.get(comparison_text(term))

    def unrecognized_terms(self, terms: Iterable[str]) -> dict[str, int]:
        """Conta termos desconhecidos e ordena por frequência, depois por nome.

        Por exemplo, duas ocorrências de "Ômega" e "omega" geram
        `{"omega": 2}` quando o termo está ausente do catálogo.
        """
        counts: Counter[str] = Counter()
        for term in terms:
            key = comparison_text(term)
            if key and key not in self._by_term:
                counts[key] += 1
        return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
