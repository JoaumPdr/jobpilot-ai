"""Consultas de candidaturas restritas ao candidato da rota."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.application import Application, ApplicationStatusHistory
from app.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository):
    def list_by_candidate(self, candidate_id: uuid.UUID) -> list[Application]:
        stmt = (
            select(Application)
            .where(Application.candidate_id == candidate_id)
            .order_by(Application.created_at.desc(), Application.id.desc())
        )
        return list(self._db.scalars(stmt))

    def get(
        self,
        candidate_id: uuid.UUID,
        application_id: uuid.UUID,
        *,
        lock: bool = False,
    ) -> Application | None:
        stmt = select(Application).where(
            Application.candidate_id == candidate_id, Application.id == application_id
        )
        if lock:
            # Validar após adquirir o lock evita registrar duas transições que
            # partiram do mesmo status em requisições concorrentes.
            stmt = stmt.with_for_update().execution_options(populate_existing=True)
        return self._db.scalar(stmt)

    def get_detail(
        self, candidate_id: uuid.UUID, application_id: uuid.UUID
    ) -> Application | None:
        # Uma consulta lê o status e o histórico no mesmo instante do banco.
        stmt = (
            select(Application)
            .where(
                Application.candidate_id == candidate_id,
                Application.id == application_id,
            )
            .options(joinedload(Application.status_history))
        )
        return self._db.scalars(stmt).unique().one_or_none()

    def add(self, application: Application) -> None:
        self._db.add(application)

    def add_history(self, entry: ApplicationStatusHistory) -> None:
        self._db.add(entry)
