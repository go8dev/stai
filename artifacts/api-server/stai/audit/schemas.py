"""API shapes of the audit trail."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from stai.core.schemas import ApiModel


class AuditBreakReason(StrEnum):
    SEQUENCE_GAP = "sequence_gap"
    PREV_HASH_MISMATCH = "prev_hash_mismatch"
    HASH_MISMATCH = "hash_mismatch"


class AuditEvent(ApiModel):
    seq: int
    occurred_at: datetime
    event_type: str
    actor_type: str
    actor_id: str | None
    correlation_id: str | None
    payload: Any = Field(
        description="The payload as stored. An object for every record the application "
        "wrote; anything else means the record was changed in the database."
    )
    hash: str


class AuditEventList(ApiModel):
    events: list[AuditEvent]
    total: int


class AuditBreak(ApiModel):
    seq: int
    reason: AuditBreakReason
    detail: str


class AuditVerification(ApiModel):
    ok: bool
    events_checked: int
    first_seq: int | None
    last_seq: int | None
    head_hash: str | None
    first_break: AuditBreak | None
    verified_at: datetime
    duration_ms: float
