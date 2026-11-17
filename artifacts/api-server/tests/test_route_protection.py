"""Deny by default: signed out, only the health check and the sign-in routes answer."""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.routing import iter_route_contexts
from sqlalchemy import text
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from stai.auth.gate import PUBLIC_PATHS
from stai.auth.sessions import hash_token
from stai.core.openapi import build_openapi

from .conftest import AppFactory, Harness
from .support import APP_ORIGIN, OTHER_ID, OWNER_ID, csrf_headers, error_code, sign_in

EXPECTED_PUBLIC_PATHS = {
    "/api/healthz",
    "/api/login",
    "/api/callback",
    "/api/logout",
    "/api/auth/user",
}

ALL_METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")


def app_routes(app: FastAPI) -> list[tuple[str, str]]:
    """Every (method, path) the application serves."""
    found: list[tuple[str, str]] = []
    for route in iter_route_contexts(app.routes):
        for method in sorted(route.methods or ()):
            found.append((method, route.path))
    return found


def assert_closed(response) -> None:
    assert response.status_code == 401, (response.request.method, response.request.url)
    if response.request.method != "HEAD":
        assert error_code(response) == "not_authenticated"
    assert "set-cookie" not in response.headers


def test_the_public_list_is_exactly_the_health_check_and_the_sign_in_routes() -> None:
    assert set(PUBLIC_PATHS) == EXPECTED_PUBLIC_PATHS


def test_every_other_route_is_closed_to_signed_out_visitors(harness: Harness) -> None:
    routes = app_routes(harness.app)
    protected = [(method, path) for method, path in routes if path not in PUBLIC_PATHS]

    # Guard against the helper finding nothing and the test passing on an empty list.
    assert ("GET", "/api/system/status") in protected
    assert ("POST", "/api/audit/verify") in protected
    assert ("GET", "/api/audit/events") in protected
    assert ("GET", "/api/auth/csrf") in protected

    for method, path in protected:
        assert_closed(harness.client.request(method, path))


def test_protected_routes_are_closed_for_every_method(harness: Harness) -> None:
    protected = {path for _, path in app_routes(harness.app) if path not in PUBLIC_PATHS}

    for path in sorted(protected):
        for method in ALL_METHODS:
            assert_closed(harness.client.request(method, path))


def test_every_route_in_the_contract_is_public_or_closed(harness: Harness) -> None:
    document = build_openapi(harness.app)

    for path, item in document["paths"].items():
        full_path = f"/api{path}"
        for method in item:
            response = harness.client.request(method.upper(), full_path)
            if full_path in PUBLIC_PATHS:
                assert response.status_code != 401, (method, full_path)
            else:
                assert_closed(response)


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/api",
        "/api/",
        "/api/nothing-here",
        "/api/system",
        "/api/system/status/",
        "/api/system/status/extra",
        "/API/SYSTEM/STATUS",
        "/api/healthz/",
        "/api/healthz/../system/status",
        "/api/healthz%2f..%2fsystem%2fstatus",
        "/api//healthz",
        "/api/healthz;x=1",
        "/api/login/",
        "/api/auth/user/",
        "/api/auth",
        "/api/docs",
        "/api/openapi.json",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/.env",
        "/static/app.js",
    ],
)
def test_addresses_that_are_not_listed_are_closed(client: TestClient, path: str) -> None:
    # An address that does not exist answers a signed-out visitor like one that does.
    assert_closed(client.get(path))


def test_a_public_path_in_the_query_string_opens_nothing(client: TestClient) -> None:
    assert_closed(client.get("/api/system/status?next=/api/healthz"))
    assert_closed(client.get("/api/system/status#/api/healthz"))


def test_a_route_added_later_is_closed_without_any_extra_code(make_harness: AppFactory) -> None:
    def add_routes(app: FastAPI) -> None:
        @app.get("/api/added-later")
        def added_later() -> dict[str, str]:
            return {"added": "later"}

        @app.post("/api/added-later")
        def change_something() -> dict[str, str]:
            return {"changed": "yes"}

        @app.get("/outside-the-api")
        def outside() -> dict[str, str]:
            return {"outside": "yes"}

    harness = make_harness(configure=add_routes)
    client = harness.client

    assert_closed(client.get("/api/added-later"))
    assert_closed(client.post("/api/added-later"))
    assert_closed(client.get("/outside-the-api"))

    sign_in(client, harness.provider)

    assert client.get("/api/added-later").json() == {"added": "later"}
    assert client.get("/outside-the-api").json() == {"outside": "yes"}
    # The new state-changing route also gets the CSRF check without asking for it.
    assert error_code(client.post("/api/added-later")) == "csrf_failed"
    assert client.post("/api/added-later", headers=csrf_headers(client)).json() == {
        "changed": "yes"
    }


def test_the_owner_reaches_protected_routes_after_sign_in(harness: Harness) -> None:
    client = harness.client
    sign_in(client, harness.provider)

    assert client.get("/api/system/status").status_code == 200
    assert client.get("/api/audit/events").status_code == 200
    assert client.get("/api/auth/csrf").status_code == 200
    assert client.post("/api/audit/verify", headers=csrf_headers(client)).status_code == 200


