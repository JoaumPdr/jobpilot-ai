"""Exercita o grafo inteiro de transições do plano."""

import pytest

from app.core.errors import InvalidDataError
from app.models.application import ApplicationStatus
from app.services.applications import validate_transition

EXPECTED_TARGETS = {
    "salva": {"planejada", "rejeitada", "encerrada"},
    "planejada": {"aplicada", "rejeitada", "encerrada"},
    "aplicada": {"entrevista", "rejeitada", "encerrada"},
    "entrevista": {"oferta", "rejeitada", "encerrada"},
    "oferta": {"rejeitada", "encerrada"},
    "rejeitada": set(),
    "encerrada": set(),
}


@pytest.mark.parametrize("current", list(ApplicationStatus))
@pytest.mark.parametrize("target", list(ApplicationStatus))
def test_transition_matches_plan(
    current: ApplicationStatus, target: ApplicationStatus
) -> None:
    if target.value in EXPECTED_TARGETS[current.value]:
        validate_transition(current, target)
    else:
        with pytest.raises(InvalidDataError, match=f"'{current}' para '{target}'"):
            validate_transition(current, target)
