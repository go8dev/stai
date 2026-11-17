"""Owner sign-in and sign-out, end to end against a fake identity provider."""

from __future__ import annotations

import base64
import hashlib
from datetime import timedelta
from urllib.parse import parse_qs, unquote, urlsplit

import httpx
import pytest
from sqlalchemy import text
from starlette.testclient import TestClient

from stai.auth.sessions import hash_token

from .conftest import AppFactory, Harness
from .support import (
    APP_ORIGIN,
    CLIENT_ID,
    ISSUER,
    OTHER_ID,
    OWNER_ID,
    begin_login,
    cookie_attributes,
    error_code,
    finish_login,
    redirect_target,
    replace_cookie,
    set_cookie_headers,
    sign_in,
)

FLOW_COOKIES = ("code_verifier", "nonce", "state", "return_to")
UNREACHABLE_DATABASE = "postgresql://nobody:nothing@127.0.0.1:1/none"


def rows(harness: Harness, sql: str) -> list[dict]:
    with harness.admin.connect() as connection:
        return [dict(row) for row in connection.execute(text(sql)).mappings()]


def audit_types(harness: Harness) -> list[str]:
    return [row["event_type"] for row in rows(harness, "SELECT * FROM audit_events ORDER BY seq")]


def assert_not_signed_in(harness: Harness, response: httpx.Response) -> None:
    session_cookie = set_cookie_headers(response).get("sid")
    assert session_cookie is None or "Max-Age=0" in cookie_attributes(session_cookie)
    assert harness.client.cookies.get("sid") is None
    assert rows(harness, "SELECT * FROM auth_sessions") == []
    assert harness.client.get("/api/auth/user").json() == {"user": None}
    assert harness.client.get("/api/system/status").status_code == 401


# -- starting the flow ------------------------------------------------------------------------