def test_signed_in_unknown_addresses_answer_not_found(harness: Harness) -> None:
    client = harness.client
    sign_in(client, harness.provider)

    response = client.get("/api/nothing-here")

    assert response.status_code == 404
    assert error_code(response) == "not_found"


@pytest.mark.parametrize(
    "cookie",
    ["", "x", "not-a-real-session", "A" * 43, "A" * 600, "' OR 1=1 --", "null", "undefined"],
)
def test_a_made_up_session_cookie_opens_nothing(harness: Harness, cookie: str) -> None:
    client = harness.new_client()
    client.cookies.set("sid", cookie)

    assert_closed(client.get("/api/system/status"))


def test_the_stored_hash_cannot_be_used_as_a_session(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)
    with harness.admin.connect() as connection:
        stored = connection.execute(text("SELECT token_hash FROM auth_sessions")).scalar_one()

    thief = harness.new_client()
    thief.cookies.set("sid", stored)

    assert_closed(thief.get("/api/system/status"))


def test_a_session_of_another_account_opens_nothing(harness: Harness) -> None:
    """Even a session row that should never exist does not get a non-owner in."""
    token = "session-token-of-an-account-that-is-not-the-owner"
    now = harness.clock()
    with harness.admin.begin() as connection:
        connection.execute(
            text("INSERT INTO users (id, created_at, updated_at) VALUES (:id, :now, :now)"),
            {"id": OTHER_ID, "now": now},
        )
        connection.execute(
            text(
                "INSERT INTO auth_sessions (token_hash, user_id, created_at, expires_at) "
                "VALUES (:hash, :id, :now, :expires)"
            ),
            {"hash": hash_token(token), "id": OTHER_ID, "now": now, "expires": now + timedelta(1)},
        )

    client = harness.new_client()
    client.cookies.set("sid", token)

    assert_closed(client.get("/api/system/status"))
    assert client.get("/api/auth/user").json() == {"user": None}


def test_changing_the_configured_owner_locks_out_existing_sessions(
    make_harness: AppFactory,
) -> None:
    first = make_harness()
    sign_in(first.client, first.provider)
    token = first.client.cookies.get("sid")
    assert first.client.get("/api/system/status").status_code == 200

    # Same database, different owner in the configuration.
    second = make_harness(STAI_OWNER_USER_ID=OTHER_ID)
    second.client.cookies.set("sid", token)

    assert_closed(second.client.get("/api/system/status"))
    assert second.client.get("/api/auth/user").json() == {"user": None}


def test_no_owner_configured_means_nobody_gets_in(make_harness: AppFactory) -> None:
    first = make_harness()
    sign_in(first.client, first.provider)
    token = first.client.cookies.get("sid")

    second = make_harness(STAI_OWNER_USER_ID=None)
    second.client.cookies.set("sid", token)

    assert_closed(second.client.get("/api/system/status"))


def test_protected_routes_answer_unavailable_when_the_database_is_down(
    make_harness: AppFactory,
) -> None:
    harness = make_harness(DATABASE_URL="postgresql://nobody:nothing@127.0.0.1:1/none")
    client = harness.new_client()
    client.cookies.set("sid", "A" * 43)

    response = client.get("/api/system/status")

    # Closed, and said plainly: never a 500, never let through.
    assert response.status_code == 503
    assert error_code(response) == "database_unavailable"
    assert "127.0.0.1" not in response.text
    assert "nothing" not in response.text


def test_websocket_connections_are_refused(harness: Harness) -> None:
    for path in ("/api/system/status", "/api/healthz", "/ws"):
        with pytest.raises(WebSocketDisconnect) as refused:
            with harness.client.websocket_connect(path):
                pass
        assert refused.value.code == 1008


def test_other_sites_get_no_cross_origin_permission(harness: Harness) -> None:
    client = harness.client
    sign_in(client, harness.provider)
    foreign = {"Origin": "https://elsewhere.example"}

    preflight = client.options(
        "/api/audit/verify", headers={**foreign, "Access-Control-Request-Method": "POST"}
    )
    read = client.get("/api/system/status", headers=foreign)

    for response in (preflight, read):
        assert not [name for name in response.headers if name.startswith("access-control-")]
    assert read.headers["cross-origin-resource-policy"] == "same-origin"


def test_being_signed_in_on_one_browser_opens_nothing_on_another(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)

    assert_closed(harness.new_client().get("/api/system/status"))


def test_the_session_cookie_is_only_read_from_the_cookie_header(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)
    token = harness.client.cookies.get("sid")
    other = harness.new_client()

    assert_closed(other.get("/api/system/status", headers={"Authorization": f"Bearer {token}"}))
    assert_closed(other.get(f"/api/system/status?sid={token}"))
    assert_closed(other.get("/api/system/status", headers={"X-Session": token}))


def test_origin_is_not_needed_for_reading(harness: Harness) -> None:
    client = harness.client
    sign_in(client, harness.provider)

    assert client.get("/api/system/status", headers={"Origin": APP_ORIGIN}).status_code == 200
    assert client.get("/api/system/status").status_code == 200
    assert client.get("/api/auth/user").json()["user"]["id"] == OWNER_ID
