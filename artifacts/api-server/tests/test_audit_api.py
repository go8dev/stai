"""The audit trail over the API: the listing, verification and the status screen."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import text

from stai.audit import service

from .conftest import Harness
from .support import OWNER_ID, csrf_headers, error_code, sign_in

EVENT_KEYS = {
    "seq",
    "occurredAt",
    "eventType",
    "actorType",
    "actorId",
    "correlationId",
    "payload",
    "hash",
}
VERIFICATION_KEYS = {
    "ok",
    "eventsChecked",
    "firstSeq",
    "lastSeq",
    "headHash",
    "firstBreak",
    "verifiedAt",
    "durationMs",
}


@pytest.fixture
def owner(harness: Harness) -> Harness:
    """The app with the owner signed in. Signing in wrote the first audit record."""
    assert sign_in(harness.client, harness.provider).status_code == 302
    return harness


def add_events(harness: Harness, count: int) -> None:
    for index in range(count):
        with harness.runtime.database.session() as session:
            service.append_event(
                session,
                event_type="test.event",
                actor_type="system",
                payload={"index": index},
                correlation_id=f"corr-{index}",
            )


def tamper(harness: Harness, sql: str) -> None:
    with harness.admin.begin() as connection:
        connection.execute(text(sql))


def listing(harness: Harness, **params: Any) -> dict[str, Any]:
    response = harness.client.get("/api/audit/events", params=params or None)
    assert response.status_code == 200, response.text
    return response.json()


def verification(harness: Harness) -> dict[str, Any]:
    response = harness.client.post("/api/audit/verify", headers=csrf_headers(harness.client))
    assert response.status_code == 200, response.text
    return response.json()


# -- GET /api/audit/events --------------------------------------------------------------------


def test_signing_in_is_the_first_record_in_the_listing(owner: Harness) -> None:
    body = listing(owner)

    assert set(body) == {"events", "total"}
    assert body["total"] == 1
    (event,) = body["events"]
    assert set(event) == EVENT_KEYS
    assert event["seq"] == 1
    assert event["eventType"] == "auth.signin"
    assert event["actorType"] == "owner"
    assert event["actorId"] == OWNER_ID
    assert set(event["payload"]) == {"sessionExpiresAt"}
    assert len(event["hash"]) == 64
    assert len(event["correlationId"]) == 32


def test_the_listing_never_shows_the_previous_hash_or_internal_names(owner: Harness) -> None:
    add_events(owner, 3)

    raw = owner.client.get("/api/audit/events").text

    assert "prevHash" not in raw
    assert "prev_hash" not in raw
    assert "occurred_at" not in raw
    assert "event_type" not in raw


def test_the_newest_records_come_first(owner: Harness) -> None:
    add_events(owner, 5)

    body = listing(owner)

    assert body["total"] == 6
    assert [event["seq"] for event in body["events"]] == [6, 5, 4, 3, 2, 1]
    assert body["events"][0]["payload"] == {"index": 4}
    assert body["events"][0]["correlationId"] == "corr-4"
    assert body["events"][-1]["eventType"] == "auth.signin"


def test_twenty_records_are_listed_unless_another_number_is_asked_for(owner: Harness) -> None:
    add_events(owner, 24)

    body = listing(owner)

    assert body["total"] == 25
    assert [event["seq"] for event in body["events"]] == list(range(25, 5, -1))


@pytest.mark.parametrize(("limit", "expected"), [(1, 1), (2, 2), (7, 7), (100, 7), ("0007", 7)])
def test_the_limit_is_honoured(owner: Harness, limit: Any, expected: int) -> None:
    add_events(owner, 6)

    body = listing(owner, limit=limit)

    assert len(body["events"]) == expected
    assert body["total"] == 7
    assert body["events"][0]["seq"] == 7


@pytest.mark.parametrize(
    "limit", ["0", "-1", "101", "1000000", "abc", "1.5", "", " ", "1e2", "0x10", "١٢", "NaN"]
)
def test_a_limit_outside_one_to_one_hundred_is_refused(owner: Harness, limit: str) -> None:
    response = owner.client.get("/api/audit/events", params={"limit": limit})

    assert response.status_code == 422
    assert error_code(response) == "validation_failed"
    body = response.json()
    assert body["message"] == "Some of the values sent are not valid."
    assert body["details"]
    assert body["details"][0]["location"] == ["query", "limit"]
    assert set(body["details"][0]) == {"location", "type", "message"}


def test_a_refused_request_does_not_repeat_what_was_sent(owner: Harness) -> None:
    marker = "value-that-must-not-come-back"

    response = owner.client.get("/api/audit/events", params={"limit": marker})

    assert response.status_code == 422
    assert marker not in response.text


def test_an_unknown_parameter_changes_nothing(owner: Harness) -> None:
    add_events(owner, 2)

    body = listing(owner, offset=1, order="asc", prevHash="yes")

    assert [event["seq"] for event in body["events"]] == [3, 2, 1]


def test_times_in_the_listing_are_utc(owner: Harness) -> None:
    (event,) = listing(owner)["events"]

    moment = datetime.fromisoformat(event["occurredAt"])
    assert moment.utcoffset() == timedelta(0)
    # The sign-in is recorded at the time the app's clock showed.
    assert abs(moment - owner.clock()) < timedelta(seconds=1)


def test_the_listing_is_never_cached(owner: Harness) -> None:
    response = owner.client.get("/api/audit/events")

    assert response.headers["cache-control"] == "no-store"


def test_the_listing_only_reads(owner: Harness) -> None:
    add_events(owner, 3)
    before = listing(owner, limit=100)

    for _ in range(3):
        listing(owner)

    assert listing(owner, limit=100) == before


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_records_cannot_be_written_or_removed_over_the_api(owner: Harness, method: str) -> None:
    add_events(owner, 2)
    headers = csrf_headers(owner.client)

    for path in ("/api/audit/events", "/api/audit/events/1"):
        response = owner.client.request(method, path, headers=headers, json={"seq": 1})
        assert response.status_code in (404, 405), (method, path)

    body = listing(owner)
    assert body["total"] == 3
    assert verification(owner)["ok"] is True


def test_a_changed_record_is_still_listed_as_stored(owner: Harness) -> None:
    add_events(owner, 3)
    tamper(owner, "UPDATE audit_events SET payload = '[1, \"two\"]' WHERE seq = 2")
    tamper(owner, "UPDATE audit_events SET payload = '\"just text\"' WHERE seq = 3")

    events = {event["seq"]: event for event in listing(owner)["events"]}

    assert events[2]["payload"] == [1, "two"]
    assert events[3]["payload"] == "just text"
    assert events[4]["payload"] == {"index": 2}


def test_a_record_python_cannot_parse_does_not_break_the_listing(owner: Harness) -> None:
    add_events(owner, 3)
    tamper(
        owner,
        "UPDATE audit_events SET payload = "
        "('{\"index\": 1' || repeat('0', 6000) || '}')::jsonb WHERE seq = 3",
    )

    events = {event["seq"]: event for event in listing(owner)["events"]}

    assert isinstance(events[3]["payload"], str)
    assert events[3]["payload"].startswith('{"index": 1000')
    assert events[4]["payload"] == {"index": 2}

    result = verification(owner)
    assert result["ok"] is False
    assert result["firstBreak"]["seq"] == 3
    assert result["firstBreak"]["reason"] == "hash_mismatch"


# -- POST /api/audit/verify -------------------------------------------------------------------


def test_verification_reports_an_intact_trail(owner: Harness) -> None:
    add_events(owner, 4)

    result = verification(owner)

    assert set(result) == VERIFICATION_KEYS
    assert result["ok"] is True
    assert result["eventsChecked"] == 5
    assert (result["firstSeq"], result["lastSeq"]) == (1, 5)
    assert result["firstBreak"] is None
    assert result["headHash"] == listing(owner, limit=1)["events"][0]["hash"]
    assert result["durationMs"] >= 0
    assert datetime.fromisoformat(result["verifiedAt"]).utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    ("sql", "seq", "reason", "checked"),
    [
        ("UPDATE audit_events SET payload = '{}' WHERE seq = 3", 3, "hash_mismatch", 2),
        ("UPDATE audit_events SET actor_id = 'x' WHERE seq = 1", 1, "hash_mismatch", 0),
        (
            "UPDATE audit_events SET prev_hash = repeat('b', 64) WHERE seq = 4",
            4,
            "prev_hash_mismatch",
            3,
        ),
        ("DELETE FROM audit_events WHERE seq = 2", 3, "sequence_gap", 1),
    ],
)
def test_verification_reports_the_first_break(
    owner: Harness, sql: str, seq: int, reason: str, checked: int
) -> None:
    add_events(owner, 4)
    tamper(owner, sql)

    result = verification(owner)

    assert result["ok"] is False
    assert result["eventsChecked"] == checked
    assert set(result["firstBreak"]) == {"seq", "reason", "detail"}
    assert result["firstBreak"]["seq"] == seq
    assert result["firstBreak"]["reason"] == reason
    assert str(seq) in result["firstBreak"]["detail"]


def test_verification_adds_no_record_and_can_be_repeated(owner: Harness) -> None:
    add_events(owner, 2)

    first = verification(owner)
    second = verification(owner)

    assert first["headHash"] == second["headHash"]
    assert first["eventsChecked"] == second["eventsChecked"] == 3
    assert listing(owner)["total"] == 3


def test_verification_takes_no_input(owner: Harness) -> None:
    add_events(owner, 2)
    tamper(owner, "UPDATE audit_events SET payload = '{}' WHERE seq = 2")

    response = owner.client.post(
        "/api/audit/verify?ok=true&window=0",
        headers=csrf_headers(owner.client),
        json={"ok": True, "skip": [2], "firstBreak": None},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert response.json()["firstBreak"]["seq"] == 2


def test_verification_is_refused_without_the_csrf_token(owner: Harness) -> None:
    response = owner.client.post("/api/audit/verify")

    assert response.status_code == 403
    assert error_code(response) == "csrf_failed"


def test_verification_does_not_answer_get(owner: Harness) -> None:
    response = owner.client.get("/api/audit/verify")

    assert response.status_code == 405
    assert error_code(response) == "method_not_allowed"


# -- the status screen ------------------------------------------------------------------------


def audit_status(harness: Harness) -> dict[str, Any]:
    response = harness.client.get("/api/system/status")
    assert response.status_code == 200, response.text
    return response.json()


def test_the_status_screen_shows_an_intact_trail(owner: Harness) -> None:
    add_events(owner, 2)

    body = audit_status(owner)

    assert body["audit"] == {
        "status": "ok",
        "eventCount": 3,
        "lastEventAt": body["audit"]["lastEventAt"],
        "lastEventType": "test.event",
        "detail": None,
    }
    assert datetime.fromisoformat(body["audit"]["lastEventAt"]).utcoffset() == timedelta(0)
    assert body["overall"] == "ok"


@pytest.mark.parametrize(
    ("sql", "seq"),
    [
        ("UPDATE audit_events SET payload = '{\"index\": 99}' WHERE seq = 3", 3),
        ("UPDATE audit_events SET event_type = 'auth.signout' WHERE seq = 1", 1),
        ("DELETE FROM audit_events WHERE seq = 2", 3),
        (
            "UPDATE audit_events SET payload = "
            "('{\"index\": 1' || repeat('0', 6000) || '}')::jsonb WHERE seq = 3",
            3,
        ),
    ],
)
def test_the_status_screen_shows_the_trail_down_after_a_change(
    owner: Harness, sql: str, seq: int
) -> None:
    add_events(owner, 3)
    tamper(owner, sql)

    body = audit_status(owner)

    assert body["audit"]["status"] == "down"
    assert body["audit"]["detail"].startswith(f"Integrity check failed at record {seq}: ")
    assert body["audit"]["eventCount"] in (3, 4)
    # A broken trail is not a detail: the whole system is reported down.
    assert body["overall"] == "down"
    # The other checks still report what they found.
    assert body["database"]["status"] == "ok"
    assert body["marketData"]["status"] == "ok"
