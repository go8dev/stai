"""The hash chain on its own: what it detects, and what it cannot."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from stai.audit.chain import (
    GENESIS_HASH,
    ChainRecord,
    InvalidAuditPayload,
    canonical_json,
    canonical_timestamp,
    compute_hash,
    record_hash,
    validate_payload,
    verify_chain,
)

START = datetime(2026, 11, 17, 4, 30, 15, 123456, tzinfo=UTC)


def build_chain(count: int, *, start_seq: int = 1, prev_hash: str = GENESIS_HASH):
    records: list[ChainRecord] = []
    for index in range(count):
        seq = start_seq + index
        fields: dict[str, Any] = {
            "seq": seq,
            "occurred_at": START + timedelta(minutes=index),
            "event_type": "test.event",
            "actor_type": "owner",
            "actor_id": "owner-account-0001",
            "correlation_id": f"{seq:032x}",
            "payload": {"index": index, "note": f"record {seq}"},
            "prev_hash": prev_hash,
        }
        record = ChainRecord(**fields, hash=compute_hash(**fields))
        records.append(record)
        prev_hash = record.hash
    return records


def rehash(record: ChainRecord, **changes: Any) -> ChainRecord:
    """Change a record and give it the hash that matches its new content."""
    changed = replace(record, **changes)
    return replace(changed, hash=record_hash(changed))


# -- the hash ---------------------------------------------------------------------------------


def test_the_hash_is_a_sha256_of_a_fixed_canonical_document() -> None:
    """Pins the format. If this changes, every stored record stops verifying."""
    document = (
        '{"actorId":"owner-1","actorType":"owner","correlationId":"abc",'
        '"eventType":"auth.signin","occurredAt":"2026-11-17T04:30:15.123456Z",'
        '"payload":{"a":1,"b":"两"},"prevHash":"' + GENESIS_HASH + '","seq":1}'
    )

    actual = compute_hash(
        seq=1,
        occurred_at=START,
        event_type="auth.signin",
        actor_type="owner",
        actor_id="owner-1",
        correlation_id="abc",
        payload={"b": "两", "a": 1},
        prev_hash=GENESIS_HASH,
    )

    assert actual == hashlib.sha256(document.encode("utf-8")).hexdigest()
    assert len(actual) == 64


@pytest.mark.parametrize(
    "change",
    [
        {"seq": 2},
        {"occurred_at": START + timedelta(microseconds=1)},
        {"event_type": "auth.signout"},
        {"actor_type": "account"},
        {"actor_id": "owner-2"},
        {"actor_id": None},
        {"correlation_id": "abd"},
        {"correlation_id": None},
        {"payload": {"a": 2}},
        {"payload": {"a": 1, "b": None}},
        {"payload": {"a": "1"}},
        {"payload": {}},
        {"prev_hash": "1" + "0" * 63},
    ],
)
def test_every_field_takes_part_in_the_hash(change: dict[str, Any]) -> None:
    fields: dict[str, Any] = {
        "seq": 1,
        "occurred_at": START,
        "event_type": "auth.signin",
        "actor_type": "owner",
        "actor_id": "owner-1",
        "correlation_id": "abc",
        "payload": {"a": 1},
        "prev_hash": GENESIS_HASH,
    }

    assert compute_hash(**{**fields, **change}) != compute_hash(**fields)


def test_the_hash_does_not_depend_on_key_order_or_time_zone() -> None:
    manila = timezone(timedelta(hours=8))
    fields: dict[str, Any] = {
        "seq": 7,
        "event_type": "test.event",
        "actor_type": "owner",
        "actor_id": None,
        "correlation_id": None,
        "prev_hash": GENESIS_HASH,
    }

    in_utc = compute_hash(occurred_at=START, payload={"a": 1, "b": {"x": 1, "y": 2}}, **fields)
    in_manila = compute_hash(
        occurred_at=START.astimezone(manila), payload={"b": {"y": 2, "x": 1}, "a": 1}, **fields
    )

    assert in_utc == in_manila


def test_canonical_json_is_compact_sorted_utf8() -> None:
    assert canonical_json({"b": [1, "é"], "a": None}) == '{"a":null,"b":[1,"é"]}'.encode()


def test_timestamps_are_written_in_utc_with_microseconds() -> None:
    manila = timezone(timedelta(hours=8))

    assert canonical_timestamp(START) == "2026-11-17T04:30:15.123456Z"
    assert canonical_timestamp(START.astimezone(manila)) == "2026-11-17T04:30:15.123456Z"
    assert canonical_timestamp(datetime(2026, 1, 1, tzinfo=UTC)) == "2026-01-01T00:00:00.000000Z"


def test_a_timestamp_without_a_time_zone_is_refused() -> None:
    with pytest.raises(ValueError, match="naive"):
        canonical_timestamp(datetime(2026, 11, 17, 4, 30))  # noqa: DTZ001


# -- what a payload may hold ------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"text": "plain", "empty": "", "none": None, "flag": True, "count": -3},
        {"nested": {"list": [1, "two", None, {"deep": [False]}]}},
        {"big": 10**30, "amount": "1234.56780000"},
        {"unicode": "₱ ñ 两 🙂"},
    ],
)
def test_values_that_survive_storage_unchanged_are_accepted(payload: dict[str, Any]) -> None:
    validate_payload(payload)


@pytest.mark.parametrize(
    ("payload", "problem"),
    [
        ({"price": 1.5}, "floats"),
        ({"nested": {"list": [1, {"price": 0.1}]}}, "floats"),
        ({"price": float("nan")}, "floats"),
        ({"price": Decimal("1.5")}, "Decimal"),
        ({"at": START}, "datetime"),
        ({"raw": b"bytes"}, "bytes"),
        ({"pair": (1, 2)}, "tuple"),
        ({"items": {1, 2}}, "set"),
        ({1: "numeric key"}, "keys must be text"),
        ({"text": "nul\x00inside"}, "NUL"),
        ({"nul\x00key": 1}, "NUL"),
        ({"text": "\udcff"}, "Unicode"),
    ],
)
def test_values_that_cannot_be_hashed_reproducibly_are_refused(
    payload: dict[Any, Any], problem: str
) -> None:
    with pytest.raises(InvalidAuditPayload, match=problem):
        validate_payload(payload)


def test_the_refusal_says_where_the_bad_value_is() -> None:
    with pytest.raises(InvalidAuditPayload, match=r"payload\.order\.legs\[1\]\.price"):
        validate_payload({"order": {"legs": [{"price": "1"}, {"price": 2.5}]}})


# -- verifying a chain ------------------------------------------------------------------------


def test_an_empty_chain_is_intact() -> None:
    result = verify_chain([])

    assert result.ok
    assert result.events_checked == 0
    assert (result.first_seq, result.last_seq, result.head_hash) == (None, None, None)


def test_an_untouched_chain_is_intact() -> None:
    records = build_chain(25)

    result = verify_chain(records)

    assert result.ok
    assert result.first_break is None
    assert result.events_checked == 25
    assert (result.first_seq, result.last_seq) == (1, 25)
    assert result.head_hash == records[-1].hash


@pytest.mark.parametrize(
    "change",
    [
        {"payload": {"index": 9, "note": "edited"}},
        {"event_type": "test.other"},
        {"actor_type": "account"},
        {"actor_id": "someone-else"},
        {"correlation_id": None},
        {"occurred_at": START + timedelta(days=1)},
    ],
)
def test_a_changed_record_is_found(change: dict[str, Any]) -> None:
    records = build_chain(20)
    records[9] = replace(records[9], **change)

    result = verify_chain(records)

    assert not result.ok
    assert result.first_break is not None
    assert (result.first_break.seq, result.first_break.reason) == (10, "hash_mismatch")
    assert result.events_checked == 9
    assert result.last_seq == 9


def test_a_changed_record_with_a_recomputed_hash_breaks_the_next_link() -> None:
    records = build_chain(20)
    records[9] = rehash(records[9], payload={"index": 9, "note": "edited"})

    result = verify_chain(records)

    assert not result.ok
    assert (result.first_break.seq, result.first_break.reason) == (11, "prev_hash_mismatch")


def test_a_removed_record_is_found() -> None:
    records = build_chain(20)
    del records[9]

    result = verify_chain(records)

    assert (result.first_break.seq, result.first_break.reason) == (11, "sequence_gap")
    assert result.events_checked == 9


def test_a_removed_first_record_is_found() -> None:
    records = build_chain(5)[1:]

    result = verify_chain(records)

    assert (result.first_break.seq, result.first_break.reason) == (2, "sequence_gap")
    assert result.events_checked == 0


def test_removed_and_renumbered_records_are_found() -> None:
    """Closing the gap in the numbers does not close the gap in the hashes."""
    records = build_chain(20)
    del records[9]
    records = [replace(record, seq=index + 1) for index, record in enumerate(records)]

    result = verify_chain(records)

    assert (result.first_break.seq, result.first_break.reason) == (10, "prev_hash_mismatch")


def test_swapped_records_are_found() -> None:
    records = build_chain(20)
    records[4], records[5] = records[5], records[4]

    result = verify_chain(records)

    assert (result.first_break.seq, result.first_break.reason) == (6, "sequence_gap")


def test_a_repeated_record_is_found() -> None:
    records = build_chain(5)
    records.insert(2, records[2])

    result = verify_chain(records)

    assert (result.first_break.seq, result.first_break.reason) == (3, "sequence_gap")
    assert result.events_checked == 3


def test_a_chain_that_does_not_start_at_the_beginning_is_found() -> None:
    forged_start = build_chain(5, prev_hash="f" * 64)

    result = verify_chain(forged_start)

    assert (result.first_break.seq, result.first_break.reason) == (1, "prev_hash_mismatch")


def test_content_that_cannot_be_hashed_is_a_break_not_a_crash() -> None:
    records = build_chain(5)
    records[2] = replace(records[2], payload={"amount": float("inf")})

    result = verify_chain(records)

    assert not result.ok
    assert (result.first_break.seq, result.first_break.reason) == (3, "hash_mismatch")
    assert "cannot be hashed" in result.first_break.detail


def test_only_the_first_break_is_reported() -> None:
    records = build_chain(20)
    records[4] = replace(records[4], payload={"edited": True})
    records[14] = replace(records[14], payload={"edited": True})

    result = verify_chain(records)

    assert result.first_break.seq == 5
    assert result.events_checked == 4


def test_a_window_in_the_middle_is_checked_against_its_predecessor() -> None:
    records = build_chain(30)
    window = records[20:]

    intact = verify_chain(window, expected_seq=21, expected_prev_hash=records[19].hash)
    wrong_predecessor = verify_chain(window, expected_seq=21, expected_prev_hash="f" * 64)

    assert intact.ok
    assert (intact.first_seq, intact.last_seq, intact.events_checked) == (21, 30, 10)
    assert wrong_predecessor.first_break.reason == "prev_hash_mismatch"


def test_the_check_reads_records_one_at_a_time() -> None:
    """A long trail is verified as a stream, without holding it all in memory."""
    records = build_chain(50)
    records[9] = replace(records[9], payload={"edited": True})
    consumed: list[int] = []

    def stream():
        for record in records:
            consumed.append(record.seq)
            yield record

    verify_chain(stream())

    assert consumed == list(range(1, 11))


# -- the limits of a hash chain ---------------------------------------------------------------
#
# These two tests record what the chain cannot detect by itself. They are here so the
# limits stay written down and visible; see docs/KNOWN_LIMITATIONS.md.


def test_limit_records_removed_from_the_end_are_not_detected() -> None:
    records = build_chain(20)

    result = verify_chain(records[:15])

    assert result.ok
    assert result.events_checked == 15
    # The only trace is the head hash, which no longer matches a copy noted earlier.
    assert result.head_hash != records[-1].hash


def test_limit_a_full_rewrite_with_recomputed_hashes_is_not_detected() -> None:
    """Someone holding the database credentials can rebuild the chain from any record on."""
    records = build_chain(20)
    rewritten = records[:9]
    prev_hash = records[8].hash
    for record in records[9:]:
        forged = rehash(record, payload={"rewritten": True}, prev_hash=prev_hash)
        rewritten.append(forged)
        prev_hash = forged.hash

    result = verify_chain(rewritten)

    assert result.ok
    assert result.head_hash != records[-1].hash
