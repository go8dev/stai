"""Settings: which variables are read, what they default to and what is refused."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from stai import __main__ as server
from stai.core.config import (
    ConfigurationError,
    Settings,
    get_settings,
    known_variable_names,
    load_settings,
    normalise_database_url,
    secret_values_from_environment,
)

from .conftest import API_ROOT, REPO_ROOT

DOCUMENTED_VARIABLES = {
    "STAI_ENV",
    "REPLIT_DEPLOYMENT",
    "PORT",
    "STAI_LOG_LEVEL",
    "STAI_BUILD_COMMIT",
    "DATABASE_URL",
    "REPL_ID",
    "ISSUER_URL",
    "STAI_OWNER_USER_ID",
    "REPL_OWNER_ID",
    "STAI_SESSION_TTL_HOURS",
    "REPLIT_DOMAINS",
    "REPLIT_DEV_DOMAIN",
    "STAI_ALLOWED_HOSTS",
    "STAI_OKX_BASE_URL",
}

DATABASE_PASSWORD = "pw-that-must-not-be-shown"
DATABASE = f"postgresql://stai:{DATABASE_PASSWORD}@db.internal:5432/stai"


# -- which variables exist --------------------------------------------------------------------


def test_the_variables_read_are_exactly_the_documented_ones() -> None:
    assert known_variable_names() == DOCUMENTED_VARIABLES


def test_every_variable_is_described_in_the_environment_document() -> None:
    document = (REPO_ROOT / "docs" / "ENVIRONMENT.md").read_text(encoding="utf-8")

    missing = sorted(name for name in DOCUMENTED_VARIABLES if f"`{name}`" not in document)

    assert missing == []


# What the example file may show: nothing, a default of the code, or an obvious placeholder.
EXAMPLE_VALUES = {
    "",
    "8080",
    "INFO",
    "168",
    "https://replit.com/oidc",
    "https://www.okx.com",
    "postgresql://USER:PASSWORD@HOST:5432/DATABASE",
}


def example_assignments() -> dict[str, str]:
    """The `NAME=value` lines of docs/example.env that are not commented out."""
    assignments: dict[str, str] = {}
    text = (REPO_ROOT / "docs" / "example.env").read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name, separator, value = line.partition("=")
        assert separator, line
        assert name not in assignments, name
        assignments[name] = value
    return assignments


def test_the_example_environment_file_lists_exactly_the_documented_variables() -> None:
    assert set(example_assignments()) == DOCUMENTED_VARIABLES


def test_the_example_environment_file_holds_no_real_values() -> None:
    values = example_assignments()

    assert sorted(name for name, value in values.items() if value not in EXAMPLE_VALUES) == []
    # The defaults it shows are the defaults of the code, and the file is valid as written.
    defaults = load_settings({})
    assert values["STAI_LOG_LEVEL"] == defaults.log_level
    assert values["ISSUER_URL"] == defaults.issuer_url
    assert values["STAI_SESSION_TTL_HOURS"] == str(defaults.session_ttl_hours)
    assert values["STAI_OKX_BASE_URL"] == defaults.okx_base_url
    assert load_settings(values).port == 8080


def test_an_environment_file_is_never_read(
    clean_environment: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Settings come from the process environment only, so no file can carry a value in."""
    written = "STAI_ENV=development\nPORT=9999\nSTAI_OWNER_USER_ID=someone\nSTAI_LOG_LEVEL=DEBUG\n"
    for name in (".env", ".env.local", ".env.production"):
        (tmp_path / name).write_text(written, encoding="utf-8")
    secrets_directory = tmp_path / "secrets"
    secrets_directory.mkdir()
    (secrets_directory / "STAI_OWNER_USER_ID").write_text("someone", encoding="utf-8")
    clean_environment.chdir(tmp_path)

    for settings in (load_settings(), get_settings(), Settings()):
        assert settings.environment == "production"
        assert settings.port is None
        assert settings.owner_user_id is None
        assert settings.log_level == "INFO"
    assert Settings.model_config.get("env_file") is None
    assert Settings.model_config.get("secrets_dir") is None


def test_the_project_keeps_no_environment_file_and_no_code_that_loads_one() -> None:
    loaders = re.compile(r"load_dotenv|dotenv_values|find_dotenv|^\s*(from|import)\s+dotenv", re.M)
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in sorted((REPO_ROOT / "artifacts" / "api-server" / "stai").rglob("*.py"))
        if loaders.search(path.read_text(encoding="utf-8"))
    ]

    assert offenders == []
    for directory in (
        REPO_ROOT,
        REPO_ROOT / "artifacts" / "api-server",
        REPO_ROOT / "artifacts" / "stai",
    ):
        assert [path.name for path in directory.glob(".env*")] == []


