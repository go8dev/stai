"""Errors: one shape for every failure, a correlation ID on every response, nothing internal."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError
from starlette.testclient import TestClient

from stai.core.errors import ApiError, ErrorResponse
from stai.core.middleware import CORRELATION_HEADER

from .conftest import AppFactory, Harness, LogCapture
from .support import csrf_headers, sign_in

INTERNAL = "internal-detail-that-must-stay-inside"
SENT = "value-sent-by-the-caller-0001"
HEX32 = re.compile(r"^[0-9a-f]{32}$")

SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
    "cross-origin-resource-policy": "same-origin",
    "x-robots-tag": "noindex, nofollow",
}
HSTS = "max-age=31536000"


class Echo(BaseModel):
    name: str
    amount: int


def add_failing_routes(app: FastAPI) -> None:
    @app.get("/api/test/boom")
    def boom() -> None:
        raise RuntimeError(f"boom {INTERNAL}")

    @app.get("/api/test/async-boom")
    async def async_boom() -> None:
        raise KeyError(INTERNAL)

    @app.get("/api/test/http/{status}")
    def http_error(status: int) -> None:
        raise HTTPException(
            status,
            detail=f"detail {INTERNAL}",
            headers={"X-Internal": INTERNAL, "Retry-After": "7", "Allow": "GET"},
        )

    @app.get("/api/test/api-error")
    def api_error() -> None:
        raise ApiError(
            409,
            "example_conflict",
            "Shown to people.",
            details=[{"field": "amount"}],
            headers={"X-Example": "yes"},
        )

    @app.get("/api/test/database")
    def database_error() -> None:
        raise OperationalError("SELECT 1", {}, Exception(f"connection failed {INTERNAL}"))

    @app.post("/api/test/echo")
    def echo(body: Echo) -> dict[str, bool]:
        return {"ok": True}


@pytest.fixture
def signed_in(make_harness: AppFactory) -> Harness:
    harness = make_harness(configure=add_failing_routes)
    sign_in(harness.client, harness.provider)
    return harness


def envelope(response: httpx.Response, status: int, code: str) -> dict[str, Any]:
    """Check the parts every error response shares and return its body."""
    assert response.status_code == status, response.text
    assert response.headers["content-type"] == "application/json"
    body = response.json()
    assert set(body) in ({"error", "message", "correlationId"}, {*body, "details"})
    assert set(body) <= {"error", "message", "correlationId", "details"}
    assert body["error"] == code
    assert isinstance(body["message"], str)
    assert body["message"]
    assert HEX32.match(body["correlationId"])
    assert body["correlationId"] == response.headers[CORRELATION_HEADER]
    assert response.headers["cache-control"] == "no-store"
    assert INTERNAL not in response.text
    assert INTERNAL not in json.dumps(dict(response.headers))
    # The documented shape accepts it.
    ErrorResponse.model_validate(body)
    return body


def log_entries(logs: LogCapture) -> list[dict[str, Any]]:
    return [json.loads(line) for line in logs.lines]


# -- the usual failures -----------------------------------------------------------------------


def test_an_unknown_address_answers_not_found(signed_in: Harness) -> None:
    body = envelope(signed_in.client.get("/api/nothing-here"), 404, "not_found")

    assert body["message"] == "There is nothing at this address."
    assert "details" not in body


def test_a_wrong_method_answers_method_not_allowed(signed_in: Harness) -> None:
    client = signed_in.client

    response = client.put("/api/audit/events", headers=csrf_headers(client))

    body = envelope(response, 405, "method_not_allowed")
    assert body["message"] == "This address does not accept that kind of request."
    assert response.headers["allow"] == "GET"


def test_a_wrong_method_on_a_public_address_gets_the_same_shape(client: TestClient) -> None:
    response = client.delete("/api/healthz")

    envelope(response, 405, "method_not_allowed")
    assert response.headers["allow"] == "GET"


@pytest.mark.parametrize(
    ("value", "kind"),
    [(SENT, "int_parsing"), ("0", "greater_than_equal"), ("101", "less_than_equal")],
)
def test_an_invalid_value_says_where_and_why_without_repeating_it(
    signed_in: Harness, value: str, kind: str
) -> None:
    response = signed_in.client.get("/api/audit/events", params={"limit": value})

    body = envelope(response, 422, "validation_failed")
    assert body["message"] == "Some of the values sent are not valid."
    (detail,) = body["details"]
    assert set(detail) == {"location", "type", "message"}
    assert detail["location"] == ["query", "limit"]
    assert detail["type"] == kind
    assert SENT not in response.text


def test_an_invalid_body_is_not_repeated_either(signed_in: Harness) -> None:
    client = signed_in.client

    response = client.post(
        "/api/test/echo",
        json={"name": {"nested": SENT}, "amount": SENT, "extra": SENT},
        headers=csrf_headers(client),
    )

    body = envelope(response, 422, "validation_failed")
    assert [detail["location"] for detail in body["details"]] == [
        ["body", "name"],
        ["body", "amount"],
    ]
    for detail in body["details"]:
        assert set(detail) == {"location", "type", "message"}
    assert SENT not in response.text


def test_a_body_that_is_not_json_is_refused_without_repeating_it(signed_in: Harness) -> None:
    client = signed_in.client

    response = client.post(
        "/api/test/echo",
        content=f'{{"name": "{SENT}", "amount": '.encode(),
        headers={**csrf_headers(client), "Content-Type": "application/json"},
    )

    body = envelope(response, 422, "validation_failed")
    assert [detail["type"] for detail in body["details"]] == ["json_invalid"]
    assert SENT not in response.text


def test_a_missing_body_is_reported_as_missing(signed_in: Harness) -> None:
    client = signed_in.client

    response = client.post("/api/test/echo", headers=csrf_headers(client))

    body = envelope(response, 422, "validation_failed")
    assert body["details"] == [
        {"location": ["body"], "type": "missing", "message": "Field required"}
    ]


# -- failures nobody planned for --------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "exception"),
    [("/api/test/boom", "RuntimeError"), ("/api/test/async-boom", "KeyError")],
)
def test_an_unexpected_error_answers_500_and_keeps_the_details_in_the_log(
    signed_in: Harness, json_logs: LogCapture, path: str, exception: str
) -> None:
    response = signed_in.client.get(path)

    body = envelope(response, 500, "internal_error")
    assert body == {
        "error": "internal_error",
        "message": "Something went wrong on the server.",
        "correlationId": response.headers[CORRELATION_HEADER],
    }
    (entry,) = [e for e in log_entries(json_logs) if e["msg"] == "Unhandled error"]
    assert entry["level"] == "error"
    assert entry["correlationId"] == body["correlationId"]
    assert entry["method"] == "GET"
    assert entry["path"] == path
    assert entry["excType"] == exception
    # The owner can find the cause in the log; the visitor cannot see it.
    assert INTERNAL in entry["exc"]
    assert "Traceback (most recent call last)" in entry["traceback"]
    assert "test_errors.py" in entry["traceback"]


def test_the_app_keeps_answering_after_an_unexpected_error(signed_in: Harness) -> None:
    client = signed_in.client

    assert client.get("/api/test/boom").status_code == 500
    assert client.get("/api/test/boom").status_code == 500

    assert client.get("/api/healthz").json() == {"status": "ok"}
    assert client.get("/api/system/status").status_code == 200


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (400, "bad_request"),
        (401, "not_authenticated"),
        (403, "forbidden"),
        (404, "not_found"),
        (405, "method_not_allowed"),
        (413, "payload_too_large"),
        (429, "rate_limited"),
        (409, "request_failed"),
        (418, "request_failed"),
        (500, "internal_error"),
        (502, "internal_error"),
        (503, "internal_error"),
    ],
)
def test_an_error_raised_with_a_status_never_passes_its_own_text_on(
    signed_in: Harness, status: int, code: str
) -> None:
    response = signed_in.client.get(f"/api/test/http/{status}")

    body = envelope(response, status, code)
    assert "details" not in body
    assert "detail" not in body
    # Headers that describe the protocol are kept; anything else is dropped.
    assert response.headers["retry-after"] == "7"
    assert response.headers["allow"] == "GET"
    assert "x-internal" not in response.headers


def test_an_application_error_carries_its_code_message_details_and_headers(
    signed_in: Harness,
) -> None:
    response = signed_in.client.get("/api/test/api-error")

    body = envelope(response, 409, "example_conflict")
    assert body["message"] == "Shown to people."
    assert body["details"] == [{"field": "amount"}]
    assert response.headers["x-example"] == "yes"


def test_a_database_error_answers_unavailable_without_the_driver_text(
    signed_in: Harness, json_logs: LogCapture
) -> None:
    response = signed_in.client.get("/api/test/database")

    body = envelope(response, 503, "database_unavailable")
    assert body["message"] == "The database could not complete the request."
    (entry,) = [
        e for e in log_entries(json_logs) if e["msg"] == "Database error while handling a request"
    ]
    assert entry["correlationId"] == body["correlationId"]
    assert entry["excType"] == "OperationalError"


def test_every_refusal_uses_the_same_shape(signed_in: Harness) -> None:
    client = signed_in.client
    visitor = signed_in.new_client()

    envelope(visitor.get("/api/system/status"), 401, "not_authenticated")
    envelope(visitor.get("/api/nothing-here"), 401, "not_authenticated")
    envelope(client.post("/api/audit/verify"), 403, "csrf_failed")
    envelope(client.get("/api/audit/events?limit=0"), 422, "validation_failed")
    envelope(client.get("/api/nothing-here"), 404, "not_found")
    envelope(client.get("/api/test/boom"), 500, "internal_error")


# -- correlation IDs --------------------------------------------------------------------------


def test_every_response_carries_its_own_correlation_id(signed_in: Harness) -> None:
    client = signed_in.client
    responses = [
        client.get("/api/healthz"),
        client.get("/api/auth/user"),
        client.get("/api/system/status"),
        client.get("/api/login"),
        client.get("/api/nothing-here"),
        client.get("/api/test/boom"),
        signed_in.new_client().get("/api/system/status"),
    ]

    ids = [response.headers[CORRELATION_HEADER] for response in responses]

    assert all(HEX32.match(value) for value in ids)
    assert len(set(ids)) == len(ids)


def test_the_caller_cannot_choose_the_correlation_id(client: TestClient) -> None:
    chosen = "chosen-by-the-caller"

    response = client.get(
        "/api/system/status", headers={CORRELATION_HEADER: chosen, "X-Request-ID": chosen}
    )

    assert response.status_code == 401
    assert HEX32.match(response.headers[CORRELATION_HEADER])
    assert chosen not in response.text
    assert chosen not in json.dumps(dict(response.headers))


def test_the_correlation_id_finds_the_log_lines_of_a_request(
    harness: Harness, json_logs: LogCapture
) -> None:
    client = harness.client
    sign_in(client, harness.provider)
    json_logs.lines.clear()

    first = client.post("/api/audit/verify")
    second = client.get("/api/system/status")

    def lines_of(response: httpx.Response) -> list[str]:
        wanted = response.headers[CORRELATION_HEADER]
        return [e["msg"] for e in log_entries(json_logs) if e.get("correlationId") == wanted]

    assert lines_of(first) == ["Request refused: not from this app's origin", "request"]
    assert lines_of(second) == ["request"]


# -- headers on every response ----------------------------------------------------------------


def test_every_response_carries_the_security_headers(signed_in: Harness) -> None:
    client = signed_in.client
    responses = [
        client.get("/api/healthz"),
        client.get("/api/auth/user"),
        client.get("/api/auth/csrf"),
        client.get("/api/system/status"),
        client.get("/api/audit/events"),
        client.get("/api/login"),
        client.get("/api/callback"),
        client.get("/api/nothing-here"),
        client.get("/api/audit/events?limit=0"),
        client.post("/api/audit/verify"),
        client.get("/api/test/boom"),
        client.get("/api/test/database"),
        signed_in.new_client().get("/api/system/status"),
        client.get("/api/logout"),
    ]

    for response in responses:
        where = f"{response.request.method} {response.request.url.path} -> {response.status_code}"
        for name, value in SECURITY_HEADERS.items():
            assert response.headers[name] == value, where
        assert response.headers["strict-transport-security"] == HSTS, where
        assert response.headers["cache-control"] == "no-store", where
        assert HEX32.match(response.headers[CORRELATION_HEADER]), where
        assert "server" not in response.headers, where
        assert "x-powered-by" not in response.headers, where
        assert "access-control-allow-origin" not in response.headers, where


def test_development_sends_the_same_headers_except_strict_transport(
    make_harness: AppFactory,
) -> None:
    harness = make_harness(STAI_ENV="development")

    for response in (
        harness.client.get("/api/healthz"),
        harness.client.get("/api/system/status"),
    ):
        for name, value in SECURITY_HEADERS.items():
            assert response.headers[name] == value
        assert response.headers["cache-control"] == "no-store"
        assert "strict-transport-security" not in response.headers
