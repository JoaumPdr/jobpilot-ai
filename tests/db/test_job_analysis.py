import json
import traceback
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from unittest.mock import Mock
from uuid import UUID

import pytest
from sqlalchemy import Engine, delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.errors import ConflictError, InvalidDataError, NotFoundError
from app.llm.job_analysis import JobAnalysisOutputError
from app.llm.providers import LLMProvider, LLMProviderError, LLMResponse
from app.matching.job_requirements import RequirementType
from app.matching.scoring import MatchLevel
from app.models import Candidate, Job, JobMatch, LLMCache
from app.repositories.matching import MatchRepository
from app.schemas.matching import MatchAnalysis, MatchEvidence
from app.services import job_analysis
from app.services.job_analysis import JobAnalysisPersistenceError, JobAnalysisService
from app.services.llm_cache import LLMCacheService

_VERSION = "deterministico-v1"
_RAW = "Texto sintético que não deve aparecer nos logs."
_SCORE = Decimal("0.57")


@dataclass(frozen=True)
class Scenario:
    sessions: sessionmaker[Session]
    candidate_id: UUID
    job_id: UUID
    match_id: UUID

    def service(self, session: Session, provider: LLMProvider) -> JobAnalysisService:
        return JobAnalysisService(
            MatchRepository(session), LLMCacheService(provider, sessions=self.sessions)
        )


def _item(
    skill: str, quote: str, level: MatchLevel, candidate_skill: str | None = None
) -> MatchEvidence:
    return MatchEvidence(
        skill_name=skill,
        requirement_type=RequirementType.REQUIRED,
        confidence=1,
        evidence_snippet=quote,
        level=level,
        weight=Decimal(1),
        factor=None,
        candidate_skill=candidate_skill,
    )


@pytest.fixture
def scenario(test_engine: Engine) -> Iterator[Scenario]:
    sessions = sessionmaker(bind=test_engine, autoflush=False)
    with sessions.begin() as db:
        candidate = Candidate(name="Perfil teste", resume_text=_RAW)
        job = Job(
            title="Analista",
            company="Equipe",
            source="manual",
            url="https://example.invalid/analista",
            canonical_url="https://example.invalid/analista",
            fingerprint="analise-llm-teste",
            description=(
                "Material da equipe sobre Python. "
                "Requisitos: Python obrigatório. Go obrigatório. Rust é desejável."
            ),
        )
        matching = MatchAnalysis(
            weighted_sum=Decimal(1),
            total_weight=Decimal(3),
            met=[_item("Python", "Python obrigatório", MatchLevel.EXACT, "Python")],
            absent=[_item("Go", "Go obrigatório", MatchLevel.ABSENT)],
            unconfirmed=[_item("Rust", "Rust é desejável", MatchLevel.UNCONFIRMED)],
        )
        db.add_all([candidate, job])
        db.flush()
        match = JobMatch(
            candidate_id=candidate.id,
            job_id=job.id,
            scoring_version=_VERSION,
            deterministic_score=_SCORE,
            match_score=_SCORE,
            analysis=matching.model_dump(mode="json"),
            knockout_flags=[],
        )
        db.add(match)
        db.flush()
        state = Scenario(sessions, candidate.id, job.id, match.id)
    try:
        yield state
    finally:
        with sessions.begin() as db:
            db.execute(delete(LLMCache))
            db.execute(delete(Candidate).where(Candidate.id == state.candidate_id))
            db.execute(delete(Job).where(Job.id == state.job_id))


def _valid_payload(job_id: UUID) -> dict[str, object]:
    return {
        "job_id": str(job_id),
        "matched_skills": ["Python"],
        "missing_skills": ["Go"],
        "unknown_requirements": ["Rust"],
        "recommendation": _RAW,
        "explanation": _RAW,
        "evidence": [
            {"requirement": "Python", "source": "job", "quote": "Python obrigatório"},
            {"requirement": "Python", "source": "profile", "quote": "Python"},
            {"requirement": "Go", "source": "job", "quote": "Go obrigatório"},
            {"requirement": "Go", "source": "profile", "quote": "Go"},
        ],
    }


def _provider(*replies: str | LLMProviderError) -> Mock:
    provider = Mock(spec=LLMProvider)
    provider.name = "fake"
    provider.model = "simulado"
    provider.complete.side_effect = [
        LLMResponse(reply, tokens_in=9, tokens_out=3)
        if isinstance(reply, str)
        else reply
        for reply in replies
    ]
    return provider


