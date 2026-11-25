"""Confere contratos entre etapas sem executar serviços nem acessar o banco."""

from uuid import UUID

import pytest
from pydantic import ValidationError

from app.orchestration.state import PipelineState


def snapshot(count: int = 1) -> dict:
    """Monta resultados sintéticos na fronteira inclusiva do funil."""
    ids = [str(UUID(int=index + 1)) for index in range(count)]
    return {
        "run_id": str(UUID(int=100)),
        "candidate_id": str(UUID(int=101)),
        "llm_enabled": True,
        "imported": {"batch_id": str(UUID(int=102)), "job_ids": ids},
        "normalized_ids": ids,
        "deduplicated_ids": ids,
        "filtered_ids": ids,
        "matching": {
            "scoring_version": "deterministico-v1",
            "jobs": [{"job_id": job_id, "score": "0.80"} for job_id in ids],
        },
        "selected_ids": ids,
        "analyzed_ids": ids,
    }


def test_estado_inicial_e_conclusao_sem_vagas() -> None:
    data = snapshot(0)
    initial = PipelineState(run_id=data["run_id"], candidate_id=data["candidate_id"])
    assert initial.selected_ids is None
    assert initial.llm_enabled is False
    completed = PipelineState.model_validate({**data, "llm_enabled": False})
    assert completed.selected_ids == completed.analyzed_ids == ()


def test_snapshot_preserva_versao_ordem_e_resultado_parcial() -> None:
    data = snapshot(3)
    data["matching"]["jobs"][0]["score"] = None
    data["selected_ids"] = data["filtered_ids"][2:0:-1]
    data["analyzed_ids"] = data["selected_ids"][:1]
    state = PipelineState.model_validate(data)
    restored = PipelineState.model_validate_json(state.model_dump_json())
    assert restored == state
    assert restored.selected_ids == (UUID(int=3), UUID(int=2))


@pytest.mark.parametrize(
    "change",
    [
        {"run_id": "inválido"},
        {"campo_extra": 1},
        {"filters": {"candidate_id": str(UUID(int=999))}},
        {"normalized_ids": None},
        {"deduplicated_ids": [str(UUID(int=999))]},
        {"filtered_ids": [str(UUID(int=1))] * 2},
        {"analyzed_ids": [str(UUID(int=999))]},
        {"llm_enabled": False},
        {"llm_enabled": "false"},
    ],
)
def test_rejeita_snapshot_incoerente(change: dict) -> None:
    with pytest.raises(ValidationError):
        PipelineState.model_validate({**snapshot(), **change})


@pytest.mark.parametrize("score", [None, "0.7999", "-0.1", "1.1", "NaN"])
def test_rejeita_score_invalido_para_selecao(score: str | None) -> None:
    data = snapshot()
    data["matching"]["jobs"][0]["score"] = score
    with pytest.raises(ValidationError):
        PipelineState.model_validate(data)


def test_limite_do_funil() -> None:
    PipelineState.model_validate(snapshot(10))
    with pytest.raises(ValidationError):
        PipelineState.model_validate(snapshot(11))
