"""The system status: live checks of the backend, database, market data, audit trail and build."""

from __future__ import annotations

import asyncio
import json
import platform
import re
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

import stai
from stai.core import build
from stai.marketdata import okx_public
from stai.marketdata.okx_public import MarketDataReachability, OkxPublicProbe
from stai.system import service as system_service
from stai.system.schemas import CheckStatus
from stai.system.service import check_database, collect_status, overall_status

from .conftest import AppFactory, DatabaseFactory, Harness, LogCapture
from .support import OKX_BASE, FakeClock, FakeProvider, sign_in

UNREACHABLE_PASSWORD = "pw-that-must-not-be-shown"
UNREACHABLE_DATABASE = f"postgresql://nobody:{UNREACHABLE_PASSWORD}@127.0.0.1:1/none"
TIME_URL = f"{OKX_BASE}/api/v5/public/time"


@pytest.fixture
def owner(harness: Harness) -> Harness:
    assert sign_in(harness.client, harness.provider).status_code == 302
    return harness


def status(harness: Harness) -> dict[str, Any]:
    response = harness.client.get("/api/system/status")
    assert response.status_code == 200, response.text
    return response.json()


def instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None, value
    return parsed


# -- GET /api/system/status -------------------------------------------------------------------


def test_every_check_is_reported_when_all_is_well(owner: Harness) -> None:
    body = status(owner)

    assert set(body) == {
        "overall",
        "tradingMode",
        "checkedAt",
        "backend",
        "database",
        "marketData",
        "audit",
        "build",
        "time",
    }
    assert body["overall"] == "ok"
    assert body["backend"]["status"] == "ok"
    assert body["database"]["status"] == "ok"
    assert body["marketData"]["status"] == "ok"
    assert body["audit"]["status"] == "ok"
    assert instant(body["checkedAt"]) == owner.clock()


def test_the_trading_mode_is_paper(owner: Harness) -> None:
    assert status(owner)["tradingMode"] == "paper"


def test_the_backend_check(owner: Harness) -> None:
    owner.clock.advance(seconds=185)

    backend = status(owner)["backend"]

    assert backend == {
        "status": "ok",
        "environment": "production",
        "uptimeSeconds": 185,
        "pythonVersion": platform.python_version(),
    }


def test_development_is_reported_only_when_it_was_asked_for(make_harness: AppFactory) -> None:
    harness = make_harness(STAI_ENV="development")
    sign_in(harness.client, harness.provider)

    assert status(harness)["backend"]["environment"] == "development"


def test_the_database_check(owner: Harness) -> None:
    database = status(owner)["database"]

    with owner.admin.connect() as connection:
        server_version = connection.execute(text("SHOW server_version")).scalar_one()

    assert set(database) == {
        "status",
        "latencyMs",
        "serverVersion",
        "schemaReady",
        "missingTables",
        "migrationRevision",
        "detail",
    }
    assert database["status"] == "ok"
    assert 0 <= database["latencyMs"] < 5000
    assert database["serverVersion"] == server_version.split(" ")[0]
    assert database["schemaReady"] is True
    assert database["missingTables"] == []
    assert database["migrationRevision"] == "0006"
    assert database["detail"] is None


def test_the_market_data_check(owner: Harness) -> None:
    market_data = status(owner)["marketData"]

    assert set(market_data) == {
        "status",
        "provider",
        "endpoint",
        "latencyMs",
        "exchangeTime",
        "clockSkewMs",
        "checkedAt",
        "detail",
    }
    assert market_data["status"] == "ok"
    assert market_data["provider"] == "OKX"
    assert market_data["endpoint"] == TIME_URL
    assert 0 <= market_data["latencyMs"] < 2000
    assert abs(market_data["clockSkewMs"]) < 1000
    assert abs(instant(market_data["exchangeTime"]) - owner.clock()) < timedelta(seconds=1)
    assert instant(market_data["checkedAt"]) == owner.clock()
    assert market_data["detail"] is None


