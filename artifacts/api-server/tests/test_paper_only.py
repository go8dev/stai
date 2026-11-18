"""Paper trading only: no live switch, no exchange credentials, nothing that places an order.

These tests read the code, the settings, the routes, the tables and the dependency list.
They fail when someone adds the thing the owner ruled out, even by accident.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import tomllib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.routing import iter_route_contexts

from stai.core.config import Settings, known_variable_names, load_settings
from stai.db.base import Base
from stai.marketdata.okx_market import MARKET_PATHS
from stai.marketdata.okx_public import TIME_PATH
from stai.marketdata.provider import MarketDataProvider
from stai.system.schemas import SystemStatus, TradingMode
from stai.trading.bots import build_bot_config

from .conftest import API_ROOT, REPO_ROOT, AppFactory, Harness
from .support import OKX_BASE, csrf_headers, sign_in

BACKEND = API_ROOT / "stai"
WEB_SOURCES = [
    REPO_ROOT / "artifacts" / "stai" / "src",
    REPO_ROOT / "artifacts" / "stai" / "index.html",
    REPO_ROOT / "lib" / "api-client-react" / "src",
    REPO_ROOT / "lib" / "api-zod" / "src",
    REPO_ROOT / "lib" / "replit-auth-web" / "src",
]
WEB_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".css", ".html", ".json"}


def backend_files() -> list[Path]:
    files = sorted(BACKEND.rglob("*.py"))
    assert len(files) > 40, "the backend sources were not found"
    return files


def web_files() -> list[Path]:
    files: list[Path] = []
    for source in WEB_SOURCES:
        assert source.exists(), source
        candidates = [source] if source.is_file() else sorted(source.rglob("*"))
        files += [path for path in candidates if path.is_file() and path.suffix in WEB_SUFFIXES]
    assert len(files) > 20, "the web sources were not found"
    return files


def occurrences(files: list[Path], pattern: str) -> list[str]:
    """Where a pattern appears, as `path:line`, ignoring case."""
    expression = re.compile(pattern, re.IGNORECASE)
    found: list[str] = []
    for path in files:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if expression.search(line):
                found.append(f"{path.relative_to(REPO_ROOT)}:{number}")
    return found


def imported_modules(path: Path) -> Iterator[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module
            for alias in node.names:
                yield f"{node.module}.{alias.name}"


def test_the_scans_below_really_read_the_code() -> None:
    """A scan that finds nothing proves something only if it can find what is there."""
    assert occurrences(backend_files(), r"/api/v5/public/time") == [
        "artifacts/api-server/stai/marketdata/okx_public.py:24"
    ]
    assert occurrences(backend_files(), r"tradingMode=\"paper\"")
    assert occurrences(web_files(), r"No real money moves")
    assert any(path.name == "api.ts" for path in web_files())
    assert "httpx" in set(imported_modules(BACKEND / "marketdata" / "okx_public.py"))
    assert "stai.core.time.utcnow" in set(imported_modules(BACKEND / "main.py"))


# -- one mode ---------------------------------------------------------------------------------


def test_paper_is_the_only_trading_mode() -> None:
    assert [mode.value for mode in TradingMode] == ["paper"]
    assert SystemStatus.model_fields["trading_mode"].annotation is TradingMode


def test_the_contract_offers_no_other_mode() -> None:
    contract = yaml.safe_load(
        (REPO_ROOT / "lib" / "api-spec" / "openapi.yaml").read_text(encoding="utf-8")
    )

    assert contract["components"]["schemas"]["TradingMode"]["enum"] == ["paper"]
    generated = (
        REPO_ROOT / "lib" / "api-client-react" / "src" / "generated" / "api.schemas.ts"
    ).read_text(encoding="utf-8")
    block = re.search(r"export const TradingMode = \{(.*?)\} as const", generated, re.DOTALL)
    assert block is not None
    assert block.group(1).split() == ["paper:", "'paper',"]


SWITCH_ATTEMPTS = {
    "STAI_TRADING_MODE": "live",
    "TRADING_MODE": "live",
    "STAI_MODE": "live",
    "STAI_LIVE": "1",
    "LIVE_TRADING": "true",
    "STAI_LIVE_TRADING": "true",
    "DRY_RUN": "false",
    "STAI_PAPER": "false",
    "OKX_API_KEY": "made-up",
    "OKX_SECRET_KEY": "made-up",
    "OKX_PASSPHRASE": "made-up",
}


def test_no_environment_variable_switches_the_mode(make_harness: AppFactory) -> None:
    assert load_settings(SWITCH_ATTEMPTS) == load_settings({})

    harness = make_harness(**SWITCH_ATTEMPTS)
    sign_in(harness.client, harness.provider)

    assert harness.client.get("/api/system/status").json()["tradingMode"] == "paper"


@pytest.mark.parametrize("environment", ["development", "production"])
def test_the_status_reports_paper_in_every_environment(
    make_harness: AppFactory, environment: str
) -> None:
    harness = make_harness(STAI_ENV=environment)
    sign_in(harness.client, harness.provider)

    assert harness.client.get("/api/system/status").json()["tradingMode"] == "paper"


# -- no credentials ---------------------------------------------------------------------------

CREDENTIAL_OR_SWITCH = re.compile(
    r"KEY|SECRET|PASSPHRASE|PASSWORD|TOKEN|CREDENTIAL|LIVE|TRADING|MODE|DRY|PAPER", re.IGNORECASE
)


def test_no_setting_holds_an_exchange_credential_or_a_mode_switch() -> None:
    names = sorted(known_variable_names() | set(Settings.model_fields))

    assert [name for name in names if CREDENTIAL_OR_SWITCH.search(name)] == []


def test_no_table_could_hold_an_exchange_credential() -> None:
    assert set(Base.metadata.tables) == {
        "users",
        "auth_sessions",
        "audit_events",
        "virtual_funds",
        "fund_allocations",
        "ledger_entries",
        "market_snapshots",
        "bot_states",
        "trading_permits",
        "paper_positions",
        "paper_fills",
    }

    suspicious = re.compile(r"api_?key|secret|passphrase|password|credential|exchange", re.I)
    columns = [
        f"{table.name}.{column.name}"
        for table in Base.metadata.tables.values()
        for column in table.columns
    ]

    assert [name for name in columns if suspicious.search(name)] == []


def test_bots_use_public_exchange_data_without_credentials() -> None:
    for bot_type in ("spot", "futures"):
        config = build_bot_config(bot_type)
        exchange = config["exchange"]
        assert isinstance(exchange, dict)
        assert set(exchange) == {"name", "pair_whitelist", "pair_blacklist"}
        assert config["dry_run"] is True
        assert config["api_server"] == {"enabled": False}
        assert config["telegram"] == {"enabled": False}


@pytest.mark.parametrize(
    "pattern",
    [
        r"passphrase",
        r"api[_ -]?secret",
        r"secret[_ -]?key",
        r"api[_ -]?key",
        r"OK-ACCESS",
        r"type=[\"']password[\"']",
    ],
)
def test_the_web_app_has_no_field_for_keys_or_passwords(pattern: str) -> None:
    assert occurrences(web_files(), pattern) == []


# -- no orders --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "pattern",
    [
        r"(create|place|submit|send|cancel|amend|modify|edit|execute)_(market_|limit_)?orders?\b",
        r"batch[_-]orders",
        r"close[_-]positions?",
        r"set[_-]leverage",
        r"withdraw",
        r"live[_-]?trading",
        r"enable[_-]?live",
        r"\bis[_-]live\b",
        r"set_sandbox_mode",
    ],
)
def test_the_backend_has_no_code_that_places_or_changes_an_order(pattern: str) -> None:
    assert occurrences(backend_files(), pattern) == []


@pytest.mark.parametrize(
    "pattern",
    [
        r"live[_ -]?trading",
        r"live[_ -]?mode",
        r"go(ing)? live",
        r"enable live",
        r"place[_ -]?order",
        r"submit[_ -]?order",
    ],
)
def test_the_web_app_offers_no_live_switch_or_order_button(pattern: str) -> None:
    assert occurrences(web_files(), pattern) == []


def test_okx_is_only_ever_asked_for_public_data() -> None:
    assert TIME_PATH == "/api/v5/public/time"

    paths: list[str] = []
    for path in backend_files():
        paths += re.findall(r"/api/v5/[A-Za-z0-9/_-]*", path.read_text(encoding="utf-8"))

    assert set(paths) == {
        "/api/v5/public/time",
        "/api/v5/market/ticker",
        "/api/v5/market/candles",
        "/api/v5/market/books",
        "/api/v5/public/instruments",
        "/api/v5/public/funding-rate",
    }
    assert set(paths) - {"/api/v5/public/time"} == set(MARKET_PATHS)
    # Private OKX paths start with trade, account, asset and the like. None may appear.
    assert all(re.match(r"/api/v5/(public|market)/", found) for found in paths)


def test_the_market_data_interface_can_only_read() -> None:
    methods = {
        name
        for name, member in vars(MarketDataProvider).items()
        if callable(member) and not name.startswith("_")
    }

    assert methods == {"get_ticker", "get_candles"}


def test_the_app_has_one_state_changing_route_and_it_is_not_about_orders(
    harness: Harness,
) -> None:
    routes = {
        (method, route.path)
        for route in iter_route_contexts(harness.app.routes)
        for method in route.methods or ()
    }

    changing = {route for route in routes if route[0] not in {"GET", "HEAD", "OPTIONS"}}
    # A new state-changing route has to be added here on purpose.
    assert changing == {("POST", "/api/audit/verify")}
    words = re.compile(r"order|trade|position|withdraw|transfer|credential|key|live|exchange")
    assert [path for _, path in sorted(routes) if words.search(path)] == []


# -- what leaves the machine ------------------------------------------------------------------

NETWORK_OR_PROCESS_MODULES = (
    "requests",
    "aiohttp",
    "urllib3",
    "urllib.request",
    "http.client",
    "websockets",
    "websocket",
    "socket",
    "smtplib",
    "ftplib",
    "tradingagents",
    "okx",
    "binance",
    "openai",
)


def test_outside_calls_can_only_come_from_the_known_places() -> None:
    uses_httpx: set[str] = set()
    forbidden: list[str] = []
    for path in backend_files():
        relative = str(path.relative_to(API_ROOT))
        for module in imported_modules(path):
            if module == "httpx" or module.startswith("httpx."):
                uses_httpx.add(relative)
            for banned in NETWORK_OR_PROCESS_MODULES:
                if module == banned or module.startswith(f"{banned}."):
                    forbidden.append(f"{relative} imports {module}")

    assert forbidden == []
    # The client is built in main, carried by runtime, and used by the public-data adapters.
    assert uses_httpx == {
        "stai/main.py",
        "stai/core/runtime.py",
        "stai/auth/oidc.py",
        "stai/marketdata/okx_public.py",
        "stai/marketdata/okx_market.py",
    }
    assert "subprocess" in set(imported_modules(BACKEND / "trading" / "bots.py"))
    assert "freqtrade.strategy" in set(
        imported_modules(BACKEND / "trading" / "freqtrade_strategy.py")
    )


def test_the_only_request_that_sends_data_out_is_the_sign_in_token_exchange() -> None:
    files = backend_files()
    sending = r"\bawait\s+[\w.]+\.(post|put|patch|delete|request|send|stream)\("
    reading = r"\bawait\s+[\w.]*http[\w.]*\.get\("

    assert [where.rsplit(":", 1)[0] for where in occurrences(files, sending)] == [
        "artifacts/api-server/stai/auth/oidc.py"
    ]
    assert [where.rsplit(":", 1)[0] for where in occurrences(files, reading)] == [
        "artifacts/api-server/stai/auth/oidc.py",
        "artifacts/api-server/stai/marketdata/okx_market.py",
        "artifacts/api-server/stai/marketdata/okx_public.py",
    ]


def test_using_the_whole_app_sends_okx_nothing_but_the_public_time_request(
    harness: Harness,
) -> None:
    client, provider = harness.client, harness.provider

    sign_in(client, provider)
    for _ in range(3):
        assert client.get("/api/system/status").status_code == 200
    assert client.get("/api/audit/events").status_code == 200
    assert client.post("/api/audit/verify", headers=csrf_headers(client)).status_code == 200
    assert client.get("/api/logout").status_code == 302

    to_okx = provider.calls_to(OKX_BASE)
    assert to_okx
    for request in to_okx:
        assert request.method == "GET"
        assert str(request.url) == f"{OKX_BASE}/api/v5/public/time"
        assert request.content == b""
        sent = {name.lower() for name in request.headers}
        assert sent <= {"host", "accept", "accept-encoding", "connection", "user-agent"}
    # Nothing but the identity provider and OKX was contacted at all.
    hosts = {request.url.host for request in provider.requests}
    assert hosts == {"idp.test", "okx.test"}


# -- the approved trading engines stay paper-only ---------------------------------------------

EXCHANGE_AND_ENGINE_PACKAGES = {
    "tradingagents",
    "python-okx",
    "okx",
    "python-binance",
    "binance-connector",
    "pybit",
    "langgraph",
    "langchain",
    "openai",
    "anthropic",
}


def package_name(requirement: str) -> str:
    return re.split(r"[\s\[<>=!~;]", requirement, maxsplit=1)[0].lower().replace("_", "-")


def test_phase_two_declares_and_locks_only_approved_engine_libraries() -> None:
    """Phase 2 uses fixed Freqtrade and CCXT versions; later AI packages stay absent."""
    project: dict[str, Any] = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    declared = {package_name(item) for item in project["project"]["dependencies"]}
    for group in project.get("dependency-groups", {}).values():
        declared |= {package_name(item) for item in group if isinstance(item, str)}

    lock = tomllib.loads((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked = {package["name"].lower() for package in lock["package"]}

    assert {"ccxt", "freqtrade"} <= declared
    assert {"ccxt", "freqtrade"} <= declared
    assert {"ccxt", "freqtrade", "freqtrade-client", "ta-lib"} <= locked
    assert declared & EXCHANGE_AND_ENGINE_PACKAGES == set()
    assert locked & EXCHANGE_AND_ENGINE_PACKAGES == set()
    assert declared - {"stai"} <= locked


def test_phase_two_engines_are_installed_and_ai_libraries_are_not() -> None:
    assert importlib.util.find_spec("ccxt") is not None
    assert importlib.util.find_spec("freqtrade") is not None
    for module in ("tradingagents", "okx", "binance", "langgraph", "openai"):
        assert importlib.util.find_spec(module) is None
