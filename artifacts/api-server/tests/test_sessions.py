"""Session lifetime: a session ends at a fixed time and leaves nothing usable behind."""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import text

from stai.auth.sessions import find_session, hash_token, new_session_token

from .conftest import AppFactory, Harness
from .support import cookie_attributes, set_cookie_headers, sign_in

WEEK = 168


def session_count(harness: Harness) -> int:
    with harness.admin.connect() as connection:
        return connection.execute(text("SELECT count(*) FROM auth_sessions")).scalar_one()


def is_signed_in(harness: Harness) -> bool:
    status = harness.client.get("/api/system/status").status_code
    user = harness.client.get("/api/auth/user").json()["user"]
    assert (status == 200) == (user is not None)
    return status == 200


def test_a_session_lasts_one_week_by_default(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)

    harness.clock.advance(hours=WEEK, seconds=-1)
    assert is_signed_in(harness)

    harness.clock.advance(seconds=1)
    assert not is_signed_in(harness)


def test_using_the_app_does_not_extend_the_session(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)

    for _ in range(6):
        harness.clock.advance(hours=24)
        assert is_signed_in(harness)
    harness.clock.advance(hours=24)

    assert not is_signed_in(harness)


def test_an_expired_session_is_removed_when_it_is_next_seen(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)
    harness.clock.advance(hours=WEEK + 1)

    assert harness.client.get("/api/system/status").status_code == 401

    assert session_count(harness) == 0


def test_expired_sessions_are_cleared_at_the_next_sign_in(harness: Harness) -> None:
    for _ in range(3):
        sign_in(harness.new_client(), harness.provider)
    assert session_count(harness) == 3

    harness.clock.advance(hours=WEEK + 1)
    sign_in(harness.client, harness.provider)

    assert session_count(harness) == 1
    assert is_signed_in(harness)


def test_the_lifetime_can_be_shortened(make_harness: AppFactory) -> None:
    harness = make_harness(STAI_SESSION_TTL_HOURS="2")

    response = sign_in(harness.client, harness.provider)

    assert "Max-Age=7200" in cookie_attributes(set_cookie_headers(response)["sid"])
    harness.clock.advance(hours=1, minutes=59)
    assert is_signed_in(harness)
    harness.clock.advance(minutes=2)
    assert not is_signed_in(harness)


def test_an_expired_session_cannot_fetch_a_csrf_token_or_change_anything(
    harness: Harness,
) -> None:
    sign_in(harness.client, harness.provider)
    token = harness.client.get("/api/auth/csrf").json()["csrfToken"]
    harness.clock.advance(hours=WEEK + 1)

    headers = {"X-CSRF-Token": token, "Origin": "https://testserver"}

    assert harness.client.get("/api/auth/csrf").status_code == 401
    assert harness.client.post("/api/audit/verify", headers=headers).status_code == 401


def test_a_clock_set_back_does_not_revive_a_removed_session(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)
    harness.clock.advance(hours=WEEK + 1)
    assert not is_signed_in(harness)

    harness.clock.advance(hours=-(WEEK + 1))

    assert not is_signed_in(harness)


def test_session_tokens_are_long_and_never_repeat() -> None:
    tokens = {new_session_token() for _ in range(200)}

    assert len(tokens) == 200
    assert all(len(token) == 43 for token in tokens)


def test_the_stored_value_is_a_sha256_of_the_token() -> None:
    # Known answer, so the stored form cannot change without this test noticing.
    assert hash_token("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


@pytest.mark.parametrize("token", ["", "x" * 513, "x" * 100_000])
def test_empty_and_oversized_tokens_are_not_looked_up(harness: Harness, token: str) -> None:
    with harness.runtime.database.session() as db:
        assert find_session(db, token, harness.clock()) is None


def test_a_session_at_its_exact_expiry_time_is_already_over(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)
    token = harness.client.cookies.get("sid")
    created = harness.clock()

    with harness.runtime.database.session() as db:
        assert find_session(db, token, created + timedelta(hours=WEEK, microseconds=-1))
    with harness.runtime.database.session() as db:
        assert find_session(db, token, created + timedelta(hours=WEEK)) is None