def test_the_build_facts(owner: Harness) -> None:
    started = owner.clock()
    owner.clock.advance(minutes=5)

    facts = status(owner)["build"]

    assert set(facts) == {"version", "commit", "startedAt"}
    assert facts["version"] == stai.__version__
    assert instant(facts["startedAt"]) == started
    assert facts["commit"] is None or re.fullmatch(r"[0-9a-f]{7,12}", facts["commit"])


def test_a_configured_commit_is_shown_shortened(make_harness: AppFactory) -> None:
    harness = make_harness(STAI_BUILD_COMMIT="  0123456789abcdef0123456789abcdef01234567 ")
    sign_in(harness.client, harness.provider)

    assert status(harness)["build"]["commit"] == "0123456789ab"


def test_time_is_utc_with_manila_alongside(make_harness: AppFactory, clock: FakeClock) -> None:
    clock.now = datetime(2026, 11, 17, 20, 30, 15, tzinfo=UTC)
    harness = make_harness()
    sign_in(harness.client, harness.provider)

    body = status(harness)

    assert body["time"]["timezone"] == "Asia/Manila"
    assert instant(body["time"]["utc"]) == clock.now
    assert instant(body["time"]["utc"]).utcoffset() == timedelta(0)
    # Half past eight in the evening UTC is already the next morning in Manila.
    assert body["time"]["manila"] == "2026-11-18T04:30:15+08:00"
    assert instant(body["time"]["manila"]) == clock.now


def test_the_status_is_never_cached(owner: Harness) -> None:
    assert owner.client.get("/api/system/status").headers["cache-control"] == "no-store"


def test_the_status_takes_no_input(owner: Harness) -> None:
    owner.provider.okx_status = 403

    body = owner.client.get("/api/system/status?overall=ok&tradingMode=live").json()

    assert body["overall"] == "degraded"
    assert body["tradingMode"] == "paper"


def test_the_status_shows_nothing_from_the_environment(owner: Harness) -> None:
    raw = owner.client.get("/api/system/status").text

    assert owner.runtime.settings.database_url is not None
    assert owner.runtime.settings.database_url.get_secret_value() not in raw
    assert "postgresql" not in raw
    assert owner.runtime.settings.owner_user_id not in raw
    assert owner.runtime.settings.repl_id not in raw


@pytest.mark.parametrize(
    ("okx_status", "detail"),
    [
        (403, "OKX answered HTTP 403. This machine's region may be blocked."),
        (451, "OKX answered HTTP 451. This machine's region may be blocked."),
        (503, "OKX answered HTTP 503."),
    ],
)
def test_market_data_out_of_reach_degrades_the_whole(
    owner: Harness, okx_status: int, detail: str
) -> None:
    owner.provider.okx_status = okx_status

    body = status(owner)

    assert body["marketData"]["status"] == "down"
    assert body["marketData"]["detail"] == detail
    assert body["marketData"]["exchangeTime"] is None
    assert body["marketData"]["clockSkewMs"] is None
    # STAI still works without fresh market data, so this is degraded, not down.
    assert body["overall"] == "degraded"
    assert body["database"]["status"] == "ok"
    assert body["audit"]["status"] == "ok"


def test_the_market_data_answer_is_reused_for_a_few_seconds(owner: Harness) -> None:
    for _ in range(4):
        status(owner)

    assert len(owner.provider.calls_to(OKX_BASE)) == 1


def test_the_database_and_the_audit_trail_are_checked_on_every_call(owner: Harness) -> None:
    assert status(owner)["audit"]["eventCount"] == 1

    with owner.admin.begin() as connection:
        connection.execute(text("UPDATE audit_events SET payload = '{}'"))

    assert status(owner)["audit"]["status"] == "down"


# -- the database check on its own ------------------------------------------------------------


