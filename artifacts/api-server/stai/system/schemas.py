"""API shapes of the health check and the system status."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from stai.core.schemas import ApiModel


class CheckStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


class RuntimeEnvironment(StrEnum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class TradingMode(StrEnum):
    """STAI has one mode. There is no live value and no switch to add one."""

    PAPER = "paper"


class HealthStatus(ApiModel):
    status: str


class BackendCheck(ApiModel):
    status: CheckStatus
    environment: RuntimeEnvironment
    uptime_seconds: int
    python_version: str


class DatabaseCheck(ApiModel):
    status: CheckStatus
    latency_ms: float | None
    server_version: str | None
    schema_ready: bool
    missing_tables: list[str]
    migration_revision: str | None
    detail: str | None


class MarketDataCheck(ApiModel):
    status: CheckStatus
    provider: str
    endpoint: str
    latency_ms: float | None
    exchange_time: datetime | None
    clock_skew_ms: float | None
    checked_at: datetime
    detail: str | None


class AuditSummary(ApiModel):
    status: CheckStatus
    event_count: int
    last_event_at: datetime | None
    last_event_type: str | None
    detail: str | None


class BuildInfo(ApiModel):
    version: str
    commit: str | None
    started_at: datetime


class TimeInfo(ApiModel):
    utc: datetime
    manila: datetime
    timezone: str


class SystemStatus(ApiModel):
    overall: CheckStatus
    trading_mode: TradingMode
    checked_at: datetime
    backend: BackendCheck
    database: DatabaseCheck
    market_data: MarketDataCheck
    audit: AuditSummary
    build: BuildInfo
    time: TimeInfo
