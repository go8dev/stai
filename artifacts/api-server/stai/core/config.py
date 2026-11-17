"""Settings, read from environment variables only.

Nothing here is a default for a secret, and there is no setting for exchange API keys:
STAI is paper trading only and uses public market-data endpoints.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from functools import lru_cache
from typing import Literal
from urllib.parse import unquote, urlsplit

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

Environment = Literal["development", "production"]

_LOCAL_HOSTS = ("localhost", "127.0.0.1")


class ConfigurationError(RuntimeError):
    """The environment is set up in a way STAI refuses to run with."""


class Settings(BaseSettings):
    """Values the backend reads from its environment. See docs/ENVIRONMENT.md.

    Build one with `load_settings`. The class itself never looks at the process
    environment: it only takes the values it is handed, so the same code path serves the
    running app and the tests, and a test can never pick up a real value by accident.
    """

    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        frozen=True,
        case_sensitive=True,
        populate_by_name=True,
        # A rejected value is never repeated in the error, whatever it was.
        hide_input_in_errors=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Only what `load_settings` passes in. No implicit environment, .env file or
        # secrets directory.
        return (init_settings,)

    # Runtime
    stai_env: Environment | None = Field(default=None, validation_alias="STAI_ENV")
    replit_deployment: str | None = Field(default=None, validation_alias="REPLIT_DEPLOYMENT")
    port: int | None = Field(default=None, validation_alias="PORT", ge=1, le=65535)
    log_level: str = Field(default="INFO", validation_alias="STAI_LOG_LEVEL")
    build_commit: str | None = Field(default=None, validation_alias="STAI_BUILD_COMMIT")

    # Database
    database_url: SecretStr | None = Field(default=None, validation_alias="DATABASE_URL")

    # Sign-in (Replit OpenID Connect)
    repl_id: str | None = Field(default=None, validation_alias="REPL_ID")
    issuer_url: str = Field(default="https://replit.com/oidc", validation_alias="ISSUER_URL")
    owner_user_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("STAI_OWNER_USER_ID", "REPL_OWNER_ID"),
    )
    session_ttl_hours: int = Field(
        default=168, validation_alias="STAI_SESSION_TTL_HOURS", ge=1, le=24 * 90
    )

    # Hosts this app is served from, used to build sign-in URLs and to check request origins
    replit_domains: str = Field(default="", validation_alias="REPLIT_DOMAINS")
    replit_dev_domain: str = Field(default="", validation_alias="REPLIT_DEV_DOMAIN")
    extra_allowed_hosts: str = Field(default="", validation_alias="STAI_ALLOWED_HOSTS")

    # Public market data (no keys)
    okx_base_url: str = Field(default="https://www.okx.com", validation_alias="STAI_OKX_BASE_URL")

    @field_validator("log_level")
    @classmethod
    def _known_log_level(cls, value: str) -> str:
        level = value.strip().upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("STAI_LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL")
        return level

    @field_validator("issuer_url", "okx_base_url")
    @classmethod
    def _https_base_url(cls, value: str) -> str:
        url = value.strip().rstrip("/")
        if not url.startswith("https://"):
            raise ValueError("must be an https:// URL")
        return url

    @field_validator("owner_user_id", "repl_id", "build_commit")
    @classmethod
    def _strip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("database_url")
    @classmethod
    def _postgresql_url(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and not _is_postgresql_url(value.get_secret_value()):
            raise ValueError("must be a postgresql:// URL")
        return value

    # -- derived values -------------------------------------------------------------------

    @property
    def environment(self) -> Environment:
        """Production unless STAI_ENV says development.

        Unset means production. Any value other than the two is refused at startup.
        """
        return self.stai_env or "production"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_published(self) -> bool:
        return self.replit_deployment == "1"

    @property
    def allowed_hosts(self) -> frozenset[str]:
        hosts: set[str] = set()
        for raw in (self.replit_domains, self.replit_dev_domain, self.extra_allowed_hosts):
            for part in raw.split(","):
                host = part.strip().lower()
                if host:
                    hosts.add(host)
        return frozenset(hosts)

    def is_allowed_host(self, host: str | None) -> bool:
        """True when `host` (optionally with a port) is one this app is served from."""
        if not host:
            return False
        candidate = host.strip().lower()
        if candidate in self.allowed_hosts:
            return True
        hostname = candidate.rsplit(":", 1)[0] if ":" in candidate else candidate
        if hostname in self.allowed_hosts:
            return True
        return not self.is_production and hostname in _LOCAL_HOSTS

    @property
    def sqlalchemy_url(self) -> str | None:
        """The database URL with the driver SQLAlchemy should use, or None when unset."""
        if self.database_url is None:
            return None
        return normalise_database_url(self.database_url.get_secret_value())

    @property
    def signin_configured(self) -> bool:
        return bool(self.repl_id and self.owner_user_id)

    def check(self) -> None:
        """Refuse combinations that would weaken a published machine."""
        if self.is_published and not self.is_production:
            raise ConfigurationError(
                "STAI_ENV=development is not allowed on a published machine "
                "(REPLIT_DEPLOYMENT=1). Remove STAI_ENV or set it to production."
            )


_PLAIN_POSTGRESQL_PREFIXES = ("postgresql://", "postgres://")
_PSYCOPG_PREFIX = "postgresql+psycopg://"


def _is_postgresql_url(url: str) -> bool:
    return url.startswith((*_PLAIN_POSTGRESQL_PREFIXES, _PSYCOPG_PREFIX))


def normalise_database_url(url: str) -> str:
    """Point a plain PostgreSQL URL at the psycopg 3 driver."""
    for prefix in _PLAIN_POSTGRESQL_PREFIXES:
        if url.startswith(prefix):
            return _PSYCOPG_PREFIX + url[len(prefix) :]
    if url.startswith(_PSYCOPG_PREFIX):
        return url
    raise ConfigurationError("DATABASE_URL must be a postgresql:// URL")


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Build settings from `env` (the process environment by default) and check them.

    Only the documented variable names are read, with their exact spelling; an empty
    value counts as not set.
    """
    source = os.environ if env is None else env
    known = known_variable_names()
    settings = Settings(**{name: source[name] for name in known if source.get(name)})
    settings.check()
    return settings


