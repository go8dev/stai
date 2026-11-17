"""The hash chain: pure functions with no database access.

Each record's hash is the SHA-256 of a canonical JSON document made of the record's own
fields and the hash of the record before it. The first record follows GENESIS_HASH.

Changing a record, removing one from the middle or reordering records breaks the chain
at the first affected record. Removing records from the end leaves a shorter, still valid
chain; see docs/KNOWN_LIMITATIONS.md.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

GENESIS_HASH = "0" * 64

BreakReason = Literal["sequence_gap", "prev_hash_mismatch", "hash_mismatch"]


class InvalidAuditPayload(ValueError):
    """The payload holds a value that cannot be hashed reproducibly."""


@dataclass(frozen=True, slots=True)
class ChainRecord:
    """The fields of one audit record that take part in the chain."""

    seq: int
    occurred_at: datetime
    event_type: str
    actor_type: str
    actor_id: str | None
    correlation_id: str | None
    # A JSON object for every record the application wrote. Typed loosely because a record
    # changed in the database can hold anything, and verification must still handle it.
    payload: Any
    prev_hash: str
    hash: str


@dataclass(frozen=True, slots=True)
class ChainBreak:
    seq: int
    reason: BreakReason
    detail: str


@dataclass(frozen=True, slots=True)
class ChainResult:
    ok: bool
    events_checked: int
    first_seq: int | None
    last_seq: int | None
    head_hash: str | None
    first_break: ChainBreak | None


def validate_payload(value: Any, *, _path: str = "payload") -> None:
    """Allow only values that survive a JSONB round trip unchanged.

    Floats are refused because their text form is not stable; pass decimals as strings.
    """
    if value is None or isinstance(value, bool | int):
        return
    if isinstance(value, str):
        _check_text(value, _path)
        return
    if isinstance(value, float):
        raise InvalidAuditPayload(f"{_path}: floats are not allowed, pass numbers as text")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise InvalidAuditPayload(f"{_path}: keys must be text")
            _check_text(key, f"{_path} key")
            validate_payload(item, _path=f"{_path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_payload(item, _path=f"{_path}[{index}]")
        return
    raise InvalidAuditPayload(f"{_path}: {type(value).__name__} values are not allowed")


def _check_text(value: str, where: str) -> None:
    if "\x00" in value:
        raise InvalidAuditPayload(f"{where}: text contains a NUL character")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise InvalidAuditPayload(f"{where}: text is not valid Unicode") from exc


def canonical_json(value: Any) -> bytes:
    """Deterministic JSON: sorted keys, no spaces, UTF-8."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def canonical_timestamp(value: datetime) -> str:
    """UTC with microseconds, the precision PostgreSQL keeps."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("naive datetime in the audit chain")
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def compute_hash(
    *,
    seq: int,
    occurred_at: datetime,
    event_type: str,
    actor_type: str,
    actor_id: str | None,
    correlation_id: str | None,
    payload: Any,
    prev_hash: str,
) -> str:
    document = {
        "seq": seq,
        "occurredAt": canonical_timestamp(occurred_at),
        "eventType": event_type,
        "actorType": actor_type,
        "actorId": actor_id,
        "correlationId": correlation_id,
        "payload": payload,
        "prevHash": prev_hash,
    }
    return hashlib.sha256(canonical_json(document)).hexdigest()


def record_hash(record: ChainRecord) -> str:
    return compute_hash(
        seq=record.seq,
        occurred_at=record.occurred_at,
        event_type=record.event_type,
        actor_type=record.actor_type,
        actor_id=record.actor_id,
        correlation_id=record.correlation_id,
        payload=record.payload,
        prev_hash=record.prev_hash,
    )


def verify_chain(
    records: Iterable[ChainRecord],
    *,
    expected_seq: int | None = 1,
    expected_prev_hash: str | None = GENESIS_HASH,
) -> ChainResult:
    """Walk records in `seq` order and stop at the first one that does not fit.

    `expected_seq` and `expected_prev_hash` describe what the first record must look like.
    Pass None for either to accept whatever the first record carries, which is how a
    window in the middle of the chain is checked.
    """
    checked = 0
    first_seq: int | None = None
    last_seq: int | None = None
    head_hash: str | None = None

    def broken(seq: int, reason: BreakReason, detail: str) -> ChainResult:
        return ChainResult(
            ok=False,
            events_checked=checked,
            first_seq=first_seq,
            last_seq=last_seq,
            head_hash=head_hash,
            first_break=ChainBreak(seq=seq, reason=reason, detail=detail),
        )

    for record in records:
        if expected_seq is not None and record.seq != expected_seq:
            return broken(
                record.seq,
                "sequence_gap",
                f"Expected record {expected_seq} but found record {record.seq}.",
            )
        if expected_prev_hash is not None and record.prev_hash != expected_prev_hash:
            return broken(
                record.seq,
                "prev_hash_mismatch",
                f"Record {record.seq} does not point at the hash of the record before it.",
            )
        try:
            actual_hash = record_hash(record)
        except (ValueError, TypeError, OverflowError, RecursionError):
            # Content the application could never have written, such as a number too
            # large to represent. It was changed after it was stored.
            return broken(
                record.seq,
                "hash_mismatch",
                f"The content of record {record.seq} cannot be hashed, so it does not "
                "match its stored hash.",
            )
        if actual_hash != record.hash:
            return broken(
                record.seq,
                "hash_mismatch",
                f"The content of record {record.seq} does not match its stored hash.",
            )

        checked += 1
        if first_seq is None:
            first_seq = record.seq
        last_seq = record.seq
        head_hash = record.hash
        expected_seq = record.seq + 1
        expected_prev_hash = record.hash

    return ChainResult(
        ok=True,
        events_checked=checked,
        first_seq=first_seq,
        last_seq=last_seq,
        head_hash=head_hash,
        first_break=None,
    )
