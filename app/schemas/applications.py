"""Contratos de escrita e leitura de candidaturas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict

from app.models.application import ApplicationStatus


def _validate_note(value: str) -> str:
    if "\x00" in value:
        raise ValueError("A observação não pode conter o caractere nulo.")
    return value


Note = Annotated[str, AfterValidator(_validate_note)]


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: uuid.UUID
    notes: Note | None = None


class ApplicationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ApplicationStatus | None = None
    notes: Note | None = None
    transition_note: Note | None = None


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    status: ApplicationStatus
    notes: str | None
    applied_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ApplicationStatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: ApplicationStatus | None
    to_status: ApplicationStatus
    changed_at: datetime
    note: str | None


class ApplicationDetail(ApplicationRead):
    status_history: list[ApplicationStatusHistoryRead]