def test_login_redirects_to_the_provider_with_pkce_state_and_nonce(client: TestClient) -> None:
    response = client.get("/api/login")

    assert response.status_code == 302
    location = urlsplit(response.headers["location"])
    assert f"{location.scheme}://{location.netloc}{location.path}" == f"{ISSUER}/auth"
    query = {key: values for key, values in parse_qs(location.query).items()}
    assert query["client_id"] == [CLIENT_ID]
    assert query["response_type"] == ["code"]
    assert query["redirect_uri"] == [f"{APP_ORIGIN}/api/callback"]
    assert query["scope"] == ["openid profile"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["prompt"] == ["login consent"]
    for name in ("state", "nonce", "code_challenge"):
        assert len(query[name][0]) >= 43, name
    # No email address and no long-lived token are asked for.
    assert "email" not in query["scope"][0]
    assert "offline_access" not in query["scope"][0]


def test_login_sets_short_lived_protected_flow_cookies(client: TestClient) -> None:
    response = client.get("/api/login")
    cookies = set_cookie_headers(response)

    assert set(cookies) == set(FLOW_COOKIES)
    for name in FLOW_COOKIES:
        assert cookie_attributes(cookies[name]) >= {
            "HttpOnly",
            "Secure",
            "SameSite=lax",
            "Path=/api",
            "Max-Age=600",
        }, name


def test_the_code_challenge_is_the_sha256_of_the_verifier_cookie(client: TestClient) -> None:
    authorization = begin_login(client)

    verifier = client.cookies.get("code_verifier")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    assert authorization["code_challenge"] == expected
    assert verifier not in authorization.values()
    assert authorization["state"] == client.cookies.get("state")
    assert authorization["nonce"] == client.cookies.get("nonce")


def test_every_login_uses_fresh_values(client: TestClient) -> None:
    first = begin_login(client)
    second = begin_login(client)

    for name in ("state", "nonce", "code_challenge"):
        assert first[name] != second[name]


# -- the owner signs in -----------------------------------------------------------------------


def test_the_owner_signs_in_and_gets_a_session(harness: Harness) -> None:
    client = harness.client

    response = sign_in(client, harness.provider, username="owner-name", first_name="Owner")

    assert response.status_code == 302
    assert response.headers["location"] == "/"
    cookies = set_cookie_headers(response)
    assert cookie_attributes(cookies["sid"]) == {
        "HttpOnly",
        "Secure",
        "SameSite=lax",
        "Path=/",
        f"Max-Age={168 * 3600}",
    }
    for name in FLOW_COOKIES:
        assert "Max-Age=0" in cookie_attributes(cookies[name]), name
        assert client.cookies.get(name) is None

    user = client.get("/api/auth/user").json()["user"]
    assert user == {
        "id": OWNER_ID,
        "username": "owner-name",
        "firstName": "Owner",
        "lastName": "User",
        "profileImageUrl": None,
    }
    assert client.get("/api/system/status").status_code == 200


def test_sign_in_stores_only_a_hash_of_the_session_token(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)
    token = harness.client.cookies.get("sid")

    sessions = rows(harness, "SELECT * FROM auth_sessions")

    assert len(token) >= 43
    assert len(sessions) == 1
    assert sessions[0]["token_hash"] == hash_token(token)
    assert sessions[0]["user_id"] == OWNER_ID
    assert sessions[0]["created_at"] == harness.clock()
    assert sessions[0]["expires_at"] == harness.clock() + timedelta(hours=168)
    everything = repr(sessions) + repr(rows(harness, "SELECT * FROM users"))
    everything += repr(rows(harness, "SELECT * FROM audit_events"))
    assert token not in everything


def test_sign_in_keeps_no_provider_token(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)

    stored = repr(rows(harness, "SELECT * FROM auth_sessions"))
    stored += repr(rows(harness, "SELECT * FROM users"))
    stored += repr(rows(harness, "SELECT * FROM audit_events"))

    assert harness.provider.last_id_token is not None
    assert harness.provider.last_id_token not in stored
    assert "access-token" not in stored
    # The columns that exist leave no room for one either.
    columns = rows(
        harness,
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name IN ('users', 'auth_sessions')",
    )
    names = {row["column_name"] for row in columns}
    assert names == {
        "id",
        "username",
        "first_name",
        "last_name",
        "profile_image_url",
        "created_at",
        "updated_at",
        "last_login_at",
        "token_hash",
        "user_id",
        "expires_at",
    }


def test_sign_in_is_recorded_in_the_audit_trail(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)

    events = rows(harness, "SELECT * FROM audit_events ORDER BY seq")

    assert [event["event_type"] for event in events] == ["auth.signin"]
    event = events[0]
    assert event["seq"] == 1
    assert event["actor_type"] == "owner"
    assert event["actor_id"] == OWNER_ID
    assert event["occurred_at"] == harness.clock()
    assert set(event["payload"]) == {"sessionExpiresAt"}
    assert len(event["correlation_id"]) == 32


def test_the_user_record_is_created_once_and_refreshed(harness: Harness) -> None:
    sign_in(harness.client, harness.provider, username="first-name")
    harness.clock.advance(hours=1)
    sign_in(harness.new_client(), harness.provider, username="second-name")

    users = rows(harness, "SELECT * FROM users")

    assert len(users) == 1
    assert users[0]["id"] == OWNER_ID
    assert users[0]["username"] == "second-name"
    assert users[0]["last_login_at"] == harness.clock()
    assert users[0]["updated_at"] == harness.clock()
    assert users[0]["created_at"] < users[0]["updated_at"]
    assert len(rows(harness, "SELECT * FROM auth_sessions")) == 2


@pytest.mark.parametrize(
    ("requested", "expected"),
    [
        ("/status", "/status"),
        ("/modules/journal?tab=notes", "/modules/journal?tab=notes"),
        ("/", "/"),
        ("https://elsewhere.example/", "/"),
        ("//elsewhere.example/", "/"),
        ("/\\elsewhere.example", "/"),
        ("elsewhere.example", "/"),
        ("javascript:alert(1)", "/"),
        ("/api/logout", "/"),
        ("/api", "/"),
        ("/status\r\nSet-Cookie: x=1", "/"),
        ("/" + "a" * 600, "/"),
        ("", "/"),
    ],
)
def test_return_to_only_ever_leads_back_into_the_app(
    harness: Harness, requested: str, expected: str
) -> None:
    authorization = begin_login(harness.client, returnTo=requested)

    response = finish_login(harness.client, harness.provider, authorization)

    assert response.status_code == 302
    assert response.headers["location"] == expected


def test_return_to_cannot_be_changed_through_the_callback(harness: Harness) -> None:
    authorization = begin_login(harness.client, returnTo="/status")

    response = finish_login(
        harness.client,
        harness.provider,
        authorization,
        callback_params={"returnTo": "https://elsewhere.example/"},
    )

    assert response.headers["location"] == "/status"


def test_a_tampered_return_cookie_still_leads_into_the_app(harness: Harness) -> None:
    authorization = begin_login(harness.client)
    replace_cookie(harness.client, "return_to", "https%3A%2F%2Felsewhere.example%2F")

    response = finish_login(harness.client, harness.provider, authorization)

    assert response.headers["location"] == "/"


# -- everyone else is refused -----------------------------------------------------------------


def test_another_account_is_refused_and_shown_its_own_id(harness: Harness) -> None:
    response = sign_in(harness.client, harness.provider, subject=OTHER_ID)

    path, query = redirect_target(response)
    assert path == "/"
    assert query == {"signin": "refused", "account": OTHER_ID}
    assert_not_signed_in(harness, response)
    assert rows(harness, "SELECT * FROM users") == []


def test_a_refused_sign_in_is_recorded_in_the_audit_trail(harness: Harness) -> None:
    sign_in(harness.client, harness.provider, subject=OTHER_ID)

    events = rows(harness, "SELECT * FROM audit_events ORDER BY seq")

    assert [event["event_type"] for event in events] == ["auth.signin_refused"]
    assert events[0]["actor_type"] == "account"
    assert events[0]["actor_id"] == OTHER_ID
    assert events[0]["payload"] == {"reason": "not_owner"}


@pytest.mark.parametrize(
    "subject",
    [
        OWNER_ID + "0",
        OWNER_ID[:-1],
        OWNER_ID.upper(),
        " " + OWNER_ID,
        OWNER_ID + " ",
        "0" + OWNER_ID,
        OWNER_ID + "\x00",
    ],
)
def test_ids_that_merely_resemble_the_owners_are_refused(harness: Harness, subject: str) -> None:
    response = sign_in(harness.client, harness.provider, subject=subject)

    _, query = redirect_target(response)
    assert query["signin"] in {"refused", "failed"}
    assert_not_signed_in(harness, response)


def test_a_refusal_stands_when_it_cannot_be_recorded(make_harness: AppFactory) -> None:
    harness = make_harness(DATABASE_URL=UNREACHABLE_DATABASE)

    response = sign_in(harness.client, harness.provider, subject=OTHER_ID)

    _, query = redirect_target(response)
    assert query == {"signin": "refused", "account": OTHER_ID}
    assert "sid" not in set_cookie_headers(response)


def test_nobody_signs_in_when_no_owner_is_configured(make_harness: AppFactory) -> None:
    harness = make_harness(STAI_OWNER_USER_ID=None)

    response = harness.client.get("/api/login")

    _, query = redirect_target(response)
    assert query == {"signin": "not-configured"}
    assert harness.provider.requests == []


def test_sign_in_is_off_without_a_client_id(make_harness: AppFactory) -> None:
    harness = make_harness(REPL_ID=None)

    for path in ("/api/login", "/api/callback?code=x&state=y"):
        _, query = redirect_target(harness.client.get(path))
        assert query == {"signin": "not-configured"}


# -- responses that do not belong to this browser's sign-in -----------------------------------


def test_a_wrong_state_is_rejected(harness: Harness) -> None:
    authorization = begin_login(harness.client)

    response = finish_login(
        harness.client, harness.provider, authorization, callback_params={"state": "x" * 43}
    )

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert_not_signed_in(harness, response)
    assert harness.provider.calls_to("/token") == []


def test_a_missing_state_is_rejected(harness: Harness) -> None:
    authorization = begin_login(harness.client)

    response = finish_login(
        harness.client, harness.provider, authorization, callback_params={"state": None}
    )

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert_not_signed_in(harness, response)


def test_a_callback_without_the_flow_cookies_is_rejected(harness: Harness) -> None:
    authorization = begin_login(harness.client)
    other_browser = harness.new_client()

    response = finish_login(other_browser, harness.provider, authorization)

    assert redirect_target(response)[1] == {"signin": "cookies"}
    assert "sid" not in set_cookie_headers(response)
    assert harness.provider.calls_to("/token") == []
    assert rows(harness, "SELECT * FROM auth_sessions") == []


def test_a_sign_in_started_in_one_browser_cannot_finish_in_another(harness: Harness) -> None:
    """Someone who starts a sign-in cannot hand its end to another browser."""
    attacker = harness.new_client()
    attacker_flow = begin_login(attacker)
    victim = harness.client
    begin_login(victim)

    response = finish_login(victim, harness.provider, attacker_flow)

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert_not_signed_in(harness, response)


def test_a_changed_verifier_cookie_is_rejected_by_the_provider(harness: Harness) -> None:
    authorization = begin_login(harness.client)
    replace_cookie(harness.client, "code_verifier", "v" * 43)

    response = finish_login(harness.client, harness.provider, authorization)

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert_not_signed_in(harness, response)


def test_an_authorization_code_works_once(harness: Harness) -> None:
    authorization = begin_login(harness.client)
    code = harness.provider.issue_code(
        subject=OWNER_ID,
        nonce=authorization["nonce"],
        code_challenge=authorization["code_challenge"],
        redirect_uri=authorization["redirect_uri"],
    )
    params = {"code": code, "state": authorization["state"], "iss": ISSUER}
    saved = {name: harness.client.cookies.get(name) for name in FLOW_COOKIES}

    first = harness.client.get("/api/callback", params=params)
    assert first.headers["location"] == "/"

    replay = harness.new_client()
    for name, value in saved.items():
        replay.cookies.set(name, value)
    second = replay.get("/api/callback", params=params)

    assert redirect_target(second)[1] == {"signin": "failed"}
    assert "sid" not in set_cookie_headers(second)
    assert len(rows(harness, "SELECT * FROM auth_sessions")) == 1


@pytest.mark.parametrize(
    ("provider_error", "reason"),
    [("access_denied", "cancelled"), ("server_error", "failed"), ("login_required", "failed")],
)
def test_an_error_from_the_provider_ends_the_sign_in(
    harness: Harness, provider_error: str, reason: str
) -> None:
    begin_login(harness.client)

    response = harness.client.get("/api/callback", params={"error": provider_error})

    assert redirect_target(response)[1] == {"signin": reason}
    assert_not_signed_in(harness, response)
    for name in FLOW_COOKIES:
        assert harness.client.cookies.get(name) is None


def test_a_callback_from_another_issuer_is_rejected(harness: Harness) -> None:
    authorization = begin_login(harness.client)

    response = finish_login(
        harness.client,
        harness.provider,
        authorization,
        callback_params={"iss": "https://elsewhere.example/oidc"},
    )

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert_not_signed_in(harness, response)
    assert harness.provider.calls_to("/token") == []


def test_a_callback_without_the_issuer_is_rejected_when_the_provider_sends_one(
    harness: Harness,
) -> None:
    authorization = begin_login(harness.client)

    response = finish_login(
        harness.client, harness.provider, authorization, callback_params={"iss": None}
    )

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert_not_signed_in(harness, response)


def test_a_provider_that_sends_no_issuer_is_still_accepted(harness: Harness) -> None:
    harness.provider.discovery_overrides["authorization_response_iss_parameter_supported"] = False
    authorization = begin_login(harness.client)

    response = finish_login(
        harness.client, harness.provider, authorization, callback_params={"iss": None}
    )

    assert response.headers["location"] == "/"


def test_a_callback_without_a_code_is_rejected(harness: Harness) -> None:
    authorization = begin_login(harness.client)

    response = finish_login(
        harness.client, harness.provider, authorization, callback_params={"code": None}
    )

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert_not_signed_in(harness, response)


def test_a_made_up_code_is_rejected(harness: Harness) -> None:
    authorization = begin_login(harness.client)

    response = finish_login(
        harness.client, harness.provider, authorization, callback_params={"code": "made-up"}
    )

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert_not_signed_in(harness, response)


# -- identity tokens that fail a check --------------------------------------------------------


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"audience": "some-other-app"}, id="wrong-audience"),
        pytest.param({"audience": ["some-other-app", "third-app"]}, id="audience-list-without-us"),
        pytest.param({"issuer": "https://elsewhere.example/oidc"}, id="wrong-issuer"),
        pytest.param({"expires_in": -3600}, id="expired"),
        pytest.param({"issued_offset": 3600}, id="issued-in-the-future"),
        pytest.param({"token_nonce": "n" * 43}, id="wrong-nonce"),
        pytest.param({"drop_claims": ["nonce"]}, id="no-nonce"),
        pytest.param({"drop_claims": ["sub"]}, id="no-subject"),
        pytest.param({"drop_claims": ["exp"]}, id="no-expiry"),
        pytest.param({"drop_claims": ["aud"]}, id="no-audience"),
        pytest.param({"drop_claims": ["iss"]}, id="no-issuer"),
        pytest.param({"drop_claims": ["iat"]}, id="no-issue-time"),
        pytest.param({"wrong_key": True}, id="signed-by-another-key"),
        pytest.param({"kid": "unknown-key"}, id="unknown-key-id"),
        pytest.param({"algorithm": "none"}, id="unsigned"),
        pytest.param({"algorithm": "HS256"}, id="shared-secret-signature"),
        pytest.param({"algorithm": "RS384"}, id="algorithm-not-advertised"),
        pytest.param({"extra_claims": {"azp": "some-other-app"}}, id="wrong-authorized-party"),
        pytest.param(
            {"audience": ["stai-test-client", "some-other-app"]}, id="two-audiences-no-azp"
        ),
        pytest.param({"extra_claims": {"sub": 12345}}, id="subject-not-text"),
        pytest.param({"extra_claims": {"sub": "   "}}, id="blank-subject"),
        pytest.param({"extra_claims": {"sub": "x" * 300}}, id="oversized-subject"),
    ],
)
def test_an_identity_token_that_fails_a_check_signs_nobody_in(
    harness: Harness, overrides: dict
) -> None:
    response = sign_in(harness.client, harness.provider, **overrides)

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert_not_signed_in(harness, response)
    assert rows(harness, "SELECT * FROM users") == []
    assert audit_types(harness) == []


