"""Private Freqtrade dry-run configuration and process lifecycle."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from stai.core.logging import StructuredLogger

logger = StructuredLogger(__name__)
BOT_TYPES = ("spot", "futures")
_SAFE_ENVIRONMENT = ("PATH", "HOME", "LANG", "LC_ALL", "TZ", "PYTHONPATH", "LD_LIBRARY_PATH")


class UnsafeBotConfiguration(RuntimeError):
    """A paper bot configuration would violate the Phase 2 safety rules."""


def build_bot_config(bot_type: str, *, database_url: str | None = None) -> dict[str, object]:
    if bot_type not in BOT_TYPES:
        raise ValueError("bot_type must be spot or futures")
    futures = bot_type == "futures"
    wallet = 400 if futures else 600
    pairs = (
        ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT"]
        if futures
        else ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    )
    config: dict[str, object] = {
        "dry_run": True,
        "dry_run_wallet": wallet,
        "trading_mode": "futures" if futures else "spot",
        "stake_currency": "USDT",
        "stake_amount": 50,
        "max_open_trades": 3,
        "timeframe": "1h",
        "entry_pricing": {
            "price_side": "other",
            "use_order_book": True,
            "order_book_top": 1,
        },
        "exit_pricing": {
            "price_side": "other",
            "use_order_book": True,
            "order_book_top": 1,
        },
        "pairlists": [{"method": "StaticPairList"}],
        "unfilledtimeout": {"entry": 10, "exit": 10, "unit": "minutes"},
        "strategy": "StaiFuturesGateStrategy" if futures else "StaiGateStrategy",
        "exchange": {
            "name": "okx",
            "pair_whitelist": pairs,
            "pair_blacklist": [],
            "ccxt_config": {"options": {"fetchMarkets": {"types": ["spot", "swap"]}}},
        },
        "initial_state": "running",
        "internals": {"process_throttle_secs": 5},
    }
    if futures:
        config["margin_mode"] = "isolated"
    if database_url is not None:
        config["db_url"] = database_url
    validate_bot_config(config, bot_type)
    return config


def validate_bot_config(config: dict[str, object], bot_type: str) -> None:
    """Reject any config that is not the fixed, credential-free paper configuration."""
    exchange = config.get("exchange")
    if not isinstance(exchange, dict):
        raise UnsafeBotConfiguration("exchange config is missing")
    if config.get("dry_run") is not True:
        raise UnsafeBotConfiguration("paper mode must be fixed on")
    if config.get("trading_mode") != ("futures" if bot_type == "futures" else "spot"):
        raise UnsafeBotConfiguration("bot market mode does not match its identity")
    if config.get("margin_mode") != ("isolated" if bot_type == "futures" else None):
        raise UnsafeBotConfiguration("margin mode does not match its identity")
    db_url = config.get("db_url")
    if db_url is not None and (
        not isinstance(db_url, str)
        or not db_url.startswith("sqlite:////tmp/stai-paper-")
        or not db_url.endswith("/tradesv3.dryrun.sqlite")
    ):
        raise UnsafeBotConfiguration(
            "paper-bot state must remain in its private temporary directory"
        )
    if exchange.get("name") != "okx":
        raise UnsafeBotConfiguration("only OKX is supported")
    if any(
        key.lower() in {"key", "secret", "password", "api_key", "passphrase"} for key in exchange
    ):
        raise UnsafeBotConfiguration("exchange credentials are not permitted")
    if "api_server" in config:
        raise UnsafeBotConfiguration("the bot API must remain disabled")
    if "telegram" in config:
        raise UnsafeBotConfiguration("external bot messaging must remain disabled")


@dataclass(slots=True)
class ManagedBot:
    bot_type: str
    process: subprocess.Popen[bytes]
    userdir: Path
    config_path: Path


class BotSupervisor:
    """Starts fixed paper-only bots with no shell and no inherited secrets."""

    def __init__(self, *, strategy_path: Path | None = None):
        self._strategy_path = strategy_path or Path(__file__).resolve().parent
        self._temporary: tempfile.TemporaryDirectory[str] | None = None
        self._bots: dict[str, ManagedBot] = {}

    @property
    def bots(self) -> dict[str, ManagedBot]:
        return self._bots

    def start_all(
        self,
        restored_snapshots: dict[str, tuple[bytes, str]] | None = None,
    ) -> dict[str, ManagedBot]:
        if self._bots:
            return self._bots
        self._temporary = tempfile.TemporaryDirectory(prefix="stai-paper-")
        root = Path(self._temporary.name)
        safe_env = {key: os.environ[key] for key in _SAFE_ENVIRONMENT if os.environ.get(key)}
        safe_env["PYTHONPATH"] = os.pathsep.join(
            filter(
                None,
                [
                    safe_env.get("PYTHONPATH"),
                    str(Path(__file__).resolve().parents[1].parent),
                ],
            )
        )
        try:
            for bot_type in BOT_TYPES:
                userdir = root / bot_type
                userdir.mkdir(mode=0o700)
                database_path = userdir / "tradesv3.dryrun.sqlite"
                if restored_snapshots and bot_type in restored_snapshots:
                    restore_freqtrade_database(database_path, *restored_snapshots[bot_type])
                config_path = root / f"{bot_type}.json"
                config_path.write_text(
                    json.dumps(
                        build_bot_config(
                            bot_type,
                            database_url=f"sqlite:///{database_path}",
                        ),
                        separators=(",", ":"),
                    ),
                    encoding="utf-8",
                )
                config_path.chmod(0o600)
                command = [
                    sys.executable,
                    "-m",
                    "freqtrade",
                    "trade",
                    "--dry-run",
                    "--config",
                    str(config_path),
                    "--userdir",
                    str(userdir),
                    "--strategy-path",
                    str(self._strategy_path),
                    "--strategy",
                    "StaiFuturesGateStrategy" if bot_type == "futures" else "StaiGateStrategy",
                ]
                process = subprocess.Popen(  # noqa: S603 - fixed command and generated paths only
                    command,
                    cwd=str(userdir),
                    env=safe_env,
                    stdin=subprocess.DEVNULL,
                    stdout=None,
                    stderr=subprocess.STDOUT,
                    shell=False,
                    close_fds=True,
                )
                self._bots[bot_type] = ManagedBot(
                    bot_type=bot_type,
                    process=process,
                    userdir=userdir,
                    config_path=config_path,
                )
                logger.info("Paper bot process started", botType=bot_type, pid=process.pid)
            return self._bots
        except BaseException:
            self.stop_all()
            raise

    def stop_all(self, *, timeout_seconds: float = 10.0) -> dict[str, tuple[bytes, str]]:
        for bot_type, bot in list(self._bots.items()):
            process = bot.process
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=timeout_seconds)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            logger.info(
                "Paper bot process stopped",
                botType=bot_type,
                returnCode=process.returncode,
            )
        snapshots = self.snapshots()
        self._bots.clear()
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None
        return snapshots

    def status(self) -> dict[str, str]:
        return {
            bot_type: ("running" if bot.process.poll() is None else "stopped")
            for bot_type, bot in self._bots.items()
        }

    def snapshots(self) -> dict[str, tuple[bytes, str]]:
        result: dict[str, tuple[bytes, str]] = {}
        for bot_type, bot in self._bots.items():
            path = bot.userdir / "tradesv3.dryrun.sqlite"
            if path.is_file():
                snapshot = snapshot_freqtrade_database(path)
                result[bot_type] = (snapshot, hashlib.sha256(snapshot).hexdigest())
        return result

    def open_trades(self, bot_type: str) -> list[dict[str, object]] | None:
        bot = self._bots.get(bot_type)
        if bot is None:
            return None
        path = bot.userdir / "tradesv3.dryrun.sqlite"
        if not path.is_file():
            return None
        try:
            connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=2)
            connection.row_factory = sqlite3.Row
            try:
                columns = {row["name"] for row in connection.execute("PRAGMA table_info(trades)")}
                if not columns:
                    return []
                fields = ("id", "pair", "is_open", "amount", "open_rate", "leverage", "is_short")
                if not set(fields) <= columns:
                    return None
                query = (
                    "SELECT id, pair, is_open, amount, open_rate, leverage, is_short "
                    "FROM trades WHERE is_open = 1 ORDER BY id"
                )
                return [{key: row[key] for key in fields} for row in connection.execute(query)]
            finally:
                connection.close()
        except sqlite3.Error:
            return None


def remove_user_directory(path: Path) -> None:
    """Only for tests and controlled cleanup of generated bot state."""
    shutil.rmtree(path, ignore_errors=True)


def snapshot_freqtrade_database(path: Path) -> bytes:
    """Create a consistent, compressed copy while Freqtrade may still be writing."""
    source = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=3)
    try:
        with tempfile.TemporaryDirectory(prefix="stai-snapshot-") as directory:
            backup_path = Path(directory) / "backup.sqlite"
            destination = sqlite3.connect(backup_path)
            try:
                source.backup(destination)
                # An in-memory backup retains WAL header flags. Such serialized bytes
                # cannot be deserialized without a WAL sidecar. Normalize the isolated
                # on-disk backup, never the live engine database.
                destination.execute("PRAGMA journal_mode=DELETE")
            finally:
                destination.close()
            return gzip.compress(backup_path.read_bytes(), mtime=0)
    finally:
        source.close()


def restore_freqtrade_database(path: Path, snapshot: bytes, expected_sha256: str) -> None:
    """Verify and restore a compressed SQLite snapshot before its private bot starts."""
    if hashlib.sha256(snapshot).hexdigest() != expected_sha256:
        raise UnsafeBotConfiguration("stored Freqtrade state failed its checksum")
    try:
        raw = gzip.decompress(snapshot)
        with tempfile.TemporaryDirectory(prefix="stai-restore-") as directory:
            validation_path = Path(directory) / "validation.sqlite"
            validation_path.write_bytes(raw)
            validation = sqlite3.connect(validation_path)
            try:
                validation.execute("PRAGMA journal_mode=DELETE")
                integrity = validation.execute("PRAGMA integrity_check").fetchone()
                if integrity is None or integrity[0] != "ok":
                    raise UnsafeBotConfiguration("stored Freqtrade state failed integrity check")
            finally:
                validation.close()
            raw = validation_path.read_bytes()
    except (OSError, sqlite3.Error) as exc:
        raise UnsafeBotConfiguration("stored Freqtrade state could not be restored") from exc
    path.write_bytes(raw)
    path.chmod(0o600)
