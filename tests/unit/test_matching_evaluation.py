"""Cobre o protocolo das métricas e a reprodução do relatório versionado."""

from decimal import Decimal

from app.matching.job_requirements import RequirementType
from scripts.evaluate_matching import (
    DEFAULT_DATASET,
    DEFAULT_REPORT,
    Compatibility,
    ExtractionCount,
    GoldenSet,
    RankingCounts,
    compare_ranking,
    evaluate,
    extraction_counts,
    render_report,
)


def test_tipo_incorreto_vira_excesso_e_omissao() -> None:
    expected = {
        ("sql", RequirementType.REQUIRED),
        ("docker", RequirementType.PREFERRED),
    }
    predicted = {
        ("sql", RequirementType.REQUIRED),
        ("docker", RequirementType.REQUIRED),
    }

    counts = extraction_counts(expected, predicted)

    assert counts[ExtractionCount.TP] == 1
    assert counts[ExtractionCount.FP] == 1
    assert counts[ExtractionCount.FN] == 1


def test_ranking_cobre_empates_e_posiciona_score_nulo_no_fim() -> None:
    ranked = [
        (Compatibility.HIGH, Decimal("0.6")),
        (Compatibility.MEDIUM, Decimal("0.6")),
        (Compatibility.LOW, None),
        (Compatibility.LOW, Decimal("0.9")),
    ]

    result = compare_ranking(ranked)

    assert result == RankingCounts(concordant=2, tied=1, discordant=2)
    assert result.pairs == 5
    assert (
        compare_ranking(
            [(Compatibility.HIGH, Decimal(0)), (Compatibility.LOW, None)]
        ).concordant
        == 1
    )


def test_relatorio_versionado_e_reproduzivel() -> None:
    golden = GoldenSet.model_validate_json(DEFAULT_DATASET.read_bytes())
    result = evaluate(golden)

    assert len(golden.cases) >= 30
    assert {case.language for case in golden.cases} == {"en", "pt-BR"}
    assert result.evidence_total > 0
    assert result.evidence_total == result.evidence_literal
    assert render_report(result) == DEFAULT_REPORT.read_text(encoding="utf-8")