def test_a_token_response_without_an_identity_token_is_rejected(harness: Harness) -> None:
    harness.provider.id_token = lambda issued: ""  # type: ignore[method-assign]

    response = sign_in(harness.client, harness.provider)

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert_not_signed_in(harness, response)


def test_garbage_instead_of_an_identity_token_is_rejected(harness: Harness) -> None:
    harness.provider.id_token = lambda issued: "not.a.token"  # type: ignore[method-assign]

    response = sign_in(harness.client, harness.provider)

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert_not_signed_in(harness, response)


# -- when something the sign-in depends on is down --------------------------------------------


def test_login_fails_cleanly_when_the_provider_is_unreachable(harness: Harness) -> None:
    harness.provider.unreachable = True

    response = harness.client.get("/api/login")

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert set_cookie_headers(response).keys() <= set(FLOW_COOKIES)
    assert harness.client.cookies.get("state") is None


def test_login_fails_cleanly_when_the_provider_answers_with_an_error(harness: Harness) -> None:
    harness.provider.discovery_status = 503

    response = harness.client.get("/api/login")

    assert redirect_target(response)[1] == {"signin": "failed"}


@pytest.mark.parametrize(
    "override",
    [
        {"issuer": "https://elsewhere.example/oidc"},
        {"authorization_endpoint": "http://idp.test/oidc/auth"},
        {"token_endpoint": "ftp://idp.test/oidc/token"},
        {"jwks_uri": None},
        {"id_token_signing_alg_values_supported": ["none", "HS256"]},
    ],
)
def test_login_refuses_provider_settings_it_cannot_trust(harness: Harness, override: dict) -> None:
    harness.provider.discovery_overrides.update(override)

    response = harness.client.get("/api/login")

    assert redirect_target(response)[1] == {"signin": "failed"}


