"""Persiste snapshots de matching e consulta o ranking de uma versão."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import contains_eager

from app.models import Job, JobMatch
from app.repositories.base import BaseRepository
from app.schemas.matching import MatchRankingQuery


class MatchRepository(BaseRepository):
    """Consultas e persistência atômica dos resultados de matching."""

    def upsert(self, match: JobMatch) -> JobMatch:
        """Grava a avaliação ou atualiza a linha da mesma chave composta."""
        insert_match = insert(JobMatch).values(
            candidate_id=match.candidate_id,
            job_id=match.job_id,
            scoring_version=match.scoring_version,
            deterministic_score=match.deterministic_score,
            match_score=match.match_score,
            knockout_flags=match.knockout_flags,
            analysis=match.analysis,
        )
        # O banco arbitra recalculações concorrentes e devolve a mesma
        # identidade na atualização, junto com o snapshot completo.
        snapshot = insert_match.excluded
        statement = insert_match.on_conflict_do_update(
            constraint="uq_job_matches_candidate_job_version",
            set_={
                "deterministic_score": snapshot.deterministic_score,
                "match_score": snapshot.match_score,
                "knockout_flags": snapshot.knockout_flags,
                "analysis": snapshot.analysis,
                "updated_at": func.now(),
            },
        ).returning(JobMatch)
        return self._db.scalars(
            statement, execution_options={"populate_existing": True}
        ).one()

    def get(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID, version: str
    ) -> JobMatch | None:
        """Busca um resultado de um candidato, com a vaga associada."""
        stmt = (
            select(JobMatch)
            .join(JobMatch.job)
            .options(contains_eager(JobMatch.job))
            .where(
                JobMatch.candidate_id == candidate_id,
                JobMatch.job_id == job_id,
                JobMatch.scoring_version == version,
            )
        )
        return self._db.scalar(stmt)

    def list_page(
        self, candidate_id: uuid.UUID, version: str, query: MatchRankingQuery
    ) -> list[JobMatch]:
        """Busca a página e uma linha extra para indicar continuidade."""
        stmt = (
            select(JobMatch)
            .join(JobMatch.job)
            .options(contains_eager(JobMatch.job))
            .where(
                JobMatch.candidate_id == candidate_id,
                JobMatch.scoring_version == version,
                Job.is_archived.is_(False),
                Job.duplicate_of_job_id.is_(None),
            )
        )
        if query.min_score is not None:
            stmt = stmt.where(JobMatch.match_score >= query.min_score)
        elif not query.include_unscored:
            stmt = stmt.where(JobMatch.match_score.is_not(None))
        if query.work_mode is not None:
            stmt = stmt.where(Job.work_mode == query.work_mode.value)

        stmt = stmt.order_by(JobMatch.match_score.desc().nulls_last(), JobMatch.job_id)
        return list(self._db.scalars(stmt.offset(query.offset).limit(query.limit + 1)))