def test_analise_valida_e_reutilizada_sem_alterar_score(scenario: Scenario) -> None:
    provider = _provider(json.dumps(_valid_payload(scenario.job_id)))
    with scenario.sessions() as db:
        service = scenario.service(db, provider)
        result = service.analyze(scenario.candidate_id, scenario.job_id, _VERSION)
        assert (
            service.analyze(scenario.candidate_id, scenario.job_id, _VERSION) == result
        )
    provider.complete.assert_called_once()
    assert result.analysis.matched_skills == ["Python"]
    assert result.analysis.missing_skills == ["Go"]
    assert result.analysis.unknown_requirements == ["Rust"]
    assert len(result.analysis.evidence) == 4

    with scenario.sessions() as db:
        match = db.get(JobMatch, scenario.match_id)
        assert match is not None
        assert match.deterministic_score == match.match_score == _SCORE
        assert match.llm_analysis == {
            "prompt_version": "job-analysis-v2",
            "analysis": result.analysis.model_dump(mode="json"),
        }
        assert _RAW not in json.dumps(match.llm_analysis)


def test_itens_sem_evidencia_ou_contraditorios_ficam_sem_confirmacao(
    scenario: Scenario,
) -> None:
    payload = _valid_payload(scenario.job_id)
    payload["matched_skills"] = ["Python", "golang", "Kotlin"]
    payload["evidence"] = [
        {"requirement": "Python", "source": "job", "quote": "Go obrigatório"},
        {
            "requirement": "Python",
            "source": "job",
            "quote": "Material da equipe sobre Python.",
        },
        {"requirement": "Python", "source": "profile", "quote": "Python"},
        {"requirement": "golang", "source": "job", "quote": "Go obrigatório"},
        {"requirement": "Go", "source": "profile", "quote": "Go"},
        {"requirement": "Kotlin", "source": "profile", "quote": "Kotlin"},
        {"requirement": "Rust", "source": "profile", "quote": "Rust"},
        {"requirement": "Rust", "source": "job", "quote": "Rust obrigatório"},
    ]
    provider = _provider(json.dumps(payload))
    with scenario.sessions() as db:
        result = (
            scenario.service(db, provider)
            .analyze(scenario.candidate_id, scenario.job_id, _VERSION)
            .analysis
        )

    assert result.matched_skills == result.missing_skills == []
    assert result.unknown_requirements == ["Rust", "Python", "Go", "Kotlin"]
    assert [(item.requirement, item.source) for item in result.evidence] == [
        ("Python", "profile"),
        ("Go", "job"),
        ("Go", "profile"),
    ]
    provider.complete.assert_called_once()


@pytest.mark.parametrize("bad_reply", ["", "JSON inválido"])
def test_um_reparo_e_reutilizacao_pela_entrada_original(
    scenario: Scenario, bad_reply: str
) -> None:
    provider = _provider(bad_reply, json.dumps(_valid_payload(scenario.job_id)))
    with scenario.sessions() as db:
        service = scenario.service(db, provider)
        result = service.analyze(scenario.candidate_id, scenario.job_id, _VERSION)
        assert (
            service.analyze(scenario.candidate_id, scenario.job_id, _VERSION) == result
        )
        cached = db.scalars(select(LLMCache)).one()
        assert cached.prompt_version == result.prompt_version
    assert result.prompt_version == "job-analysis-v2+job-analysis-repair-v1"
    first, repaired = (call.kwargs for call in provider.complete.call_args_list)
    assert first["user_prompt"] == repaired["user_prompt"]
    assert repaired["system_prompt"].startswith(first["system_prompt"])
    assert "A tentativa anterior" in repaired["system_prompt"]