def test_the_callback_fails_cleanly_when_the_token_endpoint_is_down(harness: Harness) -> None:
    authorization = begin_login(harness.client)
    harness.provider.token_status = 502

    response = finish_login(harness.client, harness.provider, authorization)

    assert redirect_target(response)[1] == {"signin": "failed"}
    assert_not_signed_in(harness, response)


def test_the_callback_reports_an_unavailable_database(make_harness: AppFactory) -> None:
    harness = make_harness(DATABASE_URL=UNREACHABLE_DATABASE)

    response = sign_in(harness.client, harness.provider)

    assert redirect_target(response)[1] == {"signin": "unavailable"}
    assert "sid" not in set_cookie_headers(response)
    assert harness.client.cookies.get("sid") is None


# -- which address the sign-in comes back to --------------------------------------------------


@pytest.mark.parametrize("path", ["/api/login", "/api/callback?code=x&state=y"])
def test_sign_in_routes_refuse_a_host_that_is_not_configured(client: TestClient, path: str) -> None:
    response = client.get(path, headers={"Host": "elsewhere.example"})

    assert response.status_code == 400
    assert error_code(response) == "unknown_host"
    assert "elsewhere.example" not in response.text
    assert "location" not in response.headers


def test_a_forwarded_host_that_is_not_configured_is_refused(client: TestClient) -> None:
    response = client.get("/api/login", headers={"X-Forwarded-Host": "elsewhere.example"})

    assert response.status_code == 400
    assert error_code(response) == "unknown_host"