def test_with_nothing_set_the_app_is_in_production_and_closed() -> None:
    settings = load_settings({})

    assert settings.environment == "production"
    assert settings.is_production is True
    assert settings.is_published is False
    assert settings.port is None
    assert settings.log_level == "INFO"
    assert settings.database_url is None
    assert settings.sqlalchemy_url is None
    assert settings.repl_id is None
    assert settings.owner_user_id is None
    assert settings.signin_configured is False
    assert settings.issuer_url == "https://replit.com/oidc"
    assert settings.session_ttl_hours == 168
    assert settings.okx_base_url == "https://www.okx.com"
    assert settings.allowed_hosts == frozenset()
    assert settings.build_commit is None


def test_empty_values_count_as_not_set() -> None:
    settings = load_settings(dict.fromkeys(DOCUMENTED_VARIABLES, ""))

    assert settings == load_settings({})


def test_names_must_match_exactly_and_unknown_ones_are_ignored() -> None:
    settings = load_settings(
        {
            "stai_env": "development",
            "Stai_Env": "development",
            "STAI_ENVIRONMENT": "development",
            "ENV": "development",
            "NODE_ENV": "development",
            "port": "8080",
            "STAI_LIVE_TRADING": "true",
        }
    )

    assert settings == load_settings({})


def test_settings_are_built_only_from_what_they_are_given(
    clean_environment: pytest.MonkeyPatch,
) -> None:
    clean_environment.setenv("STAI_ENV", "development")
    clean_environment.setenv("PORT", "9999")
    clean_environment.setenv("STAI_OWNER_USER_ID", "someone")

    # Neither the class nor an explicit mapping looks at the process environment.
    assert Settings().environment == "production"
    assert Settings().owner_user_id is None
    assert load_settings({}).port is None

    # Only the default call does, which is how the running app is configured.
    assert load_settings().environment == "development"
    assert load_settings().port == 9999
    assert get_settings().owner_user_id == "someone"


def test_settings_cannot_be_changed_after_they_are_built() -> None:
    settings = load_settings({})

    with pytest.raises(ValidationError):
        settings.stai_env = "development"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        settings.owner_user_id = "someone-else"  # type: ignore[misc]


# -- production unless development is asked for -----------------------------------------------


def test_development_must_be_asked_for_by_name() -> None:
    assert load_settings({"STAI_ENV": "development"}).is_production is False
    assert load_settings({"STAI_ENV": "production"}).is_production is True


@pytest.mark.parametrize(
    "value",
    ["dev", "Development", "DEVELOPMENT", " development", "development ", "staging", "test"]
    + ["prod", "Production", "local", "debug", "0", "false", "none"],
)
def test_any_other_environment_name_is_refused(value: str) -> None:
    with pytest.raises(ValidationError) as caught:
        load_settings({"STAI_ENV": value})

    assert "STAI_ENV" in str(caught.value)


def test_development_is_refused_on_the_published_machine() -> None:
    with pytest.raises(ConfigurationError, match="not allowed on a published machine"):
        load_settings({"STAI_ENV": "development", "REPLIT_DEPLOYMENT": "1"})


def test_the_published_machine_runs_in_production() -> None:
    for env in ({"REPLIT_DEPLOYMENT": "1"}, {"REPLIT_DEPLOYMENT": "1", "STAI_ENV": "production"}):
        settings = load_settings(env)
        assert settings.is_published is True
        assert settings.is_production is True


@pytest.mark.parametrize("value", ["0", "true", "yes", "2", " 1", "1 "])
def test_only_the_value_replit_sets_marks_a_published_machine(value: str) -> None:
    settings = load_settings({"REPLIT_DEPLOYMENT": value, "STAI_ENV": "development"})

    assert settings.is_published is False


# -- single values ----------------------------------------------------------------------------


@pytest.mark.parametrize(("value", "expected"), [("1", 1), ("8080", 8080), ("65535", 65535)])
def test_a_valid_port(value: str, expected: int) -> None:
    assert load_settings({"PORT": value}).port == expected