@pytest.mark.parametrize("first", ["", LLMProviderError("Falha sintética")])
def test_falha_e_registrada_sem_gravar_resposta(
    scenario: Scenario, first: str | LLMProviderError, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = _provider(first, _RAW)
    log = Mock()
    monkeypatch.setattr(job_analysis, "logger", log)
    expected = (
        LLMProviderError
        if isinstance(first, LLMProviderError)
        else JobAnalysisOutputError
    )
    with scenario.sessions() as db:
        with pytest.raises(expected):
            scenario.service(db, provider).analyze(
                scenario.candidate_id, scenario.job_id, _VERSION
            )
        match = db.get(JobMatch, scenario.match_id)
        assert match is not None and match.llm_analysis is None
        assert db.scalars(select(LLMCache)).first() is None

    assert provider.complete.call_count == (1 if expected is LLMProviderError else 2)
    log.warning.assert_called_once_with(
        "llm_job_analysis_failed",
        job_id=str(scenario.job_id),
        error_type=expected.__name__,
    )


def test_recusa_gravacao_quando_matching_muda_durante_a_geracao(
    scenario: Scenario,
) -> None:
    provider = _provider()

    def recalculate(**_messages: str) -> LLMResponse:
        with scenario.sessions() as db:
            stored = db.get(JobMatch, scenario.match_id)
            assert stored is not None
            changed = JobMatch(
                candidate_id=stored.candidate_id,
                job_id=stored.job_id,
                scoring_version=stored.scoring_version,
                deterministic_score=Decimal("0.25"),
                match_score=Decimal("0.25"),
                knockout_flags=stored.knockout_flags,
                analysis={**stored.analysis, "weighted_sum": "0"},
            )
            repository = MatchRepository(db)
            repository.upsert(changed)
            repository.commit()
        return LLMResponse(json.dumps(_valid_payload(scenario.job_id)))

    provider.complete.side_effect = recalculate
    with scenario.sessions() as db:
        with pytest.raises(ConflictError, match="mudou durante a análise"):
            scenario.service(db, provider).analyze(
                scenario.candidate_id, scenario.job_id, _VERSION
            )
        updated = db.get(JobMatch, scenario.match_id)
        assert updated is not None and updated.llm_analysis is None
        assert updated.match_score == Decimal("0.25")


def test_recalculo_invalida_analise_apenas_se_evidencias_mudarem(
    scenario: Scenario,
) -> None:
    provider = _provider(json.dumps(_valid_payload(scenario.job_id)))
    with scenario.sessions() as db:
        scenario.service(db, provider).analyze(
            scenario.candidate_id, scenario.job_id, _VERSION
        )
        stored = db.get(JobMatch, scenario.match_id)
        assert stored is not None and stored.llm_analysis is not None
        initial = stored.llm_analysis
        repository = MatchRepository(db)
        assert repository.upsert(stored).llm_analysis == initial
        repository.commit()

        changed = JobMatch(
            candidate_id=stored.candidate_id,
            job_id=stored.job_id,
            scoring_version=stored.scoring_version,
            deterministic_score=stored.deterministic_score,
            match_score=stored.match_score,
            knockout_flags=stored.knockout_flags,
            analysis={**stored.analysis, "weighted_sum": "0"},
        )
        assert repository.upsert(changed).llm_analysis is None


def test_matching_ausente_ou_invalido_impede_chamada(scenario: Scenario) -> None:
    provider = _provider()
    with scenario.sessions() as db:
        service = scenario.service(db, provider)
        with pytest.raises(NotFoundError):
            service.analyze(scenario.candidate_id, scenario.job_id, "outra versão")
        match = db.get(JobMatch, scenario.match_id)
        assert match is not None
        match.analysis = {"texto": _RAW}
        db.commit()
        with pytest.raises(
            InvalidDataError, match="Snapshot de matching inválido"
        ) as error:
            service.analyze(scenario.candidate_id, scenario.job_id, _VERSION)
    provider.complete.assert_not_called()
    assert _RAW not in "".join(traceback.format_exception(error.value))


def test_erro_sql_de_gravacao_oculta_parametros(
    scenario: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = _provider(json.dumps(_valid_payload(scenario.job_id)))
    save = Mock(side_effect=SQLAlchemyError(_RAW))
    monkeypatch.setattr(MatchRepository, "save_llm_analysis", save)
    with scenario.sessions() as db:
        with pytest.raises(
            JobAnalysisPersistenceError, match="Falha ao gravar"
        ) as error:
            scenario.service(db, provider).analyze(
                scenario.candidate_id, scenario.job_id, _VERSION
            )
        match = db.get(JobMatch, scenario.match_id)
        assert match is not None and match.llm_analysis is None
    assert _RAW not in "".join(traceback.format_exception(error.value))
