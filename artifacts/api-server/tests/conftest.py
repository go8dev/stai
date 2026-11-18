"""Fixtures for the backend tests.

Database tests run against a throwaway PostgreSQL database that is created from the
migrations, so they never touch the development data. It lives on the development
PostgreSQL server and is dropped when the test run ends.
"""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.pool import NullPool
from starlette.testclient import TestClient

from stai.core import logging as stai_logging
from stai.core.config import (
    Settings,
    get_settings,
    known_variable_names,
    load_settings,
    normalise_database_url,
)
from stai.core.runtime import Runtime
from stai.db.session import Database
from stai.main import build_app
from stai.marketdata import provider as market_data_provider

from .support import (
    APP_HOST,
    APP_ORIGIN,
    CLIENT_ID,
    ISSUER,
    OKX_BASE,
    OWNER_ID,
    FakeClock,
    FakeProvider,
    generate_signing_key,
)

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parents[1]

_TABLES = (
    "market_snapshots",
    "paper_fills",
    "paper_positions",
    "bot_states",
    "trading_permits",
    "ledger_entries",
    "fund_allocations",
    "virtual_funds",
    "auth_sessions",
    "users",
    "audit_events",
)


def alembic_config(database_url: str) -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.attributes["database_url"] = database_url
    return config


def _server_url() -> URL:
    raw = os.environ.get("DATABASE_URL")
    if not raw:
        pytest.fail(
            "DATABASE_URL is not set. The backend tests create a throwaway database on the "
            "development PostgreSQL server and cannot run without it."
        )
    return make_url(normalise_database_url(raw))


class DatabaseFactory:
    """Creates throwaway databases on the development server and drops them afterwards."""

    def __init__(self) -> None:
        self._server = _server_url()
        self._admin = create_engine(self._server, isolation_level="AUTOCOMMIT", poolclass=NullPool)
        self._created: list[str] = []

    def create(self, *, migrated: bool) -> str:
        name = f"stai_test_{secrets.token_hex(6)}"
        with self._admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{name}"'))
        self._created.append(name)
        url = self._server.set(database=name).render_as_string(hide_password=False)
        if migrated:
            command.upgrade(alembic_config(url), "head")
        return url

    def close(self) -> None:
        with self._admin.connect() as connection:
            for name in self._created:
                connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        self._admin.dispose()


@pytest.fixture(scope="session")
def database_factory() -> Iterator[DatabaseFactory]:
    factory = DatabaseFactory()
    try:
        yield factory
    finally:
        factory.close()


@pytest.fixture(scope="session")
def database_url(database_factory: DatabaseFactory) -> str:
    """A database with the full structure, shared by the run and emptied before each test."""
    return database_factory.create(migrated=True)


@pytest.fixture(scope="session")
def _admin_engine(database_url: str) -> Iterator[Engine]:
    engine = create_engine(database_url, poolclass=NullPool)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def admin(_admin_engine: Engine) -> Engine:
    """An engine without the application's guards, on an emptied test database.

    Tests use it to look at rows directly and to tamper with them the way someone holding
    the database credentials could.
    """
    with _admin_engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {', '.join(_TABLES)}"))
    return _admin_engine


@pytest.fixture(scope="session")
def _signing_keys() -> tuple[Any, Any]:
    return generate_signing_key(), generate_signing_key()


@pytest.fixture
def provider(_signing_keys: tuple[Any, Any]) -> FakeProvider:
    return FakeProvider(*_signing_keys)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def make_settings(database_url: str | None, **overrides: str | None) -> Settings:
    """Settings as the published machine would have them, pointed at the fakes.

    Built from these values alone: nothing is read from the real environment.
    """
    values: dict[str, str | None] = {
        "DATABASE_URL": database_url,
        "REPL_ID": CLIENT_ID,
        "ISSUER_URL": ISSUER,
        "STAI_OWNER_USER_ID": OWNER_ID,
        "STAI_ALLOWED_HOSTS": APP_HOST,
        "STAI_OKX_BASE_URL": OKX_BASE,
    }
    values.update(overrides)
    return load_settings({key: value for key, value in values.items() if value})