def test_no_database_configured(make_harness: AppFactory) -> None:
    harness = make_harness(use_database=False)

    database, audit = check_database(harness.runtime)

    assert database.status is CheckStatus.DOWN
    assert database.detail == "DATABASE_URL is not set."
    assert database.schema_ready is False
    assert database.latency_ms is None
    assert audit.status is CheckStatus.DOWN
    assert audit.detail == "The audit trail cannot be read while the database is unavailable."
    assert audit.event_count == 0


def test_a_database_that_cannot_be_reached(make_harness: AppFactory, json_logs: LogCapture) -> None:
    harness = make_harness(DATABASE_URL=UNREACHABLE_DATABASE)

    database, audit = check_database(harness.runtime)

    assert database.status is CheckStatus.DOWN
    assert database.detail == "The database could not be reached."
    assert audit.status is CheckStatus.DOWN
    # The reason is logged for the owner, without the password.
    assert "Database check failed" in json_logs.text
    assert UNREACHABLE_PASSWORD not in json_logs.text


def test_a_database_without_the_tables(
    make_harness: AppFactory, database_factory: DatabaseFactory
) -> None:
    empty = database_factory.create(migrated=False)
    harness = make_harness(DATABASE_URL=empty)

    database, audit = check_database(harness.runtime)

    assert database.status is CheckStatus.DOWN
    assert database.schema_ready is False
    assert database.missing_tables == [
        "audit_events",
        "auth_sessions",
        "bot_states",
        "committee_agents",
        "committee_calls",
        "committee_findings",
        "committee_runs",
        "fund_allocations",
        "ledger_entries",
        "market_snapshots",
        "paper_fills",
        "paper_positions",
        "setup_candidates",
        "strategy_backtest_reviews",
        "strategy_backtest_runs",
        "trade_proposals",
        "trading_permits",
        "users",
        "virtual_funds",
    ]
    assert database.detail == f"Missing tables: {', '.join(database.missing_tables)}."
    assert database.migration_revision is None
    assert database.latency_ms is not None
    assert database.server_version
    assert audit.status is CheckStatus.DOWN
    assert audit.detail == "The audit table does not exist."


def test_a_database_missing_one_table(
    make_harness: AppFactory, database_factory: DatabaseFactory
) -> None:
    url = database_factory.create(migrated=True)
    engine = create_engine(url, poolclass=NullPool)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE auth_sessions"))
    engine.dispose()
    harness = make_harness(DATABASE_URL=url)

    database, audit = check_database(harness.runtime)

    assert database.status is CheckStatus.DOWN
    assert database.missing_tables == ["auth_sessions"]
    assert database.detail == "Missing tables: auth_sessions."
    assert database.migration_revision == "0006"
    # The audit table is there and empty, so its own check passes.
    assert audit.status is CheckStatus.OK
    assert audit.event_count == 0


def test_an_audit_table_with_another_structure(
    make_harness: AppFactory, database_factory: DatabaseFactory, json_logs: LogCapture
) -> None:
    url = database_factory.create(migrated=True)
    engine = create_engine(url, poolclass=NullPool)
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE audit_events RENAME COLUMN payload TO body"))
    engine.dispose()
    harness = make_harness(DATABASE_URL=url)

    database, audit = check_database(harness.runtime)

    # The database answers and every table exists; it is the trail that cannot be read.
    assert database.status is CheckStatus.OK
    assert audit.status is CheckStatus.DOWN
    assert audit.detail == "The audit trail could not be checked."
    assert "Audit trail check failed" in json_logs.text


def test_an_audit_check_that_fails_does_not_take_the_status_with_it(
    harness: Harness, monkeypatch: pytest.MonkeyPatch, json_logs: LogCapture
) -> None:
    def explode(session: Any) -> None:
        raise ZeroDivisionError("unexpected")

    monkeypatch.setattr(system_service.audit_service, "summarise", explode)

    database, audit = check_database(harness.runtime)

    assert database.status is CheckStatus.OK
    assert audit.status is CheckStatus.DOWN
    assert audit.detail == "The audit trail could not be checked."
    assert "Audit trail check failed" in json_logs.text


