"""Live checks behind the system status screen. Nothing here is cached or made up."""

from __future__ import annotations

import asyncio
import platform
import time

from anyio import to_thread
from sqlalchemy import text
from sqlalchemy.orm import Session

from stai import __version__
from stai.audit import service as audit_service
from stai.core.build import resolve_commit
from stai.core.logging import StructuredLogger
from stai.core.runtime import Runtime
from stai.core.time import DISPLAY_TIMEZONE, MANILA
from stai.db.base import Base
from stai.db.models import AuditEvent
from stai.db.session import DATABASE_ERRORS
from stai.system.schemas import (
    AuditSummary,
    BackendCheck,
    BuildInfo,
    CheckStatus,
    DatabaseCheck,
    MarketDataCheck,
    RuntimeEnvironment,
    SystemStatus,
    TimeInfo,
    TradingMode,
)

logger = StructuredLogger(__name__)

_AUDIT_UNAVAILABLE = "The audit trail cannot be read while the database is unavailable."


def _database_down(detail: str) -> tuple[DatabaseCheck, AuditSummary]:
    return (
        DatabaseCheck(
            status=CheckStatus.DOWN,
            latency_ms=None,
            server_version=None,
            schema_ready=False,
            missing_tables=[],
            migration_revision=None,
            detail=detail,
        ),
        AuditSummary(
            status=CheckStatus.DOWN,
            event_count=0,
            last_event_at=None,
            last_event_type=None,
            detail=_AUDIT_UNAVAILABLE,
        ),
    )


def check_database(runtime: Runtime) -> tuple[DatabaseCheck, AuditSummary]:
    """Query the database: reachability, structure, migration revision and the audit tail."""
    if not runtime.database.configured:
        return _database_down("DATABASE_URL is not set.")

    try:
        with runtime.database.session() as db:
            started = time.perf_counter()
            db.execute(text("SELECT 1"))
            latency_ms = round((time.perf_counter() - started) * 1000, 1)

            server_version = str(db.execute(text("SHOW server_version")).scalar_one())
            existing = set(
                db.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public'"
                    )
                ).scalars()
            )
            missing = sorted(name for name in Base.metadata.tables if name not in existing)

            # Present in development, where migrations run. The published database gets
            # its structure from the Publish step and may have no revision recorded.
            revision = None
            if "alembic_version" in existing:
                revision = db.execute(
                    text("SELECT version_num FROM alembic_version LIMIT 1")
                ).scalar_one_or_none()

            database = DatabaseCheck(
                status=CheckStatus.DOWN if missing else CheckStatus.OK,
                latency_ms=latency_ms,
                server_version=server_version.split(" ")[0],
                schema_ready=not missing,
                missing_tables=missing,
                migration_revision=revision,
                detail=f"Missing tables: {', '.join(missing)}." if missing else None,
            )

            if AuditEvent.__tablename__ in missing:
                audit = AuditSummary(
                    status=CheckStatus.DOWN,
                    event_count=0,
                    last_event_at=None,
                    last_event_type=None,
                    detail="The audit table does not exist.",
                )
            else:
                audit = _checked_audit_summary(db)
            return database, audit
    except DATABASE_ERRORS:
        logger.exception("Database check failed")
        return _database_down("The database could not be reached.")


def _checked_audit_summary(db: Session) -> AuditSummary:
    try:
        return _audit_summary(audit_service.summarise(db))
    except Exception:
        # The status screen exists to report failures, so a check that cannot run is
        # shown as down with the reason in the log, instead of taking the screen with it.
        # That includes the database refusing the query, for example because the audit
        # table's structure differs from what this code expects: the database check
        # above already said the database itself answers.
        logger.exception("Audit trail check failed")
        return AuditSummary(
            status=CheckStatus.DOWN,
            event_count=0,
            last_event_at=None,
            last_event_type=None,
            detail="The audit trail could not be checked.",
        )


def _audit_summary(summary: audit_service.TrailSummary) -> AuditSummary:
    tail = summary.tail
    if tail.ok:
        status, detail = CheckStatus.OK, None
    else:
        failure = tail.first_break
        status = CheckStatus.DOWN
        detail = (
            f"Integrity check failed at record {failure.seq}: {failure.detail}"
            if failure is not None
            else "Integrity check failed."
        )
    return AuditSummary(
        status=status,
        event_count=summary.event_count,
        last_event_at=summary.last_event_at,
        last_event_type=summary.last_event_type,
        detail=detail,
    )


def overall_status(
    database: DatabaseCheck, audit: AuditSummary, market_data: MarketDataCheck
) -> CheckStatus:
    """Down when STAI cannot work at all, degraded when part of it cannot."""
    if CheckStatus.DOWN in (database.status, audit.status):
        return CheckStatus.DOWN
    statuses = (database.status, audit.status, market_data.status)
    if any(status != CheckStatus.OK for status in statuses):
        return CheckStatus.DEGRADED
    return CheckStatus.OK


async def collect_status(runtime: Runtime) -> SystemStatus:
    (database, audit), reachability = await asyncio.gather(
        to_thread.run_sync(check_database, runtime),
        runtime.market_data_probe.check(),
    )
    market_data = MarketDataCheck(
        status=CheckStatus(reachability.status),
        provider=reachability.provider,
        endpoint=reachability.endpoint,
        latency_ms=reachability.latency_ms,
        exchange_time=reachability.exchange_time,
        clock_skew_ms=reachability.clock_skew_ms,
        checked_at=reachability.checked_at,
        detail=reachability.detail,
    )

    now = runtime.now()
    settings = runtime.settings
    return SystemStatus(
        overall=overall_status(database, audit, market_data),
        trading_mode=TradingMode.PAPER,
        checked_at=now,
        backend=BackendCheck(
            status=CheckStatus.OK,
            environment=RuntimeEnvironment(settings.environment),
            uptime_seconds=max(0, int((now - runtime.started_at).total_seconds())),
            python_version=platform.python_version(),
        ),
        database=database,
        market_data=market_data,
        audit=audit,
        build=BuildInfo(
            version=__version__,
            commit=resolve_commit(settings.build_commit),
            started_at=runtime.started_at,
        ),
        time=TimeInfo(utc=now, manila=now.astimezone(MANILA), timezone=DISPLAY_TIMEZONE),
    )