def test_the_callback_address_uses_a_configured_forwarded_host(make_harness: AppFactory) -> None:
    harness = make_harness(REPLIT_DOMAINS="stai.example.app,other.example.app")

    response = harness.client.get(
        "/api/login", headers={"Host": "internal:8080", "X-Forwarded-Host": "STAI.example.app"}
    )

    query = parse_qs(urlsplit(response.headers["location"]).query)
    assert query["redirect_uri"] == ["https://stai.example.app/api/callback"]


def test_the_callback_address_is_always_https(make_harness: AppFactory) -> None:
    harness = make_harness()
    plain = TestClient(harness.app, base_url="http://testserver", follow_redirects=False)

    response = plain.get("/api/login")

    query = parse_qs(urlsplit(response.headers["location"]).query)
    assert query["redirect_uri"] == [f"{APP_ORIGIN}/api/callback"]


# -- signing out ------------------------------------------------------------------------------


def test_logout_ends_the_session_everywhere_it_is_kept(harness: Harness) -> None:
    client = harness.client
    sign_in(client, harness.provider)

    response = client.get("/api/logout")

    assert response.status_code == 302
    location = urlsplit(response.headers["location"])
    assert f"{location.scheme}://{location.netloc}{location.path}" == f"{ISSUER}/session/end"
    assert parse_qs(location.query) == {
        "client_id": [CLIENT_ID],
        "post_logout_redirect_uri": [APP_ORIGIN],
    }
    assert "Max-Age=0" in cookie_attributes(set_cookie_headers(response)["sid"])
    assert client.cookies.get("sid") is None
    assert rows(harness, "SELECT * FROM auth_sessions") == []
    assert client.get("/api/auth/user").json() == {"user": None}
    assert client.get("/api/system/status").status_code == 401