@pytest.mark.parametrize("value", ["0", "-1", "65536", "abc", "80.5", "8080;rm"])
def test_an_invalid_port_is_refused(value: str) -> None:
    with pytest.raises(ValidationError):
        load_settings({"PORT": value})


@pytest.mark.parametrize(
    ("value", "expected"),
    [("debug", "DEBUG"), (" Warning ", "WARNING"), ("ERROR", "ERROR"), ("critical", "CRITICAL")],
)
def test_the_log_level_is_normalised(value: str, expected: str) -> None:
    assert load_settings({"STAI_LOG_LEVEL": value}).log_level == expected


@pytest.mark.parametrize("value", ["verbose", "trace", "10", "INFO,DEBUG", "NOTSET"])
def test_an_unknown_log_level_is_refused(value: str) -> None:
    with pytest.raises(ValidationError):
        load_settings({"STAI_LOG_LEVEL": value})


@pytest.mark.parametrize("name", ["ISSUER_URL", "STAI_OKX_BASE_URL"])
def test_outside_addresses_must_be_https(name: str) -> None:
    assert load_settings({name: " https://example.test/base/ "}).model_dump()[
        "issuer_url" if name == "ISSUER_URL" else "okx_base_url"
    ] == ("https://example.test/base")

    for value in ("http://example.test", "example.test", "ftp://example.test", "//example.test"):
        with pytest.raises(ValidationError):
            load_settings({name: value})


@pytest.mark.parametrize(("value", "expected"), [("1", 1), ("24", 24), ("2160", 2160)])
def test_a_valid_session_length(value: str, expected: int) -> None:
    assert load_settings({"STAI_SESSION_TTL_HOURS": value}).session_ttl_hours == expected


@pytest.mark.parametrize("value", ["0", "-5", "2161", "forever", "1.5"])
def test_a_session_length_out_of_range_is_refused(value: str) -> None:
    with pytest.raises(ValidationError):
        load_settings({"STAI_SESSION_TTL_HOURS": value})


def test_text_values_are_trimmed_and_blank_ones_dropped() -> None:
    settings = load_settings(
        {"REPL_ID": "  client-1  ", "STAI_BUILD_COMMIT": " abc1234 ", "STAI_OWNER_USER_ID": "\t"}
    )

    assert settings.repl_id == "client-1"
    assert settings.build_commit == "abc1234"
    assert settings.owner_user_id is None


# -- who the owner is -------------------------------------------------------------------------


def test_the_owner_is_the_workspace_owner_by_default() -> None:
    settings = load_settings({"REPL_OWNER_ID": "12345", "REPL_ID": "client-1"})

    assert settings.owner_user_id == "12345"
    assert settings.signin_configured is True


def test_an_explicit_owner_wins_over_the_workspace_owner() -> None:
    settings = load_settings({"REPL_OWNER_ID": "12345", "STAI_OWNER_USER_ID": " 67890 "})

    assert settings.owner_user_id == "67890"


def test_a_blank_explicit_owner_does_not_fall_back_to_anyone() -> None:
    """Set but blank is a mistake to fix, not a reason to pick another account."""
    settings = load_settings({"REPL_OWNER_ID": "12345", "STAI_OWNER_USER_ID": "   "})

    assert settings.owner_user_id is None
    assert settings.signin_configured is False


def test_sign_in_needs_both_the_client_and_the_owner() -> None:
    assert load_settings({"REPL_ID": "client-1"}).signin_configured is False
    assert load_settings({"REPL_OWNER_ID": "12345"}).signin_configured is False
    assert load_settings({"REPL_ID": "c", "REPL_OWNER_ID": "1"}).signin_configured is True


# -- the database address ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("postgresql://u:p@h:5432/d", "postgresql+psycopg://u:p@h:5432/d"),
        ("postgres://u:p@h/d?sslmode=require", "postgresql+psycopg://u:p@h/d?sslmode=require"),
        ("postgresql+psycopg://u:p@h/d", "postgresql+psycopg://u:p@h/d"),
    ],
)
def test_the_database_address_is_pointed_at_the_driver_in_use(url: str, expected: str) -> None:
    assert load_settings({"DATABASE_URL": url}).sqlalchemy_url == expected
    assert normalise_database_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "mysql://u:p@h/d",
        "sqlite:///stai.db",
        "postgresql+psycopg2://u:p@h/d",
        "postgresql+asyncpg://u:p@h/d",
        "POSTGRESQL://u:p@h/d",
        " postgresql://u:p@h/d",
        "h:5432/d",
    ],
)
def test_any_other_database_address_is_refused(url: str) -> None:
    with pytest.raises(ValidationError) as caught:
        load_settings({"DATABASE_URL": url})
    assert "DATABASE_URL" in str(caught.value)

    with pytest.raises(ConfigurationError):
        normalise_database_url(url)


