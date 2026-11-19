"""Testes unitários da similaridade textual (camada 4)."""

from __future__ import annotations

from app.services.similarity import (
    SIMILARITY_THRESHOLD,
    is_similar,
    title_similarity,
)


def test_identical_titles_score_100() -> None:
    assert title_similarity("Engenheiro de Dados", "Engenheiro de Dados") == 100.0


def test_accents_case_and_spacing_are_ignored() -> None:
    assert title_similarity("  ENGENHEIRO   de DADOS ", "engenheiro de dados") == 100.0


def test_word_order_does_not_lower_the_score() -> None:
    assert title_similarity("Dados Engenheiro de", "Engenheiro de Dados") == 100.0


def test_abbreviation_is_flagged_as_similar() -> None:
    score = title_similarity("Engenheiro de Dados Sênior", "Engenheiro de Dados Sr.")

    assert score >= SIMILARITY_THRESHOLD
    assert is_similar("Engenheiro de Dados Sênior", "Engenheiro de Dados Sr.")


def test_different_roles_are_not_similar() -> None:
    score = title_similarity("Desenvolvedor Python", "Analista de Dados")

    assert score < SIMILARITY_THRESHOLD
    assert not is_similar("Desenvolvedor Python", "Analista de Dados")


def test_empty_title_never_matches() -> None:
    assert title_similarity(None, "Engenheiro de Dados") == 0.0
    assert title_similarity("   ", "Engenheiro de Dados") == 0.0
    assert not is_similar("", "")
