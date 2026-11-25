"""Gera a avaliação offline do extrator e do ranking determinístico."""

import argparse
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from enum import IntEnum
from itertools import combinations
from pathlib import Path
from statistics import mean, median
from time import perf_counter
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.matching.job_requirements import RequirementExtractor, RequirementType
from app.matching.knockouts import KnockoutResult
from app.matching.skill_taxonomy import SkillTaxonomy
from app.services.normalization import comparison_text
from app.services.scoring import load_score_calculator
from app.services.skill_taxonomy import get_default_skill_taxonomy

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "golden" / "matching.json"
DEFAULT_REPORT = ROOT / "docs" / "evaluation.md"
LLM_REPORT_MARKER = "\n<!-- llm-evaluation -->\n"


class Compatibility(IntEnum):
    """Faixas ordinais da avaliação manual de compatibilidade."""

    LOW = 0
    MEDIUM = 1
    HIGH = 2


class GoldenCase(BaseModel):
    """Uma vaga expurgada e seus rótulos atribuídos na curadoria."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(pattern=r"^GS-[0-9]{3}$")
    source_row: int = Field(ge=0)
    language: Literal["en", "pt-BR"]
    role: str = Field(min_length=1)
    description: str = Field(min_length=1)
    required: list[str]
    preferred: list[str]
    compatibility: Literal["low", "medium", "high"]


class GoldenSet(BaseModel):
    """Perfil sintético fixo e conjunto de vagas para reproduzir a avaliação."""

    model_config = ConfigDict(extra="forbid")

    source_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    candidate_skills: list[str] = Field(min_length=1)
    confirmed_absent: list[str]
    cases: list[GoldenCase] = Field(min_length=30)

    @model_validator(mode="after")
    def _validate_cases(self) -> Self:
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ValueError("O golden set contém identificadores duplicados.")
        if len({case.source_row for case in self.cases}) != len(self.cases):
            raise ValueError("O golden set contém anúncios de origem duplicados.")
        return self


class ExtractionCount(IntEnum):
    """Contadores de requisitos para as métricas de extração."""

    TP = 0
    FP = 1
    FN = 2


RequirementKey = tuple[str, RequirementType]
RankedCase = tuple[Compatibility, Decimal | None]


def extraction_counts[Key](
    expected: set[Key], predicted: set[Key]
) -> Counter[ExtractionCount]:
    """Conta acertos, extras e omissões. Tipo incorreto gera um extra e uma omissão."""
    return Counter(
        {
            ExtractionCount.TP: len(expected & predicted),
            ExtractionCount.FP: len(predicted - expected),
            ExtractionCount.FN: len(expected - predicted),
        }
    )


@dataclass(frozen=True)
class RankingCounts:
    """Resultado da comparação por pares de vagas com rótulos distintos."""

    concordant: int
    tied: int
    discordant: int

    @property
    def pairs(self) -> int:
        return self.concordant + self.tied + self.discordant


def compare_ranking(ranked: list[RankedCase]) -> RankingCounts:
    """Ignora pares com mesmo rótulo e posiciona vagas sem score ao final."""
    concordant = tied = discordant = 0
    for (first_label, first_score), (second_label, second_score) in combinations(
        ranked, 2
    ):
        if first_label == second_label:
            continue
        first = (first_score is not None, first_score or Decimal(0))
        second = (second_score is not None, second_score or Decimal(0))
        if first == second:
            tied += 1
        elif (first > second) == (first_label > second_label):
            concordant += 1
        else:
            discordant += 1
    return RankingCounts(concordant, tied, discordant)


@dataclass
class Evaluation:
    """Contadores e medições da execução do benchmark."""

    scoring_version: str
    source_revision: str
    extraction: Counter[ExtractionCount] = field(default_factory=Counter)
    by_language: dict[str, Counter[ExtractionCount]] = field(default_factory=dict)
    ranked: list[RankedCase] = field(default_factory=list)
    elapsed_ms: list[float] = field(default_factory=list)
    evidence_total: int = 0
    evidence_literal: int = 0


def skill_key(name: str, taxonomy: SkillTaxonomy) -> str:
    """Obtém a chave comum para comparar rótulos e resultados."""
    skill = taxonomy.lookup(name)
    return comparison_text(skill.canonical_name if skill else name)


def evaluate(golden: GoldenSet) -> Evaluation:
    """Avalia a extração e o ranking a partir das descrições, sem consultar a rede."""
    calculator = load_score_calculator()
    taxonomy = get_default_skill_taxonomy()
    extractor = RequirementExtractor(taxonomy)
    evaluation = Evaluation(calculator.scoring_version, golden.source_revision)

    for case in golden.cases:
        required = {skill_key(name, taxonomy) for name in case.required}
        preferred = {skill_key(name, taxonomy) for name in case.preferred}
        if "" in required | preferred or required & preferred:
            raise ValueError(f"Rótulos de requisitos inválidos em {case.id}.")
        expected = {(name, RequirementType.REQUIRED) for name in required} | {
            (name, RequirementType.PREFERRED) for name in preferred
        }
        start = perf_counter()
        extracted = extractor.extract(case.description)
        result = calculator.score(
            extracted,
            golden.candidate_skills,
            knockouts=KnockoutResult(),
            confirmed_absent=golden.confirmed_absent,
        )
        evaluation.elapsed_ms.append((perf_counter() - start) * 1000)

        predicted = {
            (skill_key(item.skill.canonical_name, taxonomy), item.requirement_type)
            for item in extracted
        }
        counts = extraction_counts(expected, predicted)
        evaluation.extraction.update(counts)
        evaluation.by_language.setdefault(case.language, Counter()).update(counts)
        evaluation.ranked.append(
            (Compatibility[case.compatibility.upper()], result.score)
        )
        evaluation.evidence_total += len(extracted)
        evaluation.evidence_literal += sum(
            bool(item.evidence_snippet and item.evidence_snippet in case.description)
            for item in extracted
        )
    return evaluation


def _percentage(numerator: float, denominator: int) -> str:
    return f"{numerator / denominator:.2%}".replace(".", ",") if denominator else "—"


def _extraction_row(label: str, counts: Counter[ExtractionCount]) -> str:
    tp, fp, fn = (counts[key] for key in ExtractionCount)
    return (
        f"| {label} | {tp} | {fp} | {fn} | "
        f"{_percentage(tp, tp + fp)} | {_percentage(tp, tp + fn)} | "
        f"{_percentage(2 * tp, 2 * tp + fp + fn)} |"
    )


def render_report(evaluation: Evaluation) -> str:
    """Gera Markdown estável. A latência fica disponível sob demanda na CLI."""
    ranking = compare_ranking(evaluation.ranked)
    labels = Counter(label for label, _ in evaluation.ranked)
    scored = sum(score is not None for _, score in evaluation.ranked)
    lines = [
        "# Avaliação do matching determinístico",
        "",
        (
            f"Versão de score: `{evaluation.scoring_version}`. Amostra: "
            f"{len(evaluation.ranked)} vagas. Revisão da fonte: `{evaluation.source_revision}`."
        ),
        "[Procedência, licenciamento e protocolo](../data/golden/README.md)",
        "[Metodologia do score](matching-methodology.md)",
        "",
        "## Extração",
        "",
        (
            "Métricas micro por par de habilidade e tipo do requisito. Um tipo incorreto "
            "conta como falso positivo no tipo previsto e falso negativo no esperado."
        ),
        "",
        "| Segmento | VP | FP | FN | Precisão | Revocação | F1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
        _extraction_row("Total", evaluation.extraction),
        *(
            _extraction_row(lang, counts)
            for lang, counts in sorted(evaluation.by_language.items())
        ),
        "",
        "## Ranking",
        "",
        (
            f"Compatibilidade manual: {labels[Compatibility.HIGH]} alta, "
            f"{labels[Compatibility.MEDIUM]} média e {labels[Compatibility.LOW]} baixa."
        ),
        f"Vagas com score: {scored} de {len(evaluation.ranked)}.",
        "",
        (
            f"Concordância ordinal: **{_percentage(ranking.concordant + ranking.tied / 2, ranking.pairs)}** "
            f"em {ranking.pairs} pares comparáveis. Foram {ranking.concordant} concordantes, "
            f"{ranking.tied} empatados e {ranking.discordant} divergentes."
        ),
        (
            "Pares com o mesmo rótulo ficam fora da métrica. Empates de score valem "
            "meio acerto. Vagas sem score ficam ao final."
        ),
        "",
        "## Evidências e reprodução",
        "",
        (
            f"Trechos literais na descrição: {evaluation.evidence_literal} de "
            f"{evaluation.evidence_total} requisitos extraídos."
        ),
        (
            "A avaliação roda localmente e faz zero chamadas a modelos externos. "
            "Da raiz do repositório, use `--check` para verificar o relatório. "
            "A opção `--timing` mede a média e a mediana de extração mais score por vaga."
        ),
        "",
        "```powershell",
        "uv run python -m scripts.evaluate_matching --check --timing",
        "```",
        "",
        (
            "Para regenerar o arquivo após uma mudança de dados ou de apresentação, "
            "execute `uv run python -m scripts.evaluate_matching`."
        ),
        "",
        "## Interpretação e limites",
        "",
        (
            "A precisão indica a proporção de acertos entre os requisitos previstos. "
            "A revocação indica a proporção de requisitos rotulados que o extrator recuperou. "
            "A concordância ordinal mede a ordem relativa das vagas, em pares com rótulos distintos."
        ),
        "",
        (
            "A amostra é de conveniência e avalia um único perfil sintético. A porção "
            "PT-BR é adaptada de anúncios em inglês. A medição cobre a extração e o score "
            "em memória, com as vagas elegíveis. A API, a persistência e as regras "
            "eliminatórias são exercitadas pela suíte de testes."
        ),
        "",
        (
            "Este resultado estabelece a linha de base determinística. Uma comparação "
            "com uma variante semântica nas mesmas vagas é necessária para medir o ganho. "
            "[Decisão sobre embeddings multilíngues](adr/0012-adiar-embeddings-multilingues.md)"
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    """Gera ou verifica o relatório Markdown e, opcionalmente, mede latência."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--timing", action="store_true")
    args = parser.parse_args()

    evaluation = evaluate(GoldenSet.model_validate_json(args.dataset.read_bytes()))
    report = render_report(evaluation)
    previous = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
    baseline, marker, comparison = previous.partition(LLM_REPORT_MARKER)
    if args.check:
        if baseline != report:
            parser.exit(1, "O relatório de avaliação está desatualizado.\n")
    else:
        args.output.write_text(
            report + marker + comparison, encoding="utf-8", newline="\n"
        )
    if args.timing:
        print(
            f"Latência por vaga: {mean(evaluation.elapsed_ms):.3f} ms em média, "
            f"{median(evaluation.elapsed_ms):.3f} ms de mediana."
        )


if __name__ == "__main__":
    main()
