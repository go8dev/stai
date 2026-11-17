"""Writing to and verifying the audit trail."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Text, cast, func, select, text
from sqlalchemy.orm import Session

from stai.audit import guards  # noqa: F401  (registers the append-only guards)
from stai.audit.chain import (
    GENESIS_HASH,
    ChainRecord,
    ChainResult,
    compute_hash,
    validate_payload,
    verify_chain,
)
from stai.core.logging import get_correlation_id
from stai.core.time import as_utc, utcnow
from stai.db.models import AuditEvent

# Arbitrary constant naming the audit chain for pg_advisory_xact_lock.
_CHAIN_LOCK_KEY = 0x5354_4149_0001

TAIL_WINDOW = 50
_BATCH_SIZE = 1000

# Event types written in Phase 1.
EVENT_SIGNIN = "auth.signin"
EVENT_SIGNIN_REFUSED = "auth.signin_refused"
EVENT_SIGNOUT = "auth.signout"


@dataclass(frozen=True, slots=True)
class VerificationReport:
    result: ChainResult
    verified_at: datetime
    duration_ms: float


@dataclass(frozen=True, slots=True)
class TrailSummary:
    event_count: int
    last_event_at: datetime | None
    last_event_type: str | None
    tail: ChainResult


@dataclass(frozen=True, slots=True)
class StoredEvent:
    """One record as it is stored, for display. `payload` is whatever the database holds."""

    seq: int
    occurred_at: datetime
    event_type: str
    actor_type: str
    actor_id: str | None
    correlation_id: str | None
    payload: Any
    hash: str


class UnreadablePayload:
    """A stored payload that cannot be parsed, kept as the text PostgreSQL returned.

    The application never writes one. It can only appear when a record was changed
    directly in the database, for example to a number with more digits than Python parses.
    """

    __slots__ = ("text",)

    def __init__(self, text: str):
        self.text = text


def parse_stored_payload(raw: str) -> Any:
    """Parse a payload read back as text, without letting a strange value raise."""
    try:
        return json.loads(raw)
    except (ValueError, RecursionError):
        return UnreadablePayload(raw)


# Payloads are read as text and parsed here, so that a record someone changed into
# something unparseable is reported as a break at that record instead of failing the read.
_PAYLOAD_TEXT = cast(AuditEvent.payload, Text).label("payload")

_CHAIN_COLUMNS = (
    AuditEvent.seq,
    AuditEvent.occurred_at,
    AuditEvent.event_type,
    AuditEvent.actor_type,
    AuditEvent.actor_id,
    AuditEvent.correlation_id,
    _PAYLOAD_TEXT,
    AuditEvent.prev_hash,
    AuditEvent.hash,
)


def _to_chain_record(row: Any) -> ChainRecord:
    return ChainRecord(
        seq=row.seq,
        occurred_at=row.occurred_at,
        event_type=row.event_type,
        actor_type=row.actor_type,
        actor_id=row.actor_id,
        correlation_id=row.correlation_id,
        payload=parse_stored_payload(row.payload),
        prev_hash=row.prev_hash,
        hash=row.hash,
    )


def append_event(
    session: Session,
    *,
    event_type: str,
    actor_type: str,
    actor_id: str | None = None,
    payload: dict[str, Any] | None = None,
    correlation_id: str | None = None,
    occurred_at: datetime | None = None,
) -> AuditEvent:
    """Add one record to the end of the chain, inside the caller's transaction.

    The record becomes permanent only when the caller commits, so it is saved together
    with the change it describes or not at all. A transaction-level advisory lock makes
    concurrent writers take turns; it is released at commit or rollback.
    """
    body = dict(payload or {})
    validate_payload(body)
    if not event_type or not actor_type:
        raise ValueError("event_type and actor_type are required")

    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _CHAIN_LOCK_KEY})

    last = session.execute(
        select(AuditEvent.seq, AuditEvent.hash).order_by(AuditEvent.seq.desc()).limit(1)
    ).first()
    seq = 1 if last is None else last.seq + 1
    prev_hash = GENESIS_HASH if last is None else last.hash

    moment = as_utc(occurred_at) if occurred_at is not None else utcnow()
    correlation = correlation_id if correlation_id is not None else get_correlation_id()

    record = AuditEvent(
        seq=seq,
        occurred_at=moment,
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        correlation_id=correlation,
        payload=body,
        prev_hash=prev_hash,
        hash=compute_hash(
            seq=seq,
            occurred_at=moment,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            correlation_id=correlation,
            payload=body,
            prev_hash=prev_hash,
        ),
    )
    session.add(record)
    session.flush()
    return record


def _iter_records(session: Session, *, after_seq: int = 0) -> Iterator[ChainRecord]:
    """All records after `after_seq`, in order, read in batches of plain rows."""
    cursor = after_seq
    while True:
        rows = session.execute(
            select(*_CHAIN_COLUMNS)
            .where(AuditEvent.seq > cursor)
            .order_by(AuditEvent.seq)
            .limit(_BATCH_SIZE)
        ).all()
        if not rows:
            return
        for row in rows:
            yield _to_chain_record(row)
        cursor = rows[-1].seq


def verify_trail(session: Session) -> VerificationReport:
    """Recompute the whole chain from the first record and report the first break."""
    started = time.perf_counter()
    result = verify_chain(_iter_records(session))
    return VerificationReport(
        result=result,
        verified_at=utcnow(),
        duration_ms=round((time.perf_counter() - started) * 1000, 1),
    )


def verify_tail(session: Session, window: int = TAIL_WINDOW) -> ChainResult:
    """Check the newest `window` records against each other and their predecessor."""
    rows = session.execute(
        select(*_CHAIN_COLUMNS).order_by(AuditEvent.seq.desc()).limit(window + 1)
    ).all()
    records = [_to_chain_record(row) for row in reversed(rows)]
    if not records:
        return verify_chain([])

    if len(records) <= window:
        # The whole chain fits in the window, so it must start at the first record.
        return verify_chain(records)

    predecessor, tail = records[0], records[1:]
    return verify_chain(tail, expected_seq=predecessor.seq + 1, expected_prev_hash=predecessor.hash)


def summarise(session: Session) -> TrailSummary:
    count = session.execute(select(func.count()).select_from(AuditEvent)).scalar_one()
    last = session.execute(
        select(AuditEvent.occurred_at, AuditEvent.event_type)
        .order_by(AuditEvent.seq.desc())
        .limit(1)
    ).first()
    return TrailSummary(
        event_count=int(count),
        last_event_at=None if last is None else last.occurred_at,
        last_event_type=None if last is None else last.event_type,
        tail=verify_tail(session),
    )


def list_recent(session: Session, limit: int) -> tuple[list[StoredEvent], int]:
    """The newest `limit` records, newest first, and the total number of records.

    Records are shown as stored, whether or not they still fit the chain; `verify_trail`
    is what says if they do.
    """
    rows = session.execute(
        select(*_CHAIN_COLUMNS).order_by(AuditEvent.seq.desc()).limit(limit)
    ).all()
    events: list[StoredEvent] = []
    for row in rows:
        payload = parse_stored_payload(row.payload)
        events.append(
            StoredEvent(
                seq=row.seq,
                occurred_at=row.occurred_at,
                event_type=row.event_type,
                actor_type=row.actor_type,
                actor_id=row.actor_id,
                correlation_id=row.correlation_id,
                payload=payload.text if isinstance(payload, UnreadablePayload) else payload,
                hash=row.hash,
            )
        )
    total = session.execute(select(func.count()).select_from(AuditEvent)).scalar_one()
    return events, int(total)