def test_a_copied_session_cookie_is_useless_after_logout(harness: Harness) -> None:
    client = harness.client
    sign_in(client, harness.provider)
    copied = client.cookies.get("sid")
    client.get("/api/logout")

    thief = harness.new_client()
    thief.cookies.set("sid", copied)

    assert thief.get("/api/system/status").status_code == 401
    assert thief.get("/api/auth/user").json() == {"user": None}


def test_logout_is_recorded_in_the_audit_trail(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)
    harness.clock.advance(minutes=5)

    harness.client.get("/api/logout")

    events = rows(harness, "SELECT * FROM audit_events ORDER BY seq")
    assert [event["event_type"] for event in events] == ["auth.signin", "auth.signout"]
    assert events[1]["actor_type"] == "owner"
    assert events[1]["actor_id"] == OWNER_ID
    assert events[1]["occurred_at"] == harness.clock()
    assert events[1]["prev_hash"] == events[0]["hash"]


def test_logout_without_a_session_changes_nothing(harness: Harness) -> None:
    response = harness.client.get("/api/logout")

    assert response.status_code == 302
    assert audit_types(harness) == []


def test_logout_ends_only_the_session_of_that_browser(harness: Harness) -> None:
    laptop, phone = harness.client, harness.new_client()
    sign_in(laptop, harness.provider)
    sign_in(phone, harness.provider)

    laptop.get("/api/logout")

    assert laptop.get("/api/system/status").status_code == 401
    assert phone.get("/api/system/status").status_code == 200
    assert len(rows(harness, "SELECT * FROM auth_sessions")) == 1


