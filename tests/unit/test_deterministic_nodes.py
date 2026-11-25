from unittest.mock import create_autospec
from uuid import uuid4

import pytest

from app.models import ImportBatch
from app.orchestration.deterministic import (
    deduplicate_jobs,
    filter_jobs,
    import_jobs,
    normalize_jobs,
)
from app.orchestration.state import ImportedJobs, PipelineState
from app.services.job_import import JobImportService
from app.services.jobs import JobService


@pytest.fixture
def state():
    return PipelineState(run_id=uuid4(), candidate_id=uuid4())


def advance(state, **fields):
    return PipelineState.model_validate({**state.model_dump(), **fields})


def test_import_uses_persisted_batch(state):
    importer = create_autospec(JobImportService, instance=True)
    jobs = create_autospec(JobService, instance=True)
    batch = ImportBatch(id=uuid4())
    importer.import_csv.return_value = batch
    ids = (uuid4(),)
    jobs.list_batch_ids.return_value = ids

    patch = import_jobs(
        state,
        importer=importer,
        jobs=jobs,
        content=b"csv",
        filename="v.csv",
        source="portal",
    )
    assert patch == {"imported": ImportedJobs(batch_id=batch.id, job_ids=ids)}
    importer.import_csv.assert_called_once_with(
        content=b"csv", filename="v.csv", source="portal"
    )
    jobs.list_batch_ids.assert_called_once_with(batch.id)
    assert (
        import_jobs(
            advance(state, **patch), importer=importer, jobs=jobs, content=b"csv"
        )
        == patch
    )
    assert importer.import_csv.call_count == 1


@pytest.mark.parametrize("ids", [(), (uuid4(), uuid4())])
def test_normalize_consumes_only_imported_jobs(state, ids):
    imported = ImportedJobs(batch_id=uuid4(), job_ids=ids)
    assert normalize_jobs(advance(state, imported=imported)) == {"normalized_ids": ids}


def test_deduplicate_delegates_normalized_subset(state):
    ids = (uuid4(), uuid4())
    state = advance(
        state,
        imported=ImportedJobs(batch_id=uuid4(), job_ids=ids),
        normalized_ids=ids[:1],
    )
    jobs = create_autospec(JobService, instance=True)
    jobs.deduplicate_ids.return_value = ()
    assert deduplicate_jobs(state, jobs=jobs) == {"deduplicated_ids": ()}
    jobs.deduplicate_ids.assert_called_once_with(ids[:1])


def test_filter_delegates_survivors_and_query(state):
    ids = (uuid4(), uuid4())
    state = advance(
        state,
        imported=ImportedJobs(batch_id=uuid4(), job_ids=ids),
        normalized_ids=ids,
        deduplicated_ids=ids[1:],
        filters={"source": "portal"},
    )
    jobs = create_autospec(JobService, instance=True)
    jobs.filter_ids.return_value = ids[1:]
    assert filter_jobs(state, jobs=jobs) == {"filtered_ids": ids[1:]}
    jobs.filter_ids.assert_called_once_with(ids[1:], state.filters)


@pytest.mark.parametrize("node", [normalize_jobs, deduplicate_jobs, filter_jobs])
def test_node_requires_previous_stage(state, node):
    kwargs = (
        {}
        if node is normalize_jobs
        else {"jobs": create_autospec(JobService, instance=True)}
    )
    with pytest.raises(ValueError, match="exige"):
        node(state, **kwargs)