def known_variable_names() -> frozenset[str]:
    """Every environment variable the settings read. docs/ENVIRONMENT.md lists them all."""
    names: set[str] = set()
    for field in Settings.model_fields.values():
        alias = field.validation_alias
        if isinstance(alias, AliasChoices):
            names.update(str(choice) for choice in alias.choices)
        elif isinstance(alias, str):
            names.add(alias)
    return frozenset(names)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Settings for this process, read once."""
    return load_settings()


def secret_values_from_environment(env: Mapping[str, str] | None = None) -> list[str]:
    """Values that must never appear in a log line, taken from the environment.

    Covers every variable whose name looks like a secret, the database URL and its
    password (as written in the URL and decoded), and the owner's alert address. The
    values are only used for masking.
    """
    source = os.environ if env is None else env
    markers = ("SECRET", "TOKEN", "PASSWORD", "PASSWD", "API_KEY", "PRIVATE_KEY", "ALERT_EMAIL")
    values: list[str] = []
    for name, value in source.items():
        if not value:
            continue
        upper = name.upper()
        if upper in {"DATABASE_URL", "PGPASSWORD"} or any(marker in upper for marker in markers):
            values.append(value)
        if upper == "DATABASE_URL":
            values.extend(_passwords_from_url(value))
    return values


def _passwords_from_url(url: str) -> list[str]:
    """The password of a URL as written (percent-encoded) and as the server receives it."""
    try:
        written = urlsplit(url).password
    except ValueError:
        return []
    if not written:
        return []
    decoded = unquote(written)
    return [written] if decoded == written else [written, decoded]
