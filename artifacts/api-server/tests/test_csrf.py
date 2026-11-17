"""Requests that change something must come from this app and carry the session's token."""

from __future__ import annotations

import pytest
from fastapi import FastAPI

from stai.auth.csrf import csrf_token_for, csrf_token_matches, request_is_same_origin
from stai.core.config import load_settings

from .conftest import AppFactory, Harness
from .support import APP_HOST, APP_ORIGIN, csrf_headers, error_code, sign_in

CHANGE = "/api/audit/verify"


def signed_in(harness: Harness) -> dict[str, str]:
    sign_in(harness.client, harness.provider)
    return csrf_headers(harness.client)


def assert_refused(response) -> None:
    assert response.status_code == 403
    assert error_code(response) == "csrf_failed"


def test_a_request_from_the_app_with_the_token_is_accepted(harness: Harness) -> None:
    headers = signed_in(harness)

    assert harness.client.post(CHANGE, headers=headers).status_code == 200


def test_the_token_alone_is_not_enough(harness: Harness) -> None:
    headers = signed_in(harness)

    assert_refused(harness.client.post(CHANGE, headers={"X-CSRF-Token": headers["X-CSRF-Token"]}))


def test_the_origin_alone_is_not_enough(harness: Harness) -> None:
    signed_in(harness)

    assert_refused(harness.client.post(CHANGE, headers={"Origin": APP_ORIGIN}))


@pytest.mark.parametrize(
    "origin",
    [
        "https://elsewhere.example",
        "null",
        "",
        "http://testserver",
        "https://testserver.elsewhere.example",
        "https://elsewhere.example/testserver",
        "https://elsewhere.example?testserver",
        "https://testserver@elsewhere.example",
        "https://nottestserver",
        "testserver",
        "//testserver",
        "ftp://testserver",
        "https://",
    ],
)
def test_a_request_from_anywhere_else_is_refused(harness: Harness, origin: str) -> None:
    headers = signed_in(harness)

    assert_refused(harness.client.post(CHANGE, headers={**headers, "Origin": origin}))


def test_a_foreign_origin_is_not_rescued_by_a_friendly_referer(harness: Harness) -> None:
    headers = signed_in(harness)
    headers["Origin"] = "https://elsewhere.example"
    headers["Referer"] = f"{APP_ORIGIN}/status"

    assert_refused(harness.client.post(CHANGE, headers=headers))


def test_the_referer_is_used_when_the_browser_sends_no_origin(harness: Harness) -> None:
    token = signed_in(harness)["X-CSRF-Token"]

    own = {"X-CSRF-Token": token, "Referer": f"{APP_ORIGIN}/status?tab=1"}
    foreign = {"X-CSRF-Token": token, "Referer": "https://elsewhere.example/testserver"}

    assert harness.client.post(CHANGE, headers=own).status_code == 200
    assert_refused(harness.client.post(CHANGE, headers=foreign))


@pytest.mark.parametrize(
    "token",
    ["", "wrong", "0" * 64, "f" * 64, "ünïcödé", "a" * 10_000],
)
def test_a_wrong_token_is_refused(harness: Harness, token: str) -> None:
    signed_in(harness)

    headers = {"Origin": APP_ORIGIN, "X-CSRF-Token": token.encode("utf-8")}

    assert_refused(harness.client.post(CHANGE, headers=headers))


def test_the_session_cookie_itself_is_not_the_token(harness: Harness) -> None:
    signed_in(harness)
    session_token = harness.client.cookies.get("sid")

    headers = {"Origin": APP_ORIGIN, "X-CSRF-Token": session_token}

    assert_refused(harness.client.post(CHANGE, headers=headers))


def test_a_token_from_another_session_is_refused(harness: Harness) -> None:
    signed_in(harness)
    other = harness.new_client()
    sign_in(other, harness.provider)
    other_headers = csrf_headers(other)

    assert_refused(harness.client.post(CHANGE, headers=other_headers))
    assert other.post(CHANGE, headers=other_headers).status_code == 200