def test_the_whole_status_is_assembled_when_the_database_is_down(make_harness: AppFactory) -> None:
    harness = make_harness(DATABASE_URL=UNREACHABLE_DATABASE)

    result = asyncio.run(collect_status(harness.runtime))

    assert result.overall is CheckStatus.DOWN
    assert result.database.status is CheckStatus.DOWN
    assert result.audit.status is CheckStatus.DOWN
    assert result.market_data.status is CheckStatus.OK
    assert result.backend.status is CheckStatus.OK
    assert result.trading_mode.value == "paper"


def check(value: str) -> Any:
    return SimpleNamespace(status=CheckStatus(value))


@pytest.mark.parametrize(
    ("database", "audit", "market_data", "expected"),
    [
        ("ok", "ok", "ok", "ok"),
        ("ok", "ok", "degraded", "degraded"),
        ("ok", "ok", "down", "degraded"),
        ("degraded", "ok", "ok", "degraded"),
        ("ok", "degraded", "ok", "degraded"),
        ("down", "ok", "ok", "down"),
        ("ok", "down", "ok", "down"),
        ("down", "down", "down", "down"),
        ("down", "ok", "degraded", "down"),
        ("degraded", "down", "down", "down"),
    ],
)
def test_overall_is_down_only_when_stai_cannot_work(
    database: str, audit: str, market_data: str, expected: str
) -> None:
    result = overall_status(check(database), check(audit), check(market_data))

    assert result is CheckStatus(expected)


# -- the OKX public-data check on its own -----------------------------------------------------


def run_probe(provider: FakeProvider, clock: FakeClock, **options: Any) -> MarketDataReachability:
    provider.okx_time = clock

    async def scenario() -> MarketDataReachability:
        async with httpx.AsyncClient(transport=provider.transport()) as http:
            return await OkxPublicProbe(http, OKX_BASE, clock=clock, **options).check()

    return asyncio.run(scenario())


def test_okx_reachable(provider: FakeProvider, clock: FakeClock) -> None:
    result = run_probe(provider, clock)

    assert result.status == "ok"
    assert result.provider == "OKX"
    assert result.endpoint == TIME_URL
    assert result.detail is None
    assert result.checked_at == clock()
    assert result.exchange_time is not None
    assert result.exchange_time.utcoffset() == timedelta(0)
    assert abs(result.exchange_time - clock()) < timedelta(milliseconds=2)
    assert result.latency_ms is not None and 0 <= result.latency_ms < 2000
    assert result.clock_skew_ms is not None and abs(result.clock_skew_ms) < 1000


def test_the_check_is_one_public_request_without_credentials(
    provider: FakeProvider, clock: FakeClock
) -> None:
    run_probe(provider, clock)

    (request,) = provider.requests
    assert request.method == "GET"
    assert str(request.url) == TIME_URL
    assert request.content == b""
    assert request.headers["accept"] == "application/json"
    sent = {name.lower() for name in request.headers}
    assert not {name for name in sent if name.startswith("ok-access")}
    assert "authorization" not in sent
    assert "cookie" not in sent


def test_a_trailing_slash_in_the_base_address_is_ignored(
    provider: FakeProvider, clock: FakeClock
) -> None:
    provider.okx_time = clock

    async def scenario() -> str:
        async with httpx.AsyncClient(transport=provider.transport()) as http:
            probe = OkxPublicProbe(http, f"{OKX_BASE}/", clock=clock)
            await probe.check()
            return probe.endpoint

    assert asyncio.run(scenario()) == TIME_URL
    assert str(provider.requests[0].url) == TIME_URL