@dataclass
class Harness:
    app: FastAPI
    client: TestClient
    provider: FakeProvider
    clock: FakeClock
    admin: Engine

    @property
    def runtime(self) -> Runtime:
        return self.app.state.runtime

    def new_client(self) -> TestClient:
        """Another browser: same app, empty cookie jar."""
        return TestClient(self.app, base_url=APP_ORIGIN, follow_redirects=False)


AppFactory = Callable[..., Harness]


@pytest.fixture
def make_harness(
    database_url: str, admin: Engine, provider: FakeProvider, clock: FakeClock
) -> Iterator[AppFactory]:
    """Build an app wired to the test database, the fake provider and the fake clock."""
    opened: list[tuple[TestClient, httpx.AsyncClient]] = []

    # The fake exchange keeps the same time as the app, so moving the clock adds no skew.
    provider.okx_time = clock

    def factory(*, use_database: bool = True, configure: Any = None, **settings: str | None):
        http = httpx.AsyncClient(transport=provider.transport())
        url = settings.pop("DATABASE_URL", database_url if use_database else None)
        app = build_app(make_settings(url, **settings), http_client=http, clock=clock)
        if configure is not None:
            configure(app)
        client = TestClient(app, base_url=APP_ORIGIN, follow_redirects=False)
        client.__enter__()
        opened.append((client, http))
        return Harness(app=app, client=client, provider=provider, clock=clock, admin=admin)

    try:
        yield factory
    finally:
        for client, http in reversed(opened):
            client.__exit__(None, None, None)
            asyncio.run(http.aclose())


@pytest.fixture
def harness(make_harness: AppFactory) -> Harness:
    return make_harness()


@pytest.fixture
def database(database_url: str, admin: Engine) -> Iterator[Database]:
    """The application's own database access, guards included, on the emptied test database."""
    db = Database(make_settings(database_url))
    try:
        yield db
    finally:
        db.dispose()


@pytest.fixture
def client(harness: Harness) -> TestClient:
    return harness.client


class LogCapture(logging.Handler):
    """Collects log lines exactly as the JSON formatter writes them."""

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.setFormatter(stai_logging.JsonFormatter())
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


_LIBRARY_LOGGERS = ("httpx", "httpcore", "sqlalchemy")


@pytest.fixture
def json_logs() -> Iterator[LogCapture]:
    """Everything the app would log at its most verbose setting, STAI_LOG_LEVEL=DEBUG."""
    capture = LogCapture()
    root = logging.getLogger()
    previous = root.level
    library_levels = {name: logging.getLogger(name).level for name in _LIBRARY_LOGGERS}
    root.addHandler(capture)
    root.setLevel(logging.DEBUG)
    stai_logging.quiet_library_loggers()
    try:
        yield capture
    finally:
        root.removeHandler(capture)
        root.setLevel(previous)
        for name, level in library_levels.items():
            logging.getLogger(name).setLevel(level)


@pytest.fixture
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """The process environment without any variable the settings read.

    For the few tests that go through the real environment. They set made-up values on
    the returned object, and everything is put back when the test ends.
    """
    for name in known_variable_names():
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    return monkeypatch


_LOGGERS_CHANGED_BY_CONFIGURE = ("uvicorn", "uvicorn.error", "uvicorn.access", *_LIBRARY_LOGGERS)


@pytest.fixture
def restored_logging() -> Iterator[None]:
    """Put the process's logging setup back after a test that calls `configure_logging`."""
    root = logging.getLogger()
    root_handlers, root_level = list(root.handlers), root.level
    saved = {
        name: (list(target.handlers), target.propagate, target.disabled, target.level)
        for name in _LOGGERS_CHANGED_BY_CONFIGURE
        for target in [logging.getLogger(name)]
    }
    try:
        yield
    finally:
        root.handlers[:] = root_handlers
        root.setLevel(root_level)
        for name, (handlers, propagate, disabled, level) in saved.items():
            target = logging.getLogger(name)
            target.handlers[:] = handlers
            target.propagate = propagate
            target.disabled = disabled
            target.setLevel(level)


@pytest.fixture(autouse=True)
def _isolate_process_state() -> Iterator[None]:
    """Keep process-wide state from leaking between tests."""
    yield
    stai_logging.clear_secret_values()
    stai_logging.set_correlation_id(None)
    get_settings.cache_clear()
    market_data_provider.set_market_data_provider(None)
