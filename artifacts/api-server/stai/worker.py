"""Private Phase 2 scanner and paper-bot worker process."""

from __future__ import annotations

import asyncio
import os
import signal
from contextlib import suppress
from typing import Any

from sqlalchemy import select, text

from stai.audit import guards as _audit_guards  # noqa: F401 - install append-only guards
from stai.core.config import get_settings, secret_values_from_environment
from stai.core.logging import StructuredLogger, configure_logging, register_secret_values
from stai.core.time import utcnow
from stai.db.models import BotState, PaperPosition
from stai.main import create_app
from stai.marketdata.service import persist_market_rows
from stai.trading.bots import BotSupervisor
from stai.trading.ledger import ensure_fund, verify_ledger

logger = StructuredLogger(__name__)
WORKER_LOCK_KEY = 0x5354_4149_0004
SCAN_INTERVAL_SECONDS = 15 * 60


def _prior_states(runtime: Any) -> dict[str, BotState]:
    with runtime.database.session() as session:
        return {
            row.bot_id: row
            for row in session.execute(select(BotState)).scalars().all()
        }


def _safe_trade_rows(
    bot_type: str, rows: list[dict[str, object]] | None
) -> list[dict[str, object]] | None:
    if rows is None:
        return None
    result: list[dict[str, object]] = []
    for row in rows:
        item = {key: value for key, value in row.items() if key in {
            "id", "pair", "amount", "open_rate", "open_date", "stop_loss", "leverage", "is_short"
        }}
        item["tradeId"] = f"{bot_type}:{row['id']}"
        result.append(item)
    return result


def _persist_worker_state(
    runtime: Any,
    supervisor: BotSupervisor,
    *,
    snapshots: dict[str, tuple[bytes, str]] | None = None,
    stopped: bool = False,
) -> bool:
    now = utcnow()
    current_status = supervisor.status()
    bot_ids = {"spot", "futures"}
    snapshots = snapshots or {}
    with runtime.database.session() as session:
        previous_rows = {
            row.bot_id: row
            for row in session.execute(select(BotState)).scalars().all()
        }
        expected_positions = {
            position.trade_id
            for position in session.execute(
                select(PaperPosition).where(PaperPosition.state == "open")
            ).scalars()
        }
        chain = verify_ledger(session)
        reconciliation_ok = chain.ok
        for bot_id in bot_ids:
            prior = previous_rows.get(bot_id)
            bot_trades = _safe_trade_rows(
                bot_id,
                None if stopped else supervisor.open_trades(bot_id),
            )
            if bot_trades is None:
                if prior is not None:
                    bot_trades = prior.state.get("openTrades")  # keep prior evidence intact
                else:
                    bot_trades = []
                reconciliation = "pending"
                reconciliation_ok = False
            else:
                engine_ids = {row["tradeId"] for row in bot_trades}
                if engine_ids != expected_positions:
                    reconciliation = "blocked"
                    reconciliation_ok = False
                else:
                    reconciliation = "clear" if chain.ok else "blocked"
            state = {
                "status": "stopped" if stopped else current_status.get(bot_id, "starting"),
                "dryRun": True,
                "entryGate": "closed",
                "reconciliation": reconciliation,
                "ledgerVerified": chain.ok,
                "openTrades": bot_trades,
                "snapshotAt": now.isoformat(),
                "recovery": "restored" if prior and prior.sqlite_snapshot else "fresh",
            }
            row = prior or BotState(bot_id=bot_id, saved_at=now, state=state)
            row.saved_at = now
            row.state = state
            if bot_id in snapshots:
                row.sqlite_snapshot, row.snapshot_sha256 = snapshots[bot_id]
            session.add(row)
        return reconciliation_ok


async def _scan_once(runtime: Any, supervisor: BotSupervisor) -> None:
    rows = await runtime.okx_market_data.scanner()
    with runtime.database.session() as session:
        ensure_fund(session)
        persist_market_rows(session, rows)
    aligned = _persist_worker_state(runtime, supervisor)
    if not aligned:
        logger.warning(
            "Paper trading entries remain blocked",
            reason="ledger, bot state, or reconciliation is not clear",
        )


async def _health_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        request_line = await asyncio.wait_for(reader.readline(), timeout=2)
        path = request_line.decode("ascii", "replace").split(" ")[1:2]
        status = "200 OK" if path == ["/healthz"] else "404 Not Found"
        body = b"ok\n" if status.startswith("200") else b"not found\n"
        writer.write(
            f"HTTP/1.1 {status}\r\nContent-Type: text/plain\r\n"
            f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode("ascii")
            + body
        )
        await writer.drain()
    except (TimeoutError, IndexError, UnicodeError):
        pass
    finally:
        writer.close()
        with suppress(Exception):
            await writer.wait_closed()


async def run_worker(runtime: Any, stop_event: asyncio.Event) -> None:
    lock_connection = runtime.database.engine.connect()
    acquired = lock_connection.execute(
        text("SELECT pg_try_advisory_lock(:key)"), {"key": WORKER_LOCK_KEY}
    ).scalar_one()
    if not acquired:
        lock_connection.close()
        raise RuntimeError("another STAI worker already holds the database lock")
    supervisor = BotSupervisor()
    try:
        previous = _prior_states(runtime)
        restored = {
            bot_id: (row.sqlite_snapshot, row.snapshot_sha256)
            for bot_id, row in previous.items()
            if row.sqlite_snapshot is not None and row.snapshot_sha256 is not None
        }
        supervisor.start_all(restored)
        while not stop_event.is_set():
            await _scan_once(runtime, supervisor)
            try:
                await asyncio.wait_for(
                    stop_event.wait(), timeout=SCAN_INTERVAL_SECONDS
                )
            except TimeoutError:
                continue
    finally:
        final_snapshots = supervisor.stop_all()
        _persist_worker_state(
            runtime,
            supervisor,
            snapshots=final_snapshots,
            stopped=True,
        )
        lock_connection.execute(
            text("SELECT pg_advisory_unlock(:key)"), {"key": WORKER_LOCK_KEY}
        )
        lock_connection.close()


async def _run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    register_secret_values(secret_values_from_environment())
    app = create_app()
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signum, stop_event.set)
    port = int(os.environ.get("PORT", "8099"))
    health_server = await asyncio.start_server(  # noqa: S104 - private service health port
        _health_handler, "0.0.0.0", port
    )
    async with app.router.lifespan_context(app):
        try:
            await run_worker(app.state.runtime, stop_event)
        finally:
            health_server.close()
            await health_server.wait_closed()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
