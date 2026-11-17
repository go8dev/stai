"""Logs: one JSON object per line, a correlation ID per request, and no secrets."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import numpy as np
import pytest
from starlette.testclient import TestClient

from stai.core.logging import (
    REDACTED,
    JsonFormatter,
    StructuredLogger,
    clear_secret_values,
    configure_logging,
    register_secret_values,
    scrub,
    set_correlation_id,
)
from stai.core.middleware import CORRELATION_HEADER
from stai.main import create_app
from stai.system.schemas import TradingMode

from .conftest import Harness, LogCapture
from .support import ACCESS_TOKEN, APP_ORIGIN, begin_login, csrf_headers, finish_login

logger = StructuredLogger("stai.tests.logging")

SECRET = "s3cr3t-value-0001"
SENSITIVE = "sensitive-field-value-0002"
TIMESTAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}\+00:00")


def last(logs: LogCapture) -> dict[str, Any]:
    assert logs.lines, "nothing was logged"
    return json.loads(logs.lines[-1])


def entries(logs: LogCapture, logger_name: str | None = None) -> list[dict[str, Any]]:
    found = [json.loads(line) for line in logs.lines]
    return [e for e in found if logger_name is None or e["logger"] == logger_name]


# -- the shape of a line ----------------------------------------------------------------------


def test_each_log_line_is_one_json_object(json_logs: LogCapture) -> None:
    logger.info("Market snapshot computed", symbol="BTC-USDT", rsi=41.2)

    (line,) = json_logs.lines
    assert "\n" not in line
    entry = json.loads(line)
    assert entry == {
        "ts": entry["ts"],
        "level": "info",
        "logger": "stai.tests.logging",
        "msg": "Market snapshot computed",
        "symbol": "BTC-USDT",
        "rsi": 41.2,
    }


def test_the_time_of_a_line_is_utc_to_the_millisecond(json_logs: LogCapture) -> None:
    logger.info("now")

    written = last(json_logs)["ts"]

    assert TIMESTAMP.fullmatch(written)
    assert abs(datetime.now(UTC) - datetime.fromisoformat(written)) < timedelta(seconds=5)


@pytest.mark.parametrize("level", ["debug", "info", "warning", "error", "critical"])
def test_each_level_is_written_by_name(json_logs: LogCapture, level: str) -> None:
    getattr(logger, level)("at this level")

    assert last(json_logs)["level"] == level


def test_a_message_with_line_breaks_stays_on_one_line(json_logs: LogCapture) -> None:
    forged = 'first line\n{"level":"info","msg":"a second, made-up line"}\r\n'

    logger.warning(forged, note="tab\there\nnew line")

    (line,) = json_logs.lines
    assert "\n" not in line
    assert "\r" not in line
    assert json.loads(line)["msg"] == forged
    assert json.loads(line)["note"] == "tab\there\nnew line"


def test_a_field_cannot_replace_the_fixed_parts_of_a_line(json_logs: LogCapture) -> None:
    set_correlation_id("request-1")

    logger.info("real message", msg="made up", level="critical", ts="1999", correlationId="x")

    entry = last(json_logs)
    assert entry["msg"] == "real message"
    assert entry["level"] == "info"
    assert TIMESTAMP.fullmatch(entry["ts"])
    assert entry["correlationId"] == "request-1"
    assert entry["field_msg"] == "made up"
    assert entry["field_level"] == "critical"
    assert entry["field_ts"] == "1999"
    assert entry["field_correlationId"] == "x"


def test_values_are_written_in_a_form_json_can_carry(json_logs: LogCapture) -> None:
    logger.info(
        "values",
        price=Decimal("0.10"),
        at=datetime(2026, 11, 17, 20, 30, tzinfo=UTC),
        mode=TradingMode.PAPER,
        count=np.int64(3),
        ratio=np.float64(0.5),
        tags={"only"},
        pair=("BTC-USDT", 1),
        nothing=None,
        flag=True,
        where=Path("/tmp/somewhere"),  # noqa: S108
        nested={"amount": Decimal("1.5"), "items": [np.int64(1), None]},
    )

    entry = last(json_logs)
    # A decimal stays text, so no digit is lost on the way to the log.
    assert entry["price"] == "0.10"
    assert entry["at"] == "2026-11-17T20:30:00+00:00"
    assert entry["mode"] == "paper"
    assert entry["count"] == 3
    assert entry["ratio"] == 0.5
    assert entry["tags"] == ["only"]
    assert entry["pair"] == ["BTC-USDT", 1]
    assert entry["nothing"] is None
    assert entry["flag"] is True
    assert entry["where"] == "/tmp/somewhere"  # noqa: S108
    assert entry["nested"] == {"amount": "1.5", "items": [1, None]}


def test_numbers_json_cannot_carry_are_written_as_text(json_logs: LogCapture) -> None:
    logger.info("values", a=float("nan"), b=float("inf"), c=np.float64("-inf"), d=[np.nan])

    (line,) = json_logs.lines
    # Strict JSON: a parser that rejects NaN and Infinity still reads the line.
    entry = json.loads(line, parse_constant=lambda name: pytest.fail(f"bare {name} in the line"))
    assert entry["a"] == "nan"
    assert entry["b"] == "inf"
    assert entry["c"] == "-inf"
    assert entry["d"] == ["nan"]


def test_an_exception_is_logged_with_its_type_message_and_traceback(
    json_logs: LogCapture,
) -> None:
    try:
        raise ValueError("bad value")
    except ValueError:
        logger.exception("Something failed", step="load")

    entry = last(json_logs)
    assert entry["level"] == "error"
    assert entry["msg"] == "Something failed"
    assert entry["step"] == "load"
    assert entry["excType"] == "ValueError"
    assert entry["exc"] == "bad value"
    assert entry["traceback"].startswith("Traceback (most recent call last)")
    assert "test_logging.py" in entry["traceback"]
    assert len(json_logs.lines) == 1


def test_records_from_libraries_use_the_same_format(json_logs: LogCapture) -> None:
    logging.getLogger("some.library").warning(
        "Started %s process [%d]", "server", 42, extra={"password": SENSITIVE}
    )

    entry = last(json_logs)
    assert entry == {
        "ts": entry["ts"],
        "level": "warning",
        "logger": "some.library",
        "msg": "Started server process [42]",
    }
    assert SENSITIVE not in json_logs.text


def test_the_logger_reports_its_name() -> None:
    assert logger.name == "stai.tests.logging"


def test_a_level_that_is_switched_off_writes_nothing(json_logs: LogCapture) -> None:
    quiet = logging.getLogger("stai.tests.quiet")
    quiet.setLevel(logging.WARNING)
    try:
        StructuredLogger("stai.tests.quiet").info("not written")
        StructuredLogger("stai.tests.quiet").warning("written")
    finally:
        quiet.setLevel(logging.NOTSET)

    assert [entry["msg"] for entry in entries(json_logs)] == ["written"]


# -- correlation IDs --------------------------------------------------------------------------


def test_lines_written_during_a_request_carry_its_correlation_id(json_logs: LogCapture) -> None:
    set_correlation_id("request-1")
    logger.info("inside the request")
    logging.getLogger("some.library").info("a library, inside the same request")
    set_correlation_id(None)
    logger.info("outside any request")

    inside, library, outside = entries(json_logs)

    assert inside["correlationId"] == "request-1"
    assert library["correlationId"] == "request-1"
    assert "correlationId" not in outside


# -- sensitive field names --------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "token",
        "sessionToken",
        "id_token",
        "access_token",
        "refreshToken",
        "csrfToken",
        "Authorization",
        "cookie",
        "Cookie",
        "set_cookie",
        "password",
        "db_passwd",
        "client_secret",
        "SESSION_SECRET",
        "api_key",
        "apiKey",
        "OPENAI_API_KEY",
        "private_key",
        "code_verifier",
        "nonce",
        "email",
        "alertEmail",
        "dsn",
        "database_url",
        "DATABASE_URL",
    ],
)
def test_a_field_with_a_sensitive_name_is_never_written(json_logs: LogCapture, name: str) -> None:
    logger.info("with a sensitive field", **{name: SENSITIVE})

    assert last(json_logs)[name] == REDACTED
    assert SENSITIVE not in json_logs.text


def test_sensitive_names_are_caught_inside_nested_values_too(json_logs: LogCapture) -> None:
    logger.info(
        "nested",
        request={
            "headers": {"Cookie": SENSITIVE, "accept": "application/json"},
            "items": [{"password": SENSITIVE, "position": 1}, ({"api_key": SENSITIVE},)],
        },
    )

    assert last(json_logs)["request"] == {
        "headers": {"Cookie": REDACTED, "accept": "application/json"},
        "items": [{"password": REDACTED, "position": 1}, [{"api_key": REDACTED}]],
    }
    assert SENSITIVE not in json_logs.text


def test_a_sensitive_name_hides_the_whole_value_whatever_its_type(json_logs: LogCapture) -> None:
    logger.info("structured", cookies={"sid": SENSITIVE}, tokens=[SENSITIVE], password=None)

    entry = last(json_logs)
    assert entry["cookies"] == REDACTED
    assert entry["tokens"] == REDACTED
    assert entry["password"] == REDACTED


def test_ordinary_fields_are_written_as_given(json_logs: LogCapture) -> None:
    logger.info("request", method="GET", path="/api/system/status", status=200, durationMs=1.5)

    entry = last(json_logs)
    assert (entry["method"], entry["path"], entry["status"], entry["durationMs"]) == (
        "GET",
        "/api/system/status",
        200,
        1.5,
    )


# -- registered secret values -----------------------------------------------------------------


def test_a_registered_secret_is_masked_wherever_it_appears(json_logs: LogCapture) -> None:
    register_secret_values([SECRET])

    try:
        raise RuntimeError(f"connecting with {SECRET} failed")
    except RuntimeError:
        logger.exception(
            f"message with {SECRET}", note=f"a field with {SECRET}", nested={"deep": [SECRET]}
        )
    logging.getLogger(f"library.{SECRET}").warning("printf style %s", SECRET)

    assert SECRET not in json_logs.text
    first, second = entries(json_logs)
    assert first["msg"] == f"message with {REDACTED}"
    assert first["note"] == f"a field with {REDACTED}"
    assert first["nested"] == {"deep": [REDACTED]}
    assert first["exc"] == f"connecting with {REDACTED} failed"
    assert REDACTED in first["traceback"]
    assert second["logger"] == f"library.{REDACTED}"
    assert second["msg"] == f"printf style {REDACTED}"


@pytest.mark.parametrize(
    "secret",
    [
        'quote"inside-0001',
        "back\\slash-0001",
        "two\nlines-0001",
        "tab\tinside-0001",
        "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASC\n-----END PRIVATE KEY-----",
        "unicode-ключ-鍵-0001",
    ],
)
def test_a_secret_that_json_has_to_escape_is_masked_as_well(
    json_logs: LogCapture, secret: str
) -> None:
    register_secret_values([secret])

    logger.error(f"failed with {secret}", detail=secret, nested={"value": [secret]})

    entry = last(json_logs)
    assert entry["msg"] == f"failed with {REDACTED}"
    assert entry["detail"] == REDACTED
    assert entry["nested"] == {"value": [REDACTED]}
    assert secret not in json_logs.text
    assert json.dumps(secret, ensure_ascii=False)[1:-1] not in json_logs.text


def test_a_secret_that_contains_another_is_masked_whole(json_logs: LogCapture) -> None:
    register_secret_values(["abcdef-short", "abcdef-short-and-the-rest-of-it"])

    logger.info("using abcdef-short-and-the-rest-of-it then abcdef-short")

    assert last(json_logs)["msg"] == f"using {REDACTED} then {REDACTED}"


def test_very_short_values_are_not_treated_as_secrets(json_logs: LogCapture) -> None:
    register_secret_values(["", "abc", "12345"])

    logger.info("abc 12345 stay readable")

    assert last(json_logs)["msg"] == "abc 12345 stay readable"


def test_registering_adds_to_the_values_already_known(json_logs: LogCapture) -> None:
    register_secret_values(["first-secret-value"])
    register_secret_values(["second-secret-value"])
    register_secret_values(["first-secret-value"])

    assert scrub("first-secret-value second-secret-value") == f"{REDACTED} {REDACTED}"

    clear_secret_values()

    assert scrub("first-secret-value") == "first-secret-value"


# -- what the application itself logs ---------------------------------------------------------


def test_each_request_is_logged_once_without_its_query_string(
    harness: Harness, json_logs: LogCapture
) -> None:
    marker = "query-value-that-must-not-be-logged"

    response = harness.client.get(f"/api/system/status?state={marker}&code={marker}")

    assert response.status_code == 401
    (entry,) = entries(json_logs, "stai.request")
    assert entry["msg"] == "request"
    assert entry["level"] == "info"
    assert entry["method"] == "GET"
    assert entry["path"] == "/api/system/status"
    assert entry["status"] == 401
    assert entry["durationMs"] >= 0
    assert entry["correlationId"] == response.headers[CORRELATION_HEADER]
    assert marker not in json_logs.text


def test_the_health_check_is_logged_only_at_debug(harness: Harness, json_logs: LogCapture) -> None:
    harness.client.get("/api/healthz")
    harness.client.post("/api/healthz")

    passed, refused = entries(json_logs, "stai.request")

    # A probe every few seconds would bury everything else at the default level.
    assert (passed["status"], passed["level"]) == (200, "debug")
    # A health check that does not answer 200 is worth a normal line.
    assert (refused["status"], refused["level"]) == (405, "info")


def test_request_headers_and_cookies_are_never_logged(
    harness: Harness, json_logs: LogCapture
) -> None:
    marker = "header-value-that-must-not-be-logged"

    harness.client.get(
        "/api/system/status",
        headers={
            "Authorization": f"Bearer {marker}",
            "Cookie": f"sid={marker}",
            "X-CSRF-Token": marker,
            "User-Agent": marker,
            "Referer": f"https://elsewhere.test/{marker}",
        },
    )

    assert entries(json_logs, "stai.request")
    assert marker not in json_logs.text


def test_a_sign_in_and_sign_out_leave_no_token_in_the_logs(
    harness: Harness, json_logs: LogCapture
) -> None:
    client, provider = harness.client, harness.provider

    authorization = begin_login(client)
    flow_cookies = [client.cookies.get(name) for name in list(client.cookies.keys())]
    assert finish_login(client, provider, authorization).status_code == 302
    session_token = client.cookies.get("sid")
    headers = csrf_headers(client)
    assert client.post("/api/audit/verify", headers=headers).status_code == 200
    assert client.get("/api/logout").status_code == 302

    (token_request,) = provider.calls_to("/token")
    form = {key: values[0] for key, values in parse_qs(token_request.content.decode()).items()}
    must_not_appear = [
        session_token,
        headers["X-CSRF-Token"],
        authorization["state"],
        authorization["nonce"],
        authorization["code_challenge"],
        form["code"],
        form["code_verifier"],
        provider.last_id_token,
        ACCESS_TOKEN,
        *flow_cookies,
    ]

    messages = [entry["msg"] for entry in entries(json_logs)]
    assert "Owner signed in" in messages
    assert "Signed out" in messages
    assert len(flow_cookies) >= 3
    for value in must_not_appear:
        assert value
        assert value not in json_logs.text


# -- configure_logging ------------------------------------------------------------------------


def stai_handlers() -> list[logging.Handler]:
    root = logging.getLogger()
    return [h for h in root.handlers if getattr(h, "_stai_json_handler", False)]


def printed(capsys: pytest.CaptureFixture[str]) -> list[dict[str, Any]]:
    return [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.strip()]


def test_configuring_twice_leaves_one_handler(restored_logging: None) -> None:
    others = len(logging.getLogger().handlers)

    configure_logging("INFO")
    configure_logging("DEBUG")

    (handler,) = stai_handlers()
    assert isinstance(handler.formatter, JsonFormatter)
    assert len(logging.getLogger().handlers) == others + 1
    assert logging.getLogger().level == logging.DEBUG


def test_logs_go_to_standard_output_at_the_configured_level(
    restored_logging: None, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_logging("WARNING")

    logger.info("below the level")
    logger.warning("at the level", n=1)

    (entry,) = printed(capsys)
    assert entry["msg"] == "at the level"
    assert entry["n"] == 1


def test_libraries_that_log_addresses_and_sql_stay_quiet_even_in_debug(
    restored_logging: None,
) -> None:
    configure_logging("DEBUG")

    for name in ("httpx", "httpcore", "sqlalchemy"):
        assert logging.getLogger(name).getEffectiveLevel() == logging.WARNING
    for name in ("httpcore.http11", "sqlalchemy.engine", "sqlalchemy.pool"):
        assert not logging.getLogger(name).isEnabledFor(logging.INFO)
    assert logging.getLogger("stai.anything").isEnabledFor(logging.DEBUG)


def test_the_web_server_writes_through_the_same_formatter(
    restored_logging: None, capsys: pytest.CaptureFixture[str]
) -> None:
    # Uvicorn installs its own plain-text handlers; they must not survive.
    logging.getLogger("uvicorn.error").addHandler(logging.StreamHandler())
    logging.getLogger("uvicorn.access").addHandler(logging.StreamHandler())

    configure_logging("INFO")
    logging.getLogger("uvicorn.error").info("Uvicorn running on %s", "http://0.0.0.0:8080")
    logging.getLogger("uvicorn.access").info('GET /api/callback?code=%s HTTP/1.1" 302', SECRET)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        assert logging.getLogger(name).handlers == []
        assert logging.getLogger(name).propagate is True
    (entry,) = printed(capsys)
    assert entry["logger"] == "uvicorn.error"
    assert entry["msg"] == "Uvicorn running on http://0.0.0.0:8080"
    # The server's own access log repeats query strings, so it is switched off entirely.
    assert logging.getLogger("uvicorn.access").disabled is True


def test_the_running_app_masks_the_secrets_of_its_environment(
    clean_environment: pytest.MonkeyPatch,
    restored_logging: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    values = {
        "DATABASE_URL": "postgresql://stai:p%40ss-w0rd-value@db.internal:5432/stai",
        "PGPASSWORD": "pg-password-value",
        "SESSION_SECRET": "session-secret-value",
        "OPENAI_API_KEY": "sk-made-up-for-this-test",
        "STAI_ALERT_EMAIL": "owner@example.test",
    }
    for name, value in values.items():
        clean_environment.setenv(name, value)
    leaked = [*values.values(), "p%40ss-w0rd-value", "p@ss-w0rd-value"]

    with TestClient(create_app(), base_url=APP_ORIGIN) as client:
        assert client.get("/api/healthz").status_code == 200
        logging.getLogger("some.library").error("failed: %s", " | ".join(leaked))
        logger.error(
            "failed", detail=leaked, target="postgresql+psycopg://stai:p%40ss-w0rd-value@db"
        )

    lines = printed(capsys)
    text = json.dumps(lines)
    for value in leaked:
        assert value not in text
    library = next(entry for entry in lines if entry["logger"] == "some.library")
    assert library["msg"] == "failed: " + " | ".join([REDACTED] * len(leaked))
    started = next(entry for entry in lines if entry["msg"] == "STAI backend started")
    assert started["environment"] == "production"
    assert started["tradingMode"] == "paper"
    assert started["databaseConfigured"] is True
    assert started["signInConfigured"] is False
    assert [entry["msg"] for entry in lines][-1] == "STAI backend stopped"
