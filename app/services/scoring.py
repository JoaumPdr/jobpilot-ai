"""Carrega a configuração local usada pelo cálculo determinístico do matching."""

import tomllib
from decimal import Decimal
from pathlib import Path

from app.matching.scoring import ScoreCalculator, ScoringConfig
from app.services.skill_taxonomy import load_skill_taxonomy

_DEFAULT_CONFIG = (
    Path(__file__).resolve().parents[2] / "data" / "matching" / "scoring.toml"
)


def load_scoring_config(path: Path = _DEFAULT_CONFIG) -> ScoringConfig:
    """Lê e valida a versão, os pesos positivos e as relações do arquivo TOML."""
    with path.open("rb") as file:
        return ScoringConfig.model_validate(tomllib.load(file, parse_float=Decimal))


def load_score_calculator() -> ScoreCalculator:
    """Monta o cálculo com a configuração e a taxonomia distribuídas."""
    return ScoreCalculator(load_scoring_config(), load_skill_taxonomy())