@pytest.mark.parametrize(
    ("code", "detail"),
    [
        (403, "OKX answered HTTP 403. This machine's region may be blocked."),
        (451, "OKX answered HTTP 451. This machine's region may be blocked."),
        (301, "OKX answered HTTP 301."),
        (400, "OKX answered HTTP 400."),
        (404, "OKX answered HTTP 404."),
        (429, "OKX answered HTTP 429."),
        (500, "OKX answered HTTP 500."),
        (503, "OKX answered HTTP 503."),
    ],
)
def test_okx_answering_with_an_error_status(
    provider: FakeProvider, clock: FakeClock, code: int, detail: str
) -> None:
    provider.okx_status = code

    result = run_probe(provider, clock)

    assert result.status == "down"
    assert result.detail == detail
    assert result.latency_ms is not None
    assert result.exchange_time is None
    assert result.clock_skew_ms is None


@pytest.mark.parametrize(
    ("error", "detail"),
    [
        (httpx.ConnectTimeout("timed out"), "No answer from OKX within 8 seconds."),
        (httpx.ReadTimeout("timed out"), "No answer from OKX within 8 seconds."),
        (httpx.PoolTimeout("timed out"), "No answer from OKX within 8 seconds."),
        (httpx.ConnectError("refused"), "OKX could not be reached from this machine."),
        (httpx.ReadError("reset"), "OKX could not be reached from this machine."),
        (httpx.RemoteProtocolError("garbled"), "OKX could not be reached from this machine."),
        (httpx.TooManyRedirects("loop"), "OKX could not be reached from this machine."),
        (httpx.InvalidURL("bad address"), "The OKX check could not be run."),
        (RuntimeError("the client is closed"), "The OKX check could not be run."),
    ],
)
def test_okx_not_answering(
    provider: FakeProvider, clock: FakeClock, error: Exception, detail: str
) -> None:
    provider.okx_error = error

    result = run_probe(provider, clock)

    assert result.status == "down"
    assert result.detail == detail
    assert result.latency_ms is None
    assert result.exchange_time is None


def test_the_timeout_in_the_message_is_the_one_in_use(
    provider: FakeProvider, clock: FakeClock
) -> None:
    provider.okx_error = httpx.ReadTimeout("timed out")

    result = run_probe(provider, clock, timeout_seconds=2.5)

    assert result.detail == "No answer from OKX within 2.5 seconds."


UNEXPECTED_BODIES: list[Any] = [
    "not json",
    "",
    "null",
    "[]",
    "{}",
    "12",
    '"text"',
    {"code": "0"},
    {"code": "0", "data": []},
    {"code": "0", "data": [{}]},
    {"code": "0", "data": [{"ts": None}]},
    {"code": "0", "data": [{"ts": "soon"}]},
    {"code": "0", "data": [{"ts": "1e3"}]},
    {"code": "0", "data": [{"ts": "12.5"}]},
    {"code": "0", "data": [{"ts": [1]}]},
    {"code": "0", "data": [{"ts": "9" * 400}]},
    {"code": "0", "data": [{"ts": "-" + "9" * 400}]},
    {"code": "0", "data": [{"ts": "99999999999999999999"}]},
    {"code": "0", "data": "text"},
    {"code": "0", "data": {"0": {"ts": "1"}}},
    {"code": "0", "data": None},
    {"data": [{"ts": "1"}]},
    [{"code": "0", "data": [{"ts": "1"}]}],
    '{"code": "0", "data": [{"ts": "1"}]' + " " * 5000 + "}",
    "[" * 3000 + "]" * 3000,
    b"\xff\xfe\x00\x01",
]


@pytest.mark.parametrize("body", UNEXPECTED_BODIES, ids=lambda body: repr(body)[:40])
def test_an_answer_in_an_unexpected_format(
    provider: FakeProvider, clock: FakeClock, body: Any
) -> None:
    provider.okx_body = lambda: body

    result = run_probe(provider, clock)

    assert result.status == "down"
    assert result.detail == "OKX answered in an unexpected format."
    assert result.latency_ms is not None
    assert result.exchange_time is None