def test_the_token_stays_the_same_for_one_session(harness: Harness) -> None:
    first = signed_in(harness)["X-CSRF-Token"]
    second = csrf_headers(harness.client)["X-CSRF-Token"]

    assert first == second
    assert len(first) == 64
    assert first == csrf_token_for(harness.client.cookies.get("sid"))


def test_the_token_stops_working_after_logout(harness: Harness) -> None:
    headers = signed_in(harness)
    harness.client.get("/api/logout")

    # Signed out, the answer is the same as for any other address: log in first.
    assert harness.client.post(CHANGE, headers=headers).status_code == 401


def test_the_token_is_not_handed_out_without_a_session(harness: Harness) -> None:
    response = harness.client.get("/api/auth/csrf")

    assert response.status_code == 401
    assert "csrfToken" not in response.text


def test_the_token_response_is_never_cached(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)

    response = harness.client.get("/api/auth/csrf")

    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_every_changing_method_is_checked(make_harness: AppFactory, method: str) -> None:
    def add_route(app: FastAPI) -> None:
        @app.api_route("/api/thing", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
        def thing() -> dict[str, bool]:
            return {"done": True}

    harness = make_harness(configure=add_route)
    headers = signed_in(harness)

    assert harness.client.get("/api/thing").status_code == 200
    assert_refused(harness.client.request(method, "/api/thing"))
    assert harness.client.request(method, "/api/thing", headers=headers).status_code == 200


def test_a_refused_request_does_not_reach_the_route(make_harness: AppFactory) -> None:
    calls: list[str] = []

    def add_route(app: FastAPI) -> None:
        @app.post("/api/thing")
        def thing() -> dict[str, bool]:
            calls.append("called")
            return {"done": True}

    harness = make_harness(configure=add_route)
    headers = signed_in(harness)

    harness.client.post("/api/thing", headers={"Origin": "https://elsewhere.example"})
    harness.client.post("/api/thing")
    assert calls == []

    harness.client.post("/api/thing", headers=headers)
    assert calls == ["called"]


# -- the two checks on their own --------------------------------------------------------------


def test_token_comparison_handles_any_input() -> None:
    session_token = "session-token"
    good = csrf_token_for(session_token)

    assert csrf_token_matches(session_token, good)
    assert not csrf_token_matches(session_token, None)
    assert not csrf_token_matches(session_token, "")
    assert not csrf_token_matches(session_token, good.upper())
    assert not csrf_token_matches(session_token, good + "0")
    assert not csrf_token_matches(session_token, "\udcff\x00\n")
    assert not csrf_token_matches("another-session", good)


def test_same_origin_check_in_production() -> None:
    settings = load_settings({"STAI_ALLOWED_HOSTS": f"{APP_HOST},stai.example.app"})

    def same(**headers: str) -> bool:
        return request_is_same_origin(headers, settings)

    assert same(origin="https://testserver")
    assert same(origin="https://STAI.example.app")
    assert same(origin="https://testserver:443")
    assert same(referer="https://stai.example.app/status")
    assert not same()
    assert not same(origin="http://testserver")
    assert not same(origin="http://localhost:5173")
    assert not same(origin="https://localhost")
    assert not same(origin="https://elsewhere.example")
    assert not same(origin="https://[::1")


def test_plain_http_is_only_this_machine_and_only_in_development() -> None:
    development = load_settings({"STAI_ENV": "development", "STAI_ALLOWED_HOSTS": APP_HOST})

    def same(origin: str) -> bool:
        return request_is_same_origin({"origin": origin}, development)

    assert same("http://localhost:5173")
    assert same("http://127.0.0.1:8080")
    assert same("https://testserver")
    assert not same("http://testserver")
    assert not same("http://elsewhere.example")
    assert not same("http://localhost.elsewhere.example")
