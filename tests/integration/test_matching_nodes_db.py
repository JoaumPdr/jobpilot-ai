import json
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies import (
    get_job_import_service,
    get_job_service,
    get_matching_service,
)
from app.llm.providers import LLMResponse
from app.models import Candidate, CandidateSkill, JobMatch, Skill
from app.orchestration.matching import analyze_jobs, match_jobs, select_jobs
from app.orchestration.state import ImportedJobs, PipelineState
from app.repositories.matching import MatchRepository
from app.services.job_analysis import JobAnalysisService
from app.services.llm_cache import LLMCacheService


class RecordingProvider:
    name = "fake"
    model = "teste-funil"

    def __init__(self) -> None:
        self.calls: list[UUID] = []

    def complete(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        job_id = UUID(json.loads(user_prompt)["job_id"])
        self.calls.append(job_id)
        return LLMResponse(
            text=json.dumps(
                {
                    "job_id": str(job_id),
                    "matched_skills": [],
                    "missing_skills": [],
                    "unknown_requirements": [],
                    "evidence": [],
                    "recommendation": "Revisar.",
                    "explanation": "Resposta sintética.",
                }
            )
        )


def test_apenas_top_10_recebe_chamada_e_analise_persistida(db_session: Session) -> None:
    # Onze vagas empatadas permitem conferir o orçamento mesmo quando todas são elegíveis.
    rows = [
        f"Analista {i},Equipe,Requisitos: Python.,https://example.invalid/funil/{i}"
        for i in range(11)
    ]
    content = ("title,company,description,url\n" + "\n".join(rows)).encode()
    batch = get_job_import_service(db_session).import_csv(
        content=content, filename=None
    )
    ids = get_job_service(db_session).list_batch_ids(batch.id)
    skill = db_session.scalars(
        select(Skill).where(Skill.canonical_name == "Python")
    ).one()
    candidate = Candidate(
        name="Perfil de teste",
        resume_text="Perfil sintético.",
        skills=[CandidateSkill(skill=skill)],
    )
    db_session.add(candidate)
    db_session.flush()
    state = PipelineState(
        run_id=uuid4(),
        candidate_id=candidate.id,
        llm_enabled=True,
        imported=ImportedJobs(batch_id=batch.id, job_ids=ids),
        normalized_ids=ids,
        deduplicated_ids=ids,
        filtered_ids=ids[::-1],
    )
    provider = RecordingProvider()
    cache = LLMCacheService(
        provider,
        sessions=sessionmaker(
            bind=db_session.connection(), join_transaction_mode="create_savepoint"
        ),
    )
    analysis = JobAnalysisService(MatchRepository(db_session), cache)
    match = match_jobs(state, matching=get_matching_service(db_session))
    state = PipelineState.model_validate({**state.model_dump(), **match})
    state = PipelineState.model_validate({**state.model_dump(), **select_jobs(state)})
    result = analyze_jobs(state, analysis=analysis)

    expected = sorted(ids)[:10]
    assert len(ids) == 11
    assert provider.calls == expected
    assert result["analyzed_ids"] == tuple(expected)
    matches = db_session.scalars(
        select(JobMatch).where(JobMatch.candidate_id == candidate.id)
    ).all()
    assert len(matches) == 11
    assert {m.job_id for m in matches if m.llm_analysis is not None} == set(expected)