def test_the_database_address_never_appears_when_settings_are_printed() -> None:
    settings = load_settings({"DATABASE_URL": DATABASE})

    for shown in (repr(settings), str(settings), repr(settings.model_dump()), f"{settings}"):
        assert DATABASE_PASSWORD not in shown
        assert "db.internal" not in shown
    assert DATABASE_PASSWORD not in settings.model_dump_json()
    # It is only available when asked for by name.
    assert settings.sqlalchemy_url == DATABASE.replace("postgresql://", "postgresql+psycopg://")


@pytest.mark.parametrize(
    "env",
    [
        {"DATABASE_URL": f"mysql://stai:{DATABASE_PASSWORD}@db.internal/stai"},
        {"PORT": DATABASE_PASSWORD},
        {"STAI_ENV": DATABASE_PASSWORD},
        {"STAI_LOG_LEVEL": DATABASE_PASSWORD},
        {"ISSUER_URL": f"http://user:{DATABASE_PASSWORD}@idp.test"},
        {"STAI_SESSION_TTL_HOURS": DATABASE_PASSWORD},
    ],
)
def test_a_refused_value_is_not_repeated_in_the_error(env: dict[str, str]) -> None:
    with pytest.raises(ValidationError) as caught:
        load_settings(env)

    assert DATABASE_PASSWORD not in str(caught.value)
    assert DATABASE_PASSWORD not in repr(caught.value)
    assert next(iter(env)) in str(caught.value)


# -- hosts the app is served from -------------------------------------------------------------


def hosts(**env: str) -> Settings:
    return load_settings(env)


def test_allowed_hosts_come_from_three_variables() -> None:
    settings = hosts(
        REPLIT_DOMAINS="stai.example.replit.app, STAI.Example.com ,,",
        REPLIT_DEV_DOMAIN="abc-00-xyz.pike.replit.dev",
        STAI_ALLOWED_HOSTS=" extra.test ",
    )

    assert settings.allowed_hosts == {
        "stai.example.replit.app",
        "stai.example.com",
        "abc-00-xyz.pike.replit.dev",
        "extra.test",
    }


@pytest.mark.parametrize(
    ("host", "allowed"),
    [
        ("stai.example.com", True),
        ("STAI.EXAMPLE.COM", True),
        (" stai.example.com ", True),
        ("stai.example.com:443", True),
        ("stai.example.com:8080", True),
        ("evil-stai.example.com", False),
        ("stai.example.com.evil.test", False),
        ("evil.test/stai.example.com", False),
        ("stai.example.com@evil.test", False),
        ("stai.example.com:443:80", False),
        ("example.com", False),
        ("localhost", False),
        ("127.0.0.1:8080", False),
        ("", False),
        (None, False),
        (":", False),
        (",", False),
    ],
)
def test_only_listed_hosts_are_accepted_in_production(host: str | None, allowed: bool) -> None:
    settings = hosts(REPLIT_DOMAINS="stai.example.com")

    assert settings.is_allowed_host(host) is allowed


def test_no_host_is_accepted_when_none_is_listed() -> None:
    settings = load_settings({})

    for host in ("localhost", "127.0.0.1", "stai.example.com", "", "*"):
        assert settings.is_allowed_host(host) is False


@pytest.mark.parametrize(
    ("host", "allowed"),
    [
        ("localhost", True),
        ("localhost:8080", True),
        ("127.0.0.1:5173", True),
        ("LOCALHOST:8080", True),
        ("localhost.evil.test", False),
        ("evil.test", False),
        ("0.0.0.0", False),  # noqa: S104
        ("[::1]:8080", False),
    ],
)
def test_this_machine_is_accepted_only_in_development(host: str, allowed: bool) -> None:
    assert hosts(STAI_ENV="development").is_allowed_host(host) is allowed
    assert hosts().is_allowed_host(host) is False


# -- values to keep out of logs ---------------------------------------------------------------


