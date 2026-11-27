from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.api.dependencies import (
    get_job_dedup_service,
    get_job_import_service,
    get_job_service,
)
from app.models import Job
from app.orchestration.deterministic import (
    deduplicate_jobs,
    filter_jobs,
    import_jobs,
    normalize_jobs,
)
from app.orchestration.state import PipelineState
from app.schemas.jobs import JobListQuery


def advance(state, patch):
    return PipelineState.model_validate({**state.model_dump(), **patch})


def test_batch_scope_normalization_review_and_pagination(db_session):
    jobs = get_job_service(db_session)
    importer = get_job_import_service(db_session)
    state = PipelineState(
        run_id=uuid4(),
        candidate_id=uuid4(),
        filters=JobListQuery(q="Dados", limit=1, offset=1),
    )
    header = "title,company,description,url\n"
    rows = [
        f"Dados   Python,Empresa,Descrição,https://example.org/jobs/{i}?utm_source=csv\n"
        for i in range(54)
    ]
    content = (
        header
        + "".join(rows)
        + rows[0]
        + ",Empresa,Descrição,https://example.org/invalida\n"
    ).encode()
    state = advance(
        state, import_jobs(state, importer=importer, jobs=jobs, content=content)
    )
    state = advance(state, normalize_jobs(state))
    ids = state.normalized_ids
    assert len(ids) == 54
    first = db_session.get(Job, ids[0])
    assert first.title == "Dados Python"
    assert "utm_source" not in first.canonical_url

    get_job_dedup_service(db_session).confirm_duplicate(ids[0], ids[1])
    jobs.archive(ids[2])
    state = advance(state, deduplicate_jobs(state, jobs=jobs))
    # O fingerprint comum é só uma suspeita. Arquivamento pertence à filtragem.
    assert set(state.deduplicated_ids) == set(ids[1:])

    another_run = PipelineState(run_id=uuid4(), candidate_id=state.candidate_id)
    other = import_jobs(
        another_run,
        importer=importer,
        jobs=jobs,
        content=(header + rows[0].replace("/0?", "/outra?")).encode(),
    )
    outside = db_session.get(Job, other["imported"].job_ids[0])
    outside.created_at = datetime.now(UTC) + timedelta(days=1)
    db_session.flush()
    # As vagas do primeiro lote compartilham created_at. O UUID desempata.
    eligible = sorted(set(ids) - {ids[0], ids[2]}, reverse=True)
    state = advance(state, filter_jobs(state, jobs=jobs))
    assert state.filtered_ids == (eligible[1],)

    # Uma nova importação do mesmo CSV registra um lote próprio e vazio.
    empty = advance(
        another_run,
        import_jobs(another_run, importer=importer, jobs=jobs, content=content),
    )
    assert empty.imported.batch_id != state.imported.batch_id
    assert empty.imported.job_ids == ()
    empty = advance(empty, normalize_jobs(empty))
    empty = advance(empty, deduplicate_jobs(empty, jobs=jobs))
    assert advance(empty, filter_jobs(empty, jobs=jobs)).filtered_ids == ()