def test_another_site_cannot_sign_the_owner_out(harness: Harness) -> None:
    client = harness.client
    sign_in(client, harness.provider)

    response = client.get("/api/logout", headers={"Sec-Fetch-Site": "cross-site"})

    assert response.headers["location"] == "/"
    assert "set-cookie" not in response.headers
    assert client.get("/api/system/status").status_code == 200
    assert audit_types(harness) == ["auth.signin"]


def test_logout_stays_in_the_app_when_the_provider_has_no_sign_out_page(
    harness: Harness,
) -> None:
    harness.provider.discovery_overrides["end_session_endpoint"] = None
    sign_in(harness.client, harness.provider)

    response = harness.client.get("/api/logout")

    assert response.headers["location"] == "/"
    assert rows(harness, "SELECT * FROM auth_sessions") == []


def test_logout_still_clears_the_browser_when_the_provider_is_down(
    make_harness: AppFactory,
) -> None:
    first = make_harness()
    sign_in(first.client, first.provider)
    token = first.client.cookies.get("sid")

    # A freshly started app that has never reached the provider, on the same database.
    first.provider.unreachable = True
    second = make_harness()
    second.client.cookies.set("sid", token)

    response = second.client.get("/api/logout")

    assert response.headers["location"] == "/"
    assert "Max-Age=0" in cookie_attributes(set_cookie_headers(response)["sid"])
    assert rows(second, "SELECT * FROM auth_sessions") == []


def test_logout_says_so_when_the_session_could_not_be_ended(make_harness: AppFactory) -> None:
    harness = make_harness(DATABASE_URL=UNREACHABLE_DATABASE)
    client = harness.new_client()
    client.cookies.set("sid", "A" * 43)

    response = client.get("/api/logout")

    assert redirect_target(response)[1] == {"signin": "signout-failed"}
    assert "Max-Age=0" in cookie_attributes(set_cookie_headers(response)["sid"])


def test_logout_on_an_unknown_host_stays_on_the_app(harness: Harness) -> None:
    sign_in(harness.client, harness.provider)

    response = harness.client.get("/api/logout", headers={"Host": "elsewhere.example"})

    # No redirect is ever built from a host that is not configured.
    assert response.headers["location"] == "/"
    assert "elsewhere.example" not in unquote(response.headers["location"])


# -- the current-user route -------------------------------------------------------------------


def test_current_user_is_empty_when_signed_out(harness: Harness) -> None:
    response = harness.client.get("/api/auth/user")

    assert response.status_code == 200
    assert response.json() == {"user": None}
    assert response.headers["cache-control"] == "no-store"


def test_current_user_reports_an_unavailable_database(make_harness: AppFactory) -> None:
    harness = make_harness(DATABASE_URL=UNREACHABLE_DATABASE)
    client = harness.new_client()
    client.cookies.set("sid", "A" * 43)

    response = client.get("/api/auth/user")

    assert response.status_code == 503
    assert error_code(response) == "database_unavailable"


def test_current_user_never_includes_an_email_address(harness: Harness) -> None:
    sign_in(
        harness.client,
        harness.provider,
        extra_claims={"email": "someone@example.test", "email_verified": True},
    )

    body = harness.client.get("/api/auth/user").text
    stored = repr(rows(harness, "SELECT * FROM users"))
    stored += repr(rows(harness, "SELECT * FROM audit_events"))

    assert "example.test" not in body
    assert "example.test" not in stored