def test_secret_looking_variables_are_collected_for_masking() -> None:
    env = {
        "DATABASE_URL": "postgresql://stai:p%40ss%2Fword@db.internal/stai",
        "PGPASSWORD": "pg-password-value",
        "SESSION_SECRET": "session-secret-value",
        "OPENAI_API_KEY": "sk-test-value",
        "STAI_ALERT_EMAIL": "owner@example.test",
        "GITHUB_TOKEN": "token-value",
        "SOME_PRIVATE_KEY": "private-key-value",
        "EMPTY_SECRET": "",
        "PATH": "/usr/bin",
        "HOME": "/home/runner",
        "REPL_OWNER_ID": "12345",
    }

    values = secret_values_from_environment(env)

    assert set(values) == {
        "postgresql://stai:p%40ss%2Fword@db.internal/stai",
        # The password as written in the address and as the database receives it.
        "p%40ss%2Fword",
        "p@ss/word",
        "pg-password-value",
        "session-secret-value",
        "sk-test-value",
        "owner@example.test",
        "token-value",
        "private-key-value",
    }


@pytest.mark.parametrize("url", ["not a url", "postgresql://db.internal/stai", "http://[bad"])
def test_a_database_address_without_a_password_adds_only_itself(url: str) -> None:
    assert secret_values_from_environment({"DATABASE_URL": url}) == [url]


def test_a_plain_database_password_is_collected_once() -> None:
    url = "postgresql://stai:plain-password@db.internal/stai"

    assert secret_values_from_environment({"DATABASE_URL": url}) == [url, "plain-password"]


# -- python -m stai ---------------------------------------------------------------------------


@pytest.fixture
def start(clean_environment: pytest.MonkeyPatch):
    """Run the server's entry point with the given environment, without starting a server."""
    started: list[dict[str, Any]] = []

    def fake_run(app: str, **options: Any) -> None:
        started.append({"app": app, **options})

    clean_environment.setattr(server.uvicorn, "run", fake_run)
    # The entry point configures logging; keep the test run's own handlers.
    clean_environment.setattr(server, "configure_logging", lambda level: None)
    # The claim on the port is tested below with a directory of its own. Here it is always
    # granted, so these tests do not depend on what else runs on this machine.
    clean_environment.setattr(server, "claim_port", lambda port: server.PortClaim(None))

    def run(*args: str, **env: str) -> tuple[int, list[dict[str, Any]]]:
        for name, value in env.items():
            clean_environment.setenv(name, value)
        get_settings.cache_clear()
        return server.main(list(args)), started

    return run


def test_the_server_starts_on_the_given_port(start: Any) -> None:
    code, started = start(PORT="8080")

    assert code == 0
    (options,) = started
    assert options["app"] == "stai.main:create_app"
    assert options["factory"] is True
    assert options["port"] == 8080
    assert options["host"] == "0.0.0.0"  # noqa: S104
    assert options["reload"] is False
    assert options["reload_dirs"] is None
    # STAI writes its own access log without query strings, and trusts no forwarded header.
    assert options["access_log"] is False
    assert options["proxy_headers"] is False
    assert options["server_header"] is False
    assert options["log_config"] is None


def test_reload_is_available_in_development(start: Any) -> None:
    code, started = start("--reload", PORT="8080", STAI_ENV="development")

    assert code == 0
    assert started[0]["reload"] is True
    assert len(started[0]["reload_dirs"]) == 1
    assert started[0]["reload_dirs"][0].endswith("artifacts/api-server/stai")


@pytest.mark.parametrize(
    ("args", "env", "message"),
    [
        ((), {}, "STAI cannot start: PORT is not set."),
        (
            ("--reload",),
            {"PORT": "8080"},
            "STAI cannot start: --reload needs STAI_ENV=development.",
        ),
        (
            ("--reload",),
            {"PORT": "8080", "STAI_ENV": "production"},
            "STAI cannot start: --reload needs STAI_ENV=development.",
        ),
        (
            (),
            {"PORT": "8080", "STAI_ENV": "development", "REPLIT_DEPLOYMENT": "1"},
            "STAI cannot start: STAI_ENV=development is not allowed on a published machine "
            "(REPLIT_DEPLOYMENT=1). Remove STAI_ENV or set it to production.",
        ),
    ],
)
def test_the_server_refuses_to_start_and_says_why(
    start: Any,
    capsys: pytest.CaptureFixture[str],
    args: tuple[str, ...],
    env: dict[str, str],
    message: str,
) -> None:
    code, started = start(*args, **env)

    assert code == 2
    assert started == []
    assert capsys.readouterr().err.strip() == message


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("STAI_ENV", "staging-value-not-to-repeat"),
        ("PORT", "port-value-not-to-repeat"),
        ("DATABASE_URL", "mysql://user:value-not-to-repeat@host/db"),
        ("STAI_LOG_LEVEL", "level-value-not-to-repeat"),
    ],
)
def test_a_refused_setting_is_named_without_its_value(
    start: Any, capsys: pytest.CaptureFixture[str], name: str, value: str
) -> None:
    code, started = start(**{"PORT": "8080", name: value})

    assert code == 2
    assert started == []
    error = capsys.readouterr().err
    assert error.startswith(f"STAI cannot start: {name}: ")
    assert "not-to-repeat" not in error
    assert len(error.strip().splitlines()) == 1