@pytest.mark.parametrize(
    ("code", "shown"),
    [
        ("50001", "50001"),
        (50011, "50011"),
        ("1", "1"),
        ("1234567890", "1234567890"),
        ("12345678901", "unknown"),
        ("", "unknown"),
        ("-1", "unknown"),
        ("5 0", "unknown"),
        ("٥٠٠٠١", "unknown"),
        ("<script>alert(1)</script>", "unknown"),
        ("x" * 5000, "unknown"),
        (None, "unknown"),
        ({"nested": True}, "unknown"),
        (True, "unknown"),
    ],
)
def test_an_error_code_from_okx_is_shown_only_when_it_is_a_short_number(
    provider: FakeProvider, clock: FakeClock, code: Any, shown: str
) -> None:
    message = "<img src=x onerror=alert(1)> text from the exchange"
    provider.okx_body = lambda: {"code": code, "msg": message, "data": []}

    result = run_probe(provider, clock)

    if len(json.dumps({"code": code})) > okx_public.MAX_BODY_BYTES:
        assert result.detail == "OKX answered in an unexpected format."
    else:
        assert result.detail == f"OKX answered with error code {shown}."
    assert result.status == "down"
    assert "onerror" not in (result.detail or "")


@pytest.mark.parametrize(
    ("offset_seconds", "expected"),
    [(0, "ok"), (4, "ok"), (-4, "ok"), (6, "degraded"), (-6, "degraded"), (86_400, "degraded")],
)
def test_a_clock_that_differs_from_okx(
    provider: FakeProvider, clock: FakeClock, offset_seconds: int, expected: str
) -> None:
    provider.okx_time = lambda: clock() + timedelta(seconds=offset_seconds)

    async def scenario() -> MarketDataReachability:
        async with httpx.AsyncClient(transport=provider.transport()) as http:
            return await OkxPublicProbe(http, OKX_BASE, clock=clock).check()

    result = asyncio.run(scenario())

    assert result.status == expected
    assert result.clock_skew_ms is not None
    # Positive when this machine's clock is ahead of the exchange's.
    assert abs(result.clock_skew_ms + offset_seconds * 1000) < 1000
    if expected == "degraded":
        assert result.detail == "This machine's clock and OKX's differ by more than 5 seconds."
    else:
        assert result.detail is None


class SteppingTime:
    """Stands in for the `time` module: every reading is `step` seconds after the last."""

    def __init__(self, step: float):
        self.value = 1000.0
        self.step = step

    def perf_counter(self) -> float:
        value = self.value
        self.value += self.step
        return value

    def monotonic(self) -> float:
        return self.value


@pytest.mark.parametrize(
    ("seconds", "expected", "detail"),
    [
        (0.25, "ok", None),
        (2.0, "ok", None),
        (2.5, "degraded", "OKX answered, but slowly."),
        (7.0, "degraded", "OKX answered, but slowly."),
    ],
)
def test_a_slow_answer(
    provider: FakeProvider,
    clock: FakeClock,
    monkeypatch: pytest.MonkeyPatch,
    seconds: float,
    expected: str,
    detail: str | None,
) -> None:
    monkeypatch.setattr(okx_public, "time", SteppingTime(seconds))

    result = run_probe(provider, clock)

    assert result.latency_ms == seconds * 1000
    assert result.status == expected
    assert result.detail == detail


def test_the_answer_is_kept_for_ten_seconds_then_asked_again(
    provider: FakeProvider, clock: FakeClock, monkeypatch: pytest.MonkeyPatch
) -> None:
    moment = {"now": 500.0}
    fake_time = SimpleNamespace(monotonic=lambda: moment["now"], perf_counter=time.perf_counter)
    monkeypatch.setattr(okx_public, "time", fake_time)
    provider.okx_time = clock

    async def scenario() -> None:
        async with httpx.AsyncClient(transport=provider.transport()) as http:
            probe = OkxPublicProbe(http, OKX_BASE, clock=clock)

            first = await probe.check()
            moment["now"] += 9.9
            assert await probe.check() is first
            assert len(provider.requests) == 1

            moment["now"] += 0.2
            assert await probe.check() is not first
            assert len(provider.requests) == 2

    asyncio.run(scenario())


