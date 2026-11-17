"""The audit trail in PostgreSQL: appending, the application's guards and verification."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest
from sqlalchemy import Engine, delete, select, text, update
from sqlalchemy.exc import IntegrityError

from stai.audit import service
from stai.audit.__main__ import main as audit_cli
from stai.audit.chain import GENESIS_HASH, ChainResult, InvalidAuditPayload
from stai.audit.guards import AuditImmutableError, statement_violates_append_only
from stai.core import logging as stai_logging
from stai.core.config import known_variable_names
from stai.db.models import AuditEvent
from stai.db.session import Database

from .conftest import API_ROOT, DatabaseFactory, make_settings

# -- helpers ----------------------------------------------------------------------------------


def append(database: Database, count: int = 1, **fields: Any) -> None:
    """Append `count` records the way the application does, one transaction each."""
    for index in range(count):
        with database.session() as session:
            service.append_event(
                session,
                event_type=fields.get("event_type", "test.event"),
                actor_type=fields.get("actor_type", "system"),
                actor_id=fields.get("actor_id", "actor-1"),
                payload=fields.get("payload", {"index": index, "note": "original"}),
                correlation_id=fields.get("correlation_id", f"corr-{index}"),
            )


def verify(database: Database) -> ChainResult:
    with database.session() as session:
        return service.verify_trail(session).result


def tamper(admin: Engine, sql: str) -> None:
    """Change stored records the way someone holding the database credentials could."""
    with admin.begin() as connection:
        connection.execute(text(sql))


def stored(admin: Engine) -> list[Any]:
    with admin.connect() as connection:
        return list(
            connection.execute(
                text(
                    "SELECT seq, occurred_at, event_type, actor_type, actor_id, correlation_id, "
                    "payload, prev_hash, hash FROM audit_events ORDER BY seq"
                )
            )
        )


def break_of(result: ChainResult) -> tuple[int, str]:
    assert not result.ok
    assert result.first_break is not None
    return result.first_break.seq, result.first_break.reason


# -- appending --------------------------------------------------------------------------------


def test_the_first_record_follows_the_genesis_hash(database: Database, admin: Engine) -> None:
    append(database)

    (row,) = stored(admin)
    assert row.seq == 1
    assert row.prev_hash == GENESIS_HASH
    assert len(row.hash) == 64
    assert row.hash != GENESIS_HASH


def test_each_record_points_at_the_one_before(database: Database, admin: Engine) -> None:
    append(database, 6)

    rows = stored(admin)
    assert [row.seq for row in rows] == [1, 2, 3, 4, 5, 6]
    for previous, current in zip(rows, rows[1:], strict=False):
        assert current.prev_hash == previous.hash
    assert len({row.hash for row in rows}) == 6

    result = verify(database)
    assert result.ok
    assert (result.events_checked, result.first_seq, result.last_seq) == (6, 1, 6)
    assert result.head_hash == rows[-1].hash


def test_an_empty_trail_is_intact(database: Database) -> None:
    result = verify(database)

    assert result.ok
    assert result.events_checked == 0
    assert result.head_hash is None


def test_a_record_is_saved_with_its_transaction_or_not_at_all(
    database: Database, admin: Engine
) -> None:
    with pytest.raises(RuntimeError, match="the change failed"), database.session() as session:
        service.append_event(session, event_type="test.event", actor_type="system")
        raise RuntimeError("the change failed")

    assert stored(admin) == []

    # The number that was handed out and rolled back is used again: no gap is left.
    append(database)
    assert [row.seq for row in stored(admin)] == [1]
    assert verify(database).ok


def test_several_records_in_one_transaction(database: Database, admin: Engine) -> None:
    with database.session() as session:
        for index in range(4):
            service.append_event(
                session, event_type="test.event", actor_type="system", payload={"index": index}
            )

    assert [row.seq for row in stored(admin)] == [1, 2, 3, 4]
    assert verify(database).ok


def test_timestamps_are_stored_in_utc_to_the_microsecond(database: Database, admin: Engine) -> None:
    manila = timezone(timedelta(hours=8))
    moment = datetime(2026, 11, 17, 12, 30, 15, 987654, tzinfo=manila)

    with database.session() as session:
        service.append_event(
            session, event_type="test.event", actor_type="system", occurred_at=moment
        )

    (row,) = stored(admin)
    assert row.occurred_at == moment
    assert row.occurred_at.astimezone(UTC) == datetime(2026, 11, 17, 4, 30, 15, 987654, tzinfo=UTC)
    assert verify(database).ok


def test_a_timestamp_without_a_time_zone_is_refused(database: Database, admin: Engine) -> None:
    naive = datetime(2026, 11, 17, 12, 30)  # noqa: DTZ001

    with pytest.raises(ValueError, match="naive"), database.session() as session:
        service.append_event(
            session, event_type="test.event", actor_type="system", occurred_at=naive
        )

    assert stored(admin) == []


@pytest.mark.parametrize(
    "payload",
    [{"price": 101.25}, {"nested": [{"qty": 0.1}]}, {"when": datetime.now(UTC)}, {"raw": b"x"}],
)
def test_a_payload_that_cannot_be_hashed_reproducibly_is_refused(
    database: Database, admin: Engine, payload: dict[str, Any]
) -> None:
    with pytest.raises(InvalidAuditPayload), database.session() as session:
        service.append_event(session, event_type="test.event", actor_type="system", payload=payload)

    assert stored(admin) == []


@pytest.mark.parametrize(("event_type", "actor_type"), [("", "system"), ("test.event", "")])
def test_an_event_needs_a_type_and_an_actor(
    database: Database, event_type: str, actor_type: str
) -> None:
    with pytest.raises(ValueError, match="required"), database.session() as session:
        service.append_event(session, event_type=event_type, actor_type=actor_type)


def test_the_callers_payload_is_copied(database: Database, admin: Engine) -> None:
    payload = {"index": 1}
    with database.session() as session:
        service.append_event(session, event_type="test.event", actor_type="system", payload=payload)
        payload["index"] = 2

    assert stored(admin)[0].payload == {"index": 1}
    assert verify(database).ok


def test_the_request_id_is_recorded_when_none_is_given(database: Database, admin: Engine) -> None:
    stai_logging.set_correlation_id("request-1234")

    with database.session() as session:
        service.append_event(session, event_type="test.event", actor_type="system")

    assert stored(admin)[0].correlation_id == "request-1234"
    assert verify(database).ok


def test_awkward_but_valid_payloads_still_verify(database: Database, admin: Engine) -> None:
    """What PostgreSQL returns hashes the same as what was written."""
    payloads: list[dict[str, Any]] = [
        {},
        {"z": 1, "a": 2, "mm": 3, "B": 4, "": 5},
        {"text": '₱1,234.50 ñ 两 🙂 "quoted" back\\slash \n\t\u2028 </script>'},
        {"amount": "0.10000000", "leading": "000123", "exponent": "1e5"},
        {"big": 10**40, "negative": -(10**40), "zero": 0, "flag": True, "off": False},
        {"nothing": None, "empty_list": [], "empty_object": {}},
        {"deep": {"a": [{"b": [{"c": [1, [2, [3, {"d": None}]]]}]}]}},
        {"spaces": "  padded  ", "unicode_escape": "\\u0041", "control": "\x01\x1f"},
    ]
    for payload in payloads:
        with database.session() as session:
            service.append_event(
                session, event_type="test.event", actor_type="system", payload=payload
            )

    assert [row.payload for row in stored(admin)] == payloads
    result = verify(database)
    assert result.ok
    assert result.events_checked == len(payloads)


# -- the application's own guards -------------------------------------------------------------


def test_a_loaded_record_cannot_be_changed(database: Database, admin: Engine) -> None:
    append(database, 2)
    before = stored(admin)

    with pytest.raises(AuditImmutableError, match="UPDATE"), database.session() as session:
        record = session.get(AuditEvent, 1)
        assert record is not None
        record.payload = {"index": 0, "note": "edited"}

    assert stored(admin) == before


def test_a_loaded_record_cannot_be_deleted(database: Database, admin: Engine) -> None:
    append(database, 2)
    before = stored(admin)

    with pytest.raises(AuditImmutableError, match="DELETE"), database.session() as session:
        session.delete(session.get(AuditEvent, 1))

    assert stored(admin) == before


@pytest.mark.parametrize(
    ("statement", "action"),
    [
        (update(AuditEvent).values(event_type="edited"), "UPDATE"),
        (update(AuditEvent).where(AuditEvent.seq == 1).values(actor_id=None), "UPDATE"),
        (delete(AuditEvent), "DELETE"),
        (delete(AuditEvent).where(AuditEvent.seq == 1), "DELETE"),
    ],
)
def test_bulk_changes_are_refused(
    database: Database, admin: Engine, statement: Any, action: str
) -> None:
    append(database, 2)
    before = stored(admin)

    with pytest.raises(AuditImmutableError, match=action), database.session() as session:
        session.execute(statement)

    assert stored(admin) == before


MODIFYING_SQL = [
    "UPDATE audit_events SET payload = '{}'::jsonb",
    "update audit_events set event_type = 'x' where seq = 1",
    'UPDATE "audit_events" SET actor_id = NULL',
    "UPDATE public.audit_events SET actor_id = NULL",
    'UPDATE "public"."audit_events" SET actor_id = NULL',
    "UPDATE ONLY audit_events SET actor_id = NULL",
    "UPDATE\n\taudit_events\nSET actor_id = NULL",
    "DELETE FROM audit_events",
    "DELETE FROM audit_events WHERE seq = 1",
    "DeLeTe FrOm AUDIT_EVENTS",
    "/* tidy up */ DELETE FROM audit_events",
    "DELETE FROM audit_events -- only the old ones",
    "DELETE/**/FROM/**/audit_events",
    "TRUNCATE audit_events",
    "TRUNCATE TABLE auth_sessions, audit_events",
    "DROP TABLE audit_events",
    "ALTER TABLE audit_events ADD COLUMN note text",
    "ALTER TABLE audit_events RENAME TO audit_events_old",
    "WITH gone AS (DELETE FROM audit_events RETURNING seq) SELECT count(*) FROM gone",
    "INSERT INTO audit_events SELECT * FROM audit_events "
    "ON CONFLICT (seq) DO UPDATE SET payload = '{}'::jsonb",
    "MERGE INTO audit_events a USING (SELECT 1 AS seq) s ON a.seq = s.seq WHEN MATCHED THEN DELETE",
]


@pytest.mark.parametrize("sql", MODIFYING_SQL)
def test_sql_that_changes_the_table_never_reaches_the_database(
    database: Database, admin: Engine, sql: str
) -> None:
    append(database, 2)
    before = stored(admin)

    with pytest.raises(AuditImmutableError), database.engine.begin() as connection:
        connection.execute(text(sql))
    with pytest.raises(AuditImmutableError), database.engine.begin() as connection:
        connection.exec_driver_sql(sql)
    with pytest.raises(AuditImmutableError), database.session() as session:
        session.execute(text(sql))

    assert stored(admin) == before
    assert verify(database).ok


@pytest.mark.parametrize("sql", MODIFYING_SQL)
def test_the_guard_recognises_each_modifying_statement(sql: str) -> None:
    assert statement_violates_append_only(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT seq, hash FROM audit_events ORDER BY seq DESC LIMIT 1",
        "SELECT count(*) FROM audit_events WHERE event_type = 'auth.signin'",
        "INSERT INTO audit_events (seq, event_type) VALUES (1, 'x')",
        "UPDATE users SET updated_at = now()",
        "DELETE FROM auth_sessions WHERE expires_at < now()",
        "TRUNCATE auth_sessions",
        "UPDATE audit_events_archive SET note = 'x'",
        "DELETE FROM my_audit_events",
        "SELECT u.updated_at FROM users u JOIN audit_events a ON a.actor_id = u.id",
        "SELECT * FROM audit_events -- delete the old ones later",
        "SELECT * FROM audit_events /* UPDATE: revisit this query */",
    ],
)
def test_reading_inserting_and_other_tables_are_left_alone(sql: str) -> None:
    assert not statement_violates_append_only(sql)


@pytest.mark.parametrize(
    "sql",
    [
        # Harmless statements that happen to name both. Refusing them costs nothing,
        # because the application has no reason to run either.
        "UPDATE users SET username = 'audit_events'",
        "SELECT * FROM audit_events FOR UPDATE",
    ],
)
def test_the_guard_errs_on_the_side_of_refusing(sql: str) -> None:
    assert statement_violates_append_only(sql)


def test_other_tables_stay_writable_through_the_application(database: Database) -> None:
    now = datetime.now(UTC)
    with database.engine.begin() as connection:
        connection.execute(
            text("INSERT INTO users (id, created_at, updated_at) VALUES ('u1', :now, :now)"),
            {"now": now},
        )
        connection.execute(text("UPDATE users SET username = 'renamed' WHERE id = 'u1'"))
        connection.execute(text("DELETE FROM users WHERE id = 'u1'"))
        assert connection.execute(text("SELECT count(*) FROM audit_events")).scalar_one() == 0


def test_every_engine_the_application_builds_is_guarded(database_url: str, admin: Engine) -> None:
    for _ in range(2):
        other = Database(make_settings(database_url))
        try:
            with pytest.raises(AuditImmutableError), other.engine.begin() as connection:
                connection.execute(text("DELETE FROM audit_events"))
        finally:
            other.dispose()


def test_limit_the_guard_stops_mistakes_not_intent(database: Database, admin: Engine) -> None:
    """The guard reads SQL text. Code written to get around it can, and the chain shows it.

    Recorded here so the limit stays visible; see docs/KNOWN_LIMITATIONS.md.
    """
    append(database, 3)

    with database.engine.begin() as connection:
        connection.exec_driver_sql(
            "DO $$ BEGIN EXECUTE 'DEL' || 'ETE FROM audit_' || 'events WHERE seq = 2'; END $$"
        )

    assert [row.seq for row in stored(admin)] == [1, 3]
    assert break_of(verify(database)) == (3, "sequence_gap")


# -- changes made with the database credentials -----------------------------------------------


AT_FIVE = "WHERE seq = 5"

# (statement, (record reported, reason), intact records before it)
DIRECT_CHANGES: list[tuple[str, tuple[int, str], int]] = [
    (
        f'UPDATE audit_events SET payload = \'{{"index": 4, "note": "edited"}}\' {AT_FIVE}',
        (5, "hash_mismatch"),
        4,
    ),
    (
        f"UPDATE audit_events SET payload = payload || '{{\"extra\": true}}' {AT_FIVE}",
        (5, "hash_mismatch"),
        4,
    ),
    (f"UPDATE audit_events SET payload = payload - 'note' {AT_FIVE}", (5, "hash_mismatch"), 4),
    (
        f'UPDATE audit_events SET payload = \'{{"index": 4.0, "note": "original"}}\' {AT_FIVE}',
        (5, "hash_mismatch"),
        4,
    ),
    (
        f'UPDATE audit_events SET payload = \'{{"index": "4", "note": "original"}}\' {AT_FIVE}',
        (5, "hash_mismatch"),
        4,
    ),
    (f"UPDATE audit_events SET payload = '[1, 2]' {AT_FIVE}", (5, "hash_mismatch"), 4),
    (f"UPDATE audit_events SET payload = 'null' {AT_FIVE}", (5, "hash_mismatch"), 4),
    (f"UPDATE audit_events SET payload = '\"text\"' {AT_FIVE}", (5, "hash_mismatch"), 4),
    (f"UPDATE audit_events SET event_type = 'test.other' {AT_FIVE}", (5, "hash_mismatch"), 4),
    (f"UPDATE audit_events SET actor_type = 'owner' {AT_FIVE}", (5, "hash_mismatch"), 4),
    (f"UPDATE audit_events SET actor_id = 'someone-else' {AT_FIVE}", (5, "hash_mismatch"), 4),
    (f"UPDATE audit_events SET actor_id = NULL {AT_FIVE}", (5, "hash_mismatch"), 4),
    (f"UPDATE audit_events SET correlation_id = NULL {AT_FIVE}", (5, "hash_mismatch"), 4),
    (
        f"UPDATE audit_events SET occurred_at = occurred_at + interval '1 microsecond' {AT_FIVE}",
        (5, "hash_mismatch"),
        4,
    ),
    (
        f"UPDATE audit_events SET occurred_at = occurred_at - interval '1 day' {AT_FIVE}",
        (5, "hash_mismatch"),
        4,
    ),
    (f"UPDATE audit_events SET hash = repeat('a', 64) {AT_FIVE}", (5, "hash_mismatch"), 4),
    (
        f"UPDATE audit_events SET prev_hash = repeat('b', 64) {AT_FIVE}",
        (5, "prev_hash_mismatch"),
        4,
    ),
    ("DELETE FROM audit_events WHERE seq = 5", (6, "sequence_gap"), 4),
    ("DELETE FROM audit_events WHERE seq = 1", (2, "sequence_gap"), 0),
    ("DELETE FROM audit_events WHERE seq IN (3, 4, 5)", (6, "sequence_gap"), 2),
    ("UPDATE audit_events SET seq = 50 WHERE seq = 5", (6, "sequence_gap"), 4),
    ("UPDATE audit_events SET seq = seq + 100", (101, "sequence_gap"), 0),
]


@pytest.mark.parametrize(("sql", "expected", "intact"), DIRECT_CHANGES)
def test_a_change_made_directly_in_the_database_is_found(
    database: Database, admin: Engine, sql: str, expected: tuple[int, str], intact: int
) -> None:
    append(database, 8)
    assert verify(database).ok

    tamper(admin, sql)

    result = verify(database)
    assert break_of(result) == expected
    assert result.events_checked == intact


def test_the_first_record_cannot_be_replaced_unnoticed(database: Database, admin: Engine) -> None:
    append(database, 3)

    tamper(admin, "UPDATE audit_events SET payload = '{}' WHERE seq = 1")

    assert break_of(verify(database)) == (1, "hash_mismatch")


def test_removing_a_record_and_renumbering_the_rest_is_found(
    database: Database, admin: Engine
) -> None:
    append(database, 8)

    tamper(admin, "DELETE FROM audit_events WHERE seq = 5")
    tamper(admin, "UPDATE audit_events SET seq = seq - 1 WHERE seq > 5")

    assert [row.seq for row in stored(admin)] == [1, 2, 3, 4, 5, 6, 7]
    assert break_of(verify(database)) == (5, "prev_hash_mismatch")


def test_a_record_inserted_in_the_middle_is_found(database: Database, admin: Engine) -> None:
    append(database, 4)

    # Make room at 3 in two steps, so the renumbering itself never collides.
    tamper(admin, "UPDATE audit_events SET seq = seq + 100 WHERE seq >= 3")
    tamper(admin, "UPDATE audit_events SET seq = seq - 99 WHERE seq > 100")
    tamper(
        admin,
        "INSERT INTO audit_events "
        "(seq, occurred_at, event_type, actor_type, payload, prev_hash, hash) "
        "SELECT 3, occurred_at, 'test.forged', 'system', '{}', repeat('c', 64), repeat('d', 64) "
        "FROM audit_events WHERE seq = 2",
    )

    assert break_of(verify(database)) == (3, "prev_hash_mismatch")


def test_a_number_python_cannot_parse_is_a_break_not_a_crash(
    database: Database, admin: Engine
) -> None:
    """PostgreSQL stores numbers with thousands of digits; Python refuses to parse them."""
    append(database, 4)

    tamper(
        admin,
        "UPDATE audit_events SET payload = "
        "('{\"index\": 1' || repeat('0', 6000) || '}')::jsonb WHERE seq = 3",
    )

    result = verify(database)
    assert break_of(result) == (3, "hash_mismatch")
    assert "cannot be hashed" in result.first_break.detail
    assert result.events_checked == 2

    with database.session() as session:
        tail = service.verify_tail(session)
        events, total = service.list_recent(session, 10)
    assert break_of(tail) == (3, "hash_mismatch")
    assert total == 4
    # The record is still listed, with the stored text in place of a parsed payload.
    unreadable = next(event for event in events if event.seq == 3)
    assert isinstance(unreadable.payload, str)
    assert len(unreadable.payload) > 6000


def test_a_number_too_large_for_a_float_is_a_break_not_a_crash(
    database: Database, admin: Engine
) -> None:
    append(database, 4)

    tamper(
        admin,
        "UPDATE audit_events SET payload = "
        "('{\"index\": 1' || repeat('0', 400) || '.5}')::jsonb WHERE seq = 3",
    )

    assert break_of(verify(database)) == (3, "hash_mismatch")


def test_deeply_nested_text_is_unreadable_not_fatal() -> None:
    nested = "[" * 200_000 + "]" * 200_000

    parsed = service.parse_stored_payload(nested)

    assert isinstance(parsed, service.UnreadablePayload)
    assert parsed.text == nested
    assert service.parse_stored_payload('{"a": [1, "two", null]}') == {"a": [1, "two", None]}


def test_two_records_cannot_follow_the_same_predecessor(database: Database, admin: Engine) -> None:
    """A fork is refused by the database itself, whoever tries."""
    append(database, 2)

    with pytest.raises(IntegrityError, match="uq_audit_events_prev_hash"):
        tamper(
            admin,
            "INSERT INTO audit_events "
            "(seq, occurred_at, event_type, actor_type, payload, prev_hash, hash) "
            "SELECT 3, occurred_at, 'test.fork', 'system', '{}', prev_hash, repeat('e', 64) "
            "FROM audit_events WHERE seq = 2",
        )


@pytest.mark.parametrize(
    ("values", "constraint"),
    [
        ("0, now(), 'x', 'system', '{}', repeat('1', 64), repeat('2', 64)", "seq_positive"),
        ("-5, now(), 'x', 'system', '{}', repeat('1', 64), repeat('2', 64)", "seq_positive"),
        ("1, now(), 'x', 'system', '{}', repeat('1', 64), repeat('2', 64)", "pk_audit_events"),
        ("9, now(), 'x', 'system', '{}', repeat('1', 64), hash", "uq_audit_events_hash"),
        # A second record claiming to be the first one of the chain.
        ("9, now(), 'x', 'system', '{}', repeat('0', 64), repeat('2', 64)", "prev_hash"),
        ("9, NULL, 'x', 'system', '{}', repeat('1', 64), repeat('2', 64)", "occurred_at"),
        ("9, now(), 'x', 'system', NULL, repeat('1', 64), repeat('2', 64)", "payload"),
    ],
)
def test_the_table_itself_refuses_malformed_records(
    database: Database, admin: Engine, values: str, constraint: str
) -> None:
    append(database, 1)

    with pytest.raises(IntegrityError, match=constraint):
        tamper(
            admin,
            "INSERT INTO audit_events "
            "(seq, occurred_at, event_type, actor_type, payload, prev_hash, hash) "
            f"SELECT {values} FROM audit_events WHERE seq = 1",
        )


def test_limit_records_removed_from_the_end_are_not_detected(
    database: Database, admin: Engine
) -> None:
    """Recorded here so the limit stays visible; see docs/KNOWN_LIMITATIONS.md."""
    append(database, 8)
    head_before = verify(database).head_hash

    tamper(admin, "DELETE FROM audit_events WHERE seq > 5")

    result = verify(database)
    assert result.ok
    assert result.events_checked == 5
    # The head hash is the only trace: it differs from one noted before the removal.
    assert result.head_hash != head_before


# -- writers at the same time -----------------------------------------------------------------


def test_concurrent_writers_produce_one_unbroken_chain(database: Database, admin: Engine) -> None:
    writers, each = 8, 12
    start = threading.Barrier(writers)
    errors: list[BaseException] = []

    def write(writer: int) -> None:
        try:
            start.wait(timeout=30)
            for index in range(each):
                with database.session() as session:
                    service.append_event(
                        session,
                        event_type="test.concurrent",
                        actor_type="system",
                        actor_id=f"writer-{writer}",
                        payload={"writer": writer, "index": index},
                    )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=write, args=(writer,)) for writer in range(writers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=120)

    assert errors == []
    rows = stored(admin)
    assert [row.seq for row in rows] == list(range(1, writers * each + 1))
    assert {(row.payload["writer"], row.payload["index"]) for row in rows} == {
        (writer, index) for writer in range(writers) for index in range(each)
    }
    result = verify(database)
    assert result.ok
    assert result.events_checked == writers * each


def test_a_second_writer_waits_for_the_first_to_finish(database: Database, admin: Engine) -> None:
    first_has_appended = threading.Event()
    let_first_finish = threading.Event()
    second_done = threading.Event()
    errors: list[BaseException] = []

    def first() -> None:
        try:
            with database.session() as session:
                service.append_event(
                    session, event_type="test.first", actor_type="system", payload={}
                )
                first_has_appended.set()
                assert let_first_finish.wait(timeout=30)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    def second() -> None:
        try:
            with database.session() as session:
                service.append_event(
                    session, event_type="test.second", actor_type="system", payload={}
                )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            second_done.set()

    first_thread = threading.Thread(target=first)
    second_thread = threading.Thread(target=second)
    first_thread.start()
    assert first_has_appended.wait(timeout=30)
    second_thread.start()

    # The first writer has not committed, so the second cannot have taken a number yet.
    assert not second_done.wait(timeout=0.5)
    assert stored(admin) == []

    let_first_finish.set()
    first_thread.join(timeout=30)
    second_thread.join(timeout=30)

    assert errors == []
    assert [(row.seq, row.event_type) for row in stored(admin)] == [
        (1, "test.first"),
        (2, "test.second"),
    ]
    assert verify(database).ok


def test_a_writer_that_rolls_back_does_not_block_or_break_the_next(
    database: Database, admin: Engine
) -> None:
    append(database, 2)

    with pytest.raises(RuntimeError), database.session() as session:
        service.append_event(session, event_type="test.abandoned", actor_type="system")
        raise RuntimeError("abandoned")
    append(database, 1, event_type="test.next")

    assert [(row.seq, row.event_type) for row in stored(admin)][-1] == (3, "test.next")
    assert verify(database).ok


# -- the quick check behind the status screen -------------------------------------------------


def test_the_quick_check_covers_a_whole_short_trail(database: Database, admin: Engine) -> None:
    append(database, 5)
    tamper(admin, "DELETE FROM audit_events WHERE seq = 1")

    with database.session() as session:
        tail = service.verify_tail(session, window=10)

    # Short enough to fit the window, so it must begin at the very first record.
    assert break_of(tail) == (2, "sequence_gap")


@pytest.mark.parametrize("count", [4, 5, 6, 12])
def test_the_quick_check_passes_on_an_intact_trail_of_any_length(
    database: Database, count: int
) -> None:
    append(database, count)

    with database.session() as session:
        tail = service.verify_tail(session, window=5)

    assert tail.ok
    assert tail.events_checked == min(count, 5)
    assert tail.last_seq == count


@pytest.mark.parametrize(
    ("sql", "expected"),
    [
        ("UPDATE audit_events SET payload = '{}' WHERE seq = 8", (8, "hash_mismatch")),
        ("UPDATE audit_events SET payload = '{}' WHERE seq = 12", (12, "hash_mismatch")),
        ("DELETE FROM audit_events WHERE seq = 10", (11, "sequence_gap")),
        # Record 7 is the one just before the window: its hash is what record 8 points at.
        ("UPDATE audit_events SET hash = repeat('a', 64) WHERE seq = 7", (8, "prev_hash_mismatch")),
    ],
)
def test_the_quick_check_finds_changes_among_the_newest_records(
    database: Database, admin: Engine, sql: str, expected: tuple[int, str]
) -> None:
    append(database, 12)
    tamper(admin, sql)

    with database.session() as session:
        tail = service.verify_tail(session, window=5)

    assert break_of(tail) == expected


def test_limit_the_quick_check_does_not_see_older_records(
    database: Database, admin: Engine
) -> None:
    """Only the full verification reads every record. Recorded so the limit stays visible."""
    append(database, 12)
    tamper(admin, "UPDATE audit_events SET payload = '{}' WHERE seq = 3")

    with database.session() as session:
        tail = service.verify_tail(session, window=5)

    assert tail.ok
    assert break_of(verify(database)) == (3, "hash_mismatch")


def test_the_status_summary_checks_the_newest_fifty_records(
    database: Database, admin: Engine
) -> None:
    assert service.TAIL_WINDOW == 50
    append(database, 55)

    with database.session() as session:
        intact = service.summarise(session)
    assert intact.event_count == 55
    assert intact.last_event_type == "test.event"
    assert intact.last_event_at is not None
    assert intact.tail.ok
    assert (intact.tail.first_seq, intact.tail.last_seq) == (6, 55)

    tamper(admin, "UPDATE audit_events SET actor_id = 'edited' WHERE seq = 6")
    with database.session() as session:
        assert break_of(service.summarise(session).tail) == (6, "hash_mismatch")


def test_the_summary_of_an_empty_trail(database: Database) -> None:
    with database.session() as session:
        summary = service.summarise(session)

    assert summary.event_count == 0
    assert summary.last_event_at is None
    assert summary.last_event_type is None
    assert summary.tail.ok


def test_a_long_trail_is_read_in_batches(
    database: Database, admin: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(service, "_BATCH_SIZE", 4)
    append(database, 11)

    assert verify(database).events_checked == 11

    tamper(admin, "UPDATE audit_events SET payload = '{}' WHERE seq = 9")
    assert break_of(verify(database)) == (9, "hash_mismatch")


def test_listing_returns_the_newest_records_first(database: Database) -> None:
    append(database, 7)

    with database.session() as session:
        events, total = service.list_recent(session, 3)

    assert total == 7
    assert [event.seq for event in events] == [7, 6, 5]
    assert events[0].payload == {"index": 6, "note": "original"}
    assert events[0].occurred_at.utcoffset() == timedelta(0)


def test_reading_the_trail_issues_no_modifying_statement(database: Database) -> None:
    """Verification and listing only ever read."""
    append(database, 3)
    statements: list[str] = []

    from sqlalchemy import event

    @event.listens_for(database.engine, "before_cursor_execute")
    def record(conn, cursor, statement, parameters, context, executemany) -> None:
        statements.append(statement)

    with database.session() as session:
        service.verify_trail(session)
        service.verify_tail(session)
        service.summarise(session)
        service.list_recent(session, 10)

    assert statements
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in statements)
    with database.session() as session:
        assert session.execute(select(AuditEvent.seq).order_by(AuditEvent.seq)).scalars().all() == [
            1,
            2,
            3,
        ]


# -- python -m stai.audit verify --------------------------------------------------------------


def run_cli(*args: str, **env: str) -> subprocess.CompletedProcess[str]:
    """Run the command in its own process, with only the given STAI settings."""
    import os

    settings = known_variable_names()
    base = {name: value for name, value in os.environ.items() if name not in settings}
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "stai.audit", *args],
        cwd=API_ROOT,
        env={**base, **env},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


@pytest.fixture
def cli_env(monkeypatch: pytest.MonkeyPatch):
    """Run the command in this process with exactly the given settings."""
    for name in known_variable_names():
        monkeypatch.delenv(name, raising=False)

    def run(**env: str) -> int:
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        return audit_cli(["verify"])

    return run


def test_the_command_exits_zero_for_an_intact_trail(
    database: Database, admin: Engine, database_url: str
) -> None:
    append(database, 3)

    completed = run_cli("verify", DATABASE_URL=database_url)

    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["ok"] is True
    assert report["eventsChecked"] == 3
    assert (report["firstSeq"], report["lastSeq"]) == (1, 3)
    assert report["headHash"] == stored(admin)[-1].hash
    assert report["firstBreak"] is None
    assert completed.stderr == ""


def test_the_command_exits_one_when_a_break_is_found(
    database: Database, admin: Engine, database_url: str
) -> None:
    append(database, 5)
    tamper(admin, "UPDATE audit_events SET payload = '{}' WHERE seq = 4")

    completed = run_cli("verify", DATABASE_URL=database_url)

    assert completed.returncode == 1, completed.stderr
    report = json.loads(completed.stdout)
    assert report["ok"] is False
    assert report["eventsChecked"] == 3
    assert report["firstBreak"]["seq"] == 4
    assert report["firstBreak"]["reason"] == "hash_mismatch"


def test_the_command_exits_two_when_it_cannot_run(database_url: str) -> None:
    password = "pw-that-must-not-be-printed"
    unreachable = f"postgresql://nobody:{password}@127.0.0.1:1/nowhere"

    completed = run_cli("verify", DATABASE_URL=unreachable)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr.strip() == "The audit trail could not be read: OperationalError"
    assert password not in completed.stderr
    assert "Traceback" not in completed.stderr


def test_an_unknown_command_exits_two() -> None:
    completed = run_cli("erase")

    assert completed.returncode == 2
    assert completed.stdout == ""


def test_an_empty_trail_counts_as_intact(
    database: Database, cli_env: Any, database_url: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli_env(DATABASE_URL=database_url) == 0

    assert json.loads(capsys.readouterr().out)["eventsChecked"] == 0


@pytest.mark.parametrize(
    ("env", "error"),
    [
        ({}, "DatabaseNotConfigured"),
        ({"DATABASE_URL": "mysql://user@localhost/stai"}, "ValidationError"),
        (
            {"DATABASE_URL": "postgresql://u@127.0.0.1:1/x", "STAI_ENV": "staging"},
            "ValidationError",
        ),
        (
            {
                "DATABASE_URL": "postgresql://u@127.0.0.1:1/x",
                "STAI_ENV": "development",
                "REPLIT_DEPLOYMENT": "1",
            },
            "ConfigurationError",
        ),
    ],
)
def test_settings_the_command_cannot_use_exit_two(
    cli_env: Any, capsys: pytest.CaptureFixture[str], env: dict[str, str], error: str
) -> None:
    assert cli_env(**env) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == f"The audit trail could not be read: {error}"


def test_a_database_without_the_table_exits_two(
    database_factory: DatabaseFactory, cli_env: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    empty = database_factory.create(migrated=False)

    assert cli_env(DATABASE_URL=empty) == 2

    assert capsys.readouterr().err.strip() == "The audit trail could not be read: ProgrammingError"


def test_a_failure_inside_the_check_exits_two_not_one(
    database: Database,
    cli_env: Any,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exit status 1 is reserved for "a break was found". A crash must not look like one."""

    def explode(session: Any) -> None:
        raise ZeroDivisionError("unexpected")

    monkeypatch.setattr("stai.audit.__main__.verify_trail", explode)

    assert cli_env(DATABASE_URL=database_url) == 2

    captured = capsys.readouterr()
    assert captured.err.strip() == "The audit trail could not be read: ZeroDivisionError"
    assert "unexpected" not in captured.err