def test_a_second_backend_on_a_taken_port_refuses_to_start(
    start: Any, clean_environment: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    asked: list[int] = []

    def taken(port: int) -> None:
        asked.append(port)

    code, started = start(PORT="8080")
    assert code == 0 and len(started) == 1

    clean_environment.setattr(server, "claim_port", taken)
    code, started = start(PORT="8081")

    assert code == 2
    assert asked == [8081]
    assert len(started) == 1  # no second server was started
    assert capsys.readouterr().err.strip() == (
        "STAI cannot start: another STAI backend is already running on port 8081."
    )


# -- the claim on the port --------------------------------------------------------------------


def test_only_one_backend_can_claim_a_port(tmp_path: Path) -> None:
    first = server.claim_port(8080, directory=tmp_path, wait_seconds=0)
    assert first is not None
    try:
        assert server.claim_port(8080, directory=tmp_path, wait_seconds=0) is None
        # Another port is another claim.
        other = server.claim_port(8081, directory=tmp_path, wait_seconds=0)
        assert other is not None
        other.close()
    finally:
        first.close()


def test_the_port_can_be_claimed_again_once_it_is_released(tmp_path: Path) -> None:
    first = server.claim_port(8080, directory=tmp_path, wait_seconds=0)
    assert first is not None
    first.close()
    first.close()  # closing twice is harmless

    second = server.claim_port(8080, directory=tmp_path, wait_seconds=0)
    assert second is not None
    second.close()


def test_a_starting_backend_waits_for_the_previous_one_to_finish(tmp_path: Path) -> None:
    previous = server.claim_port(8080, directory=tmp_path, wait_seconds=0)
    assert previous is not None
    waits: list[float] = []

    def previous_backend_exits(seconds: float) -> None:
        waits.append(seconds)
        previous.close()

    claim = server.claim_port(
        8080, directory=tmp_path, wait_seconds=30, sleep=previous_backend_exits
    )

    assert claim is not None
    assert len(waits) == 1
    claim.close()


def test_a_backend_gives_up_when_the_port_stays_claimed(tmp_path: Path) -> None:
    holder = server.claim_port(8080, directory=tmp_path, wait_seconds=0)
    assert holder is not None
    waits: list[float] = []
    try:
        assert (
            server.claim_port(8080, directory=tmp_path, wait_seconds=0.05, sleep=waits.append)
            is None
        )
    finally:
        holder.close()
    # It kept trying for the whole wait, and the holder's claim is untouched.
    assert waits
    assert server.claim_port(8080, directory=tmp_path, wait_seconds=0) is not None


def test_a_claim_ends_with_the_process_that_holds_it(tmp_path: Path) -> None:
    script = (
        "import sys; from pathlib import Path; from stai.__main__ import claim_port; "
        "claim = claim_port(8080, directory=Path(sys.argv[1]), wait_seconds=0); "
        "print('claimed' if claim is not None else 'refused')"
    )

    settings = known_variable_names()
    environment = {name: value for name, value in os.environ.items() if name not in settings}

    def run_in_another_process() -> str:
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-c", script, str(tmp_path)],
            cwd=API_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        return result.stdout.strip()

    # The first process ended without closing its claim. The next one still gets the port.
    assert run_in_another_process() == "claimed"
    assert run_in_another_process() == "claimed"

    held = server.claim_port(8080, directory=tmp_path, wait_seconds=0)
    assert held is not None
    try:
        assert run_in_another_process() == "refused"
    finally:
        held.close()


def test_the_backend_starts_without_a_claim_when_the_directory_is_unusable(tmp_path: Path) -> None:
    claim = server.claim_port(8080, directory=tmp_path / "missing", wait_seconds=0)

    assert claim is not None
    claim.close()
