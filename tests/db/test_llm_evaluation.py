import json
from dataclasses import replace
from decimal import Decimal
from unittest.mock import Mock

from sqlalchemy import Engine, delete
from sqlalchemy.orm import sessionmaker

from app.llm.providers import LLMProvider, LLMResponse
from app.models import Candidate, Job, LLMCache
from scripts.evaluate_llm import (
    DEFAULT_MAX_TOKENS,
    choose_funnel,
    compare_funnels,
    evaluate_llm,
    render_comparison,
)
from scripts.evaluate_matching import DEFAULT_DATASET, GoldenSet


def test_avaliacao_mede_reparo_e_mantem_base_em_falha(test_engine: Engine) -> None:
    golden = GoldenSet.model_validate_json(DEFAULT_DATASET.read_bytes())
    golden = golden.model_copy(update={"cases": golden.cases[:2]})
    provider = Mock(spec=LLMProvider)
    provider.name = "fake"
    provider.model = "contrato-teste"
    calls = 0

    def complete(*, system_prompt: str, user_prompt: str) -> LLMResponse:
        nonlocal calls
        calls += 1
        response = ""
        if calls == 2:
            response = json.dumps(
                {
                    "job_id": json.loads(user_prompt)["job_id"],
                    "matched_skills": [],
                    "missing_skills": [],
                    "unknown_requirements": [],
                    "recommendation": "Revisar.",
                    "explanation": "Saída sintética.",
                    "evidence": [],
                }
            )
        return LLMResponse(response, tokens_in=5, tokens_out=3)

    provider.complete.side_effect = complete
    sessions = sessionmaker(bind=test_engine, autoflush=False)
    try:
        rows = evaluate_llm(golden, sessions, provider)
    finally:
        with sessions.begin() as db:
            db.execute(delete(LLMCache))
            db.execute(delete(Job).where(Job.company == "Golden set"))
            db.execute(delete(Candidate).where(Candidate.name == "Perfil sintético"))

    assert [row.status for row in rows] == ["reparo", "saída inválida"]
    assert [row.calls for row in rows] == [2, 2]
    assert [row.tokens for row in rows] == [16, 16]
    assert all(row.cost == 0 and row.provider_ms >= 0 for row in rows)
    assert rows[1].baseline == rows[1].augmented

    cases = [
        replace(
            rows[0],
            case=rows[0].case.model_copy(update={"compatibility": "high"}),
            score=Decimal("0.72"),
        ),
        replace(
            rows[1],
            case=rows[1].case.model_copy(update={"compatibility": "low"}),
            score=Decimal("0.62"),
        ),
    ]
    selected = choose_funnel(compare_funnels(cases))
    assert selected.threshold == Decimal("0.70")
    assert selected.top_n == 3
    assert selected.high == 1
    report = render_comparison(
        rows,
        model="contrato-teste",
        digest="sintético",
        version="teste",
        max_tokens=DEFAULT_MAX_TOKENS,
    )
    assert "Determinístico + LLM" in report
    assert "4 chamadas" in report
    assert "reparo produziu saída válida em 1" in report
    assert "Saída sintética." not in report