def test_a_failure_is_kept_as_long_as_a_success(
    provider: FakeProvider, clock: FakeClock, json_logs: LogCapture
) -> None:
    provider.okx_status = 403
    provider.okx_time = clock

    async def scenario() -> list[MarketDataReachability]:
        async with httpx.AsyncClient(transport=provider.transport()) as http:
            probe = OkxPublicProbe(http, OKX_BASE, clock=clock)
            return [await probe.check() for _ in range(5)]

    results = asyncio.run(scenario())

    assert {result.status for result in results} == {"down"}
    # OKX is not asked again and again while it refuses this machine.
    assert len(provider.requests) == 1
    assert json_logs.text.count("OKX public data check not ok") == 1


def test_nothing_is_kept_when_caching_is_off(provider: FakeProvider, clock: FakeClock) -> None:
    provider.okx_time = clock

    async def scenario() -> None:
        async with httpx.AsyncClient(transport=provider.transport()) as http:
            probe = OkxPublicProbe(http, OKX_BASE, clock=clock, cache_seconds=0)
            assert (await probe.check()).status == "ok"
            provider.okx_status = 503
            assert (await probe.check()).status == "down"
            provider.okx_status = 200
            assert (await probe.check()).status == "ok"

    asyncio.run(scenario())
    assert len(provider.requests) == 3


def test_an_unexpected_failure_is_logged_with_its_reason(
    provider: FakeProvider, clock: FakeClock, json_logs: LogCapture
) -> None:
    provider.okx_error = RuntimeError("the client is closed")

    result = run_probe(provider, clock)

    assert result.detail == "The OKX check could not be run."
    assert "OKX public data check could not be run" in json_logs.text
    assert "the client is closed" in json_logs.text


# -- build facts ------------------------------------------------------------------------------

COMMIT = "0123456789abcdef0123456789abcdef01234567"


def git_dir(tmp_path: Path, head: str) -> Path:
    directory = tmp_path / ".git"
    directory.mkdir()
    (directory / "HEAD").write_text(head, encoding="utf-8")
    return directory


def test_commit_of_a_detached_checkout(tmp_path: Path) -> None:
    assert build._read_head(git_dir(tmp_path, f"{COMMIT}\n")) == COMMIT[:12]


def test_commit_of_a_branch(tmp_path: Path) -> None:
    directory = git_dir(tmp_path, "ref: refs/heads/main\n")
    (directory / "refs" / "heads").mkdir(parents=True)
    (directory / "refs" / "heads" / "main").write_text(f"{COMMIT}\n", encoding="utf-8")

    assert build._read_head(directory) == COMMIT[:12]


def test_commit_of_a_packed_branch(tmp_path: Path) -> None:
    directory = git_dir(tmp_path, "ref: refs/heads/main\n")
    (directory / "packed-refs").write_text(
        f"# pack-refs with: peeled fully-peeled sorted\n{'f' * 40} refs/heads/other\n"
        f"{COMMIT} refs/heads/main\n",
        encoding="utf-8",
    )

    assert build._read_head(directory) == COMMIT[:12]


@pytest.mark.parametrize(
    "head",
    ["", "garbage", "ref: refs/heads/missing\n", "ZZZZZZZZZZZZ\n", "ref: ../../etc/hostname\n"],
)
def test_no_commit_when_the_checkout_says_nothing_usable(tmp_path: Path, head: str) -> None:
    assert build._read_head(git_dir(tmp_path, head)) is None


def test_no_commit_without_a_checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build, "_REPO_ROOT", tmp_path)

    assert build.resolve_commit(None) is None
    assert build.resolve_commit("") is None
    assert build.resolve_commit("   ") is None


def test_the_configured_commit_wins_over_the_checkout(tmp_path: Path) -> None:
    assert build.resolve_commit(f" {COMMIT} ") == COMMIT[:12]
    assert build.resolve_commit("abc1234") == "abc1234"
