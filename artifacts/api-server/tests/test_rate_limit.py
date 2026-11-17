"""Attempt limits on the sign-in routes, and the limiter behind them."""

from __future__ import annotations

import threading

from stai.core.ratelimit import RateLimiter

from .conftest import Harness
from .support import ISSUER, error_code, redirect_target, set_cookie_headers, sign_in


class Seconds:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def with_fake_time(harness: Harness) -> Seconds:
    seconds = Seconds()
    harness.runtime.rate_limiter = RateLimiter(clock=seconds)
    return seconds


def from_address(address: str) -> dict[str, str]:
    return {"X-Forwarded-For": address}


# -- the limiter ------------------------------------------------------------------------------


def test_the_limit_is_exact() -> None:
    limiter = RateLimiter(clock=Seconds())

    results = [limiter.allow("key", limit=3, window_seconds=60) for _ in range(5)]

    assert results == [True, True, True, False, False]


def test_refused_attempts_do_not_extend_the_wait() -> None:
    seconds = Seconds()
    limiter = RateLimiter(clock=seconds)
    for _ in range(3):
        limiter.allow("key", limit=3, window_seconds=60)

    # Hammering while blocked must not push the unblock time further away.
    for _ in range(50):
        seconds.now += 1
        assert not limiter.allow("key", limit=3, window_seconds=60)

    seconds.now = 1000.0 + 60
    assert limiter.allow("key", limit=3, window_seconds=60)


def test_the_window_slides() -> None:
    seconds = Seconds()
    limiter = RateLimiter(clock=seconds)

    assert limiter.allow("key", limit=2, window_seconds=60)
    seconds.now += 30
    assert limiter.allow("key", limit=2, window_seconds=60)
    seconds.now += 29
    assert not limiter.allow("key", limit=2, window_seconds=60)
    seconds.now += 1  # the first attempt is now a full window old
    assert limiter.allow("key", limit=2, window_seconds=60)
    assert not limiter.allow("key", limit=2, window_seconds=60)


def test_keys_are_counted_separately() -> None:
    limiter = RateLimiter(clock=Seconds())

    assert limiter.allow("a", limit=1, window_seconds=60)
    assert limiter.allow("b", limit=1, window_seconds=60)
    assert not limiter.allow("a", limit=1, window_seconds=60)


def test_memory_stays_bounded_under_many_keys() -> None:
    limiter = RateLimiter(max_keys=100, clock=Seconds())

    for index in range(10_000):
        limiter.allow(f"key-{index}", limit=1, window_seconds=60)

    assert len(limiter._hits) == 100


def test_the_count_is_exact_under_concurrent_use() -> None:
    limiter = RateLimiter(clock=Seconds())
    allowed: list[bool] = []
    start = threading.Barrier(16)

    def attempt() -> None:
        start.wait()
        for _ in range(50):
            allowed.append(limiter.allow("key", limit=100, window_seconds=60))

    threads = [threading.Thread(target=attempt) for _ in range(16)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(allowed) == 800
    assert sum(allowed) == 100


# -- the sign-in routes -----------------------------------------------------------------------


def test_login_allows_ten_attempts_a_minute_per_caller(harness: Harness) -> None:
    seconds = with_fake_time(harness)
    client = harness.client

    for _ in range(10):
        assert client.get("/api/login").headers["location"].startswith(f"{ISSUER}/auth?")

    blocked = client.get("/api/login")
    assert redirect_target(blocked) == ("/", {"signin": "rate-limited"})

    seconds.now += 61
    assert client.get("/api/login").headers["location"].startswith(f"{ISSUER}/auth?")


def test_a_blocked_login_does_no_work(harness: Harness) -> None:
    with_fake_time(harness)
    client = harness.client
    for _ in range(10):
        client.get("/api/login")
    calls_before = len(harness.provider.requests)
    client.cookies.clear()

    blocked = client.get("/api/login")

    assert len(harness.provider.requests) == calls_before
    cookies = set_cookie_headers(blocked)
    assert all("Max-Age=0" in value for value in cookies.values())
    assert client.cookies.get("state") is None


def test_one_caller_being_blocked_does_not_block_another(harness: Harness) -> None:
    with_fake_time(harness)
    client = harness.client
    for _ in range(11):
        client.get("/api/login", headers=from_address("203.0.113.1"))

    response = client.get("/api/login", headers=from_address("203.0.113.2"))

    assert response.headers["location"].startswith(f"{ISSUER}/auth?")


def test_many_callers_together_cannot_exceed_the_overall_limit(harness: Harness) -> None:
    """Changing the claimed address on every attempt does not get around the limit."""
    seconds = with_fake_time(harness)
    client = harness.client

    outcomes = [
        client.get("/api/login", headers=from_address(f"203.0.113.{index}")).headers["location"]
        for index in range(40)
    ]

    assert sum(location.startswith(f"{ISSUER}/auth?") for location in outcomes) == 30
    assert all(location == "/?signin=rate-limited" for location in outcomes[30:])

    seconds.now += 61
    assert (
        client.get("/api/login", headers=from_address("203.0.113.200"))
        .headers["location"]
        .startswith(f"{ISSUER}/auth?")
    )


def test_the_callback_has_its_own_limit(harness: Harness) -> None:
    with_fake_time(harness)
    client = harness.client

    for _ in range(10):
        assert redirect_target(client.get("/api/callback?code=x&state=y"))[1] == {
            "signin": "cookies"
        }

    assert redirect_target(client.get("/api/callback?code=x&state=y"))[1] == {
        "signin": "rate-limited"
    }
    # The login limit is counted separately and is still untouched.
    assert client.get("/api/login").headers["location"].startswith(f"{ISSUER}/auth?")


def test_a_blocked_callback_signs_nobody_in(harness: Harness) -> None:
    with_fake_time(harness)
    client = harness.client
    for _ in range(10):
        client.get("/api/callback?code=x&state=y")

    response = sign_in(client, harness.provider)

    assert redirect_target(response)[1] == {"signin": "rate-limited"}
    assert client.cookies.get("sid") is None
    assert harness.provider.calls_to("/token") == []


def test_logout_answers_too_many_requests(harness: Harness) -> None:
    seconds = with_fake_time(harness)
    client = harness.client

    for _ in range(20):
        assert client.get("/api/logout").status_code == 302

    blocked = client.get("/api/logout")
    assert blocked.status_code == 429
    assert error_code(blocked) == "rate_limited"
    assert blocked.headers["retry-after"] == "60"
    assert blocked.headers["cache-control"] == "no-store"

    seconds.now += 61
    assert client.get("/api/logout").status_code == 302


def test_the_limits_do_not_apply_to_the_rest_of_the_app(harness: Harness) -> None:
    with_fake_time(harness)
    client = harness.client
    sign_in(client, harness.provider)

    for _ in range(60):
        assert client.get("/api/auth/user").status_code == 200
        assert client.get("/api/healthz").status_code == 200
