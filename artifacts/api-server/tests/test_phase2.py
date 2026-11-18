"""Phase 2 safety, accounting, market-data and recovery regression tests."""

from __future__ import annotations

import asyncio
import gzip
import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select, text

from stai.db.models import BotState, LedgerEntry, PaperFill, TradingPermit
from stai.marketdata.schemas import BookLevel
from stai.marketdata.service import persist_market_rows
from stai.trading.accounting import (
    FeeSchedule,
    FillConflict,
    FillRejected,
    accounting_reconciles,
    estimate_taker_fill,
    record_fill,
    record_funding,
)
from stai.trading.bots import (
    UnsafeBotConfiguration,
    build_bot_config,
    restore_freqtrade_database,
    snapshot_freqtrade_database,
    validate_bot_config,
)
from stai.trading.gate import EntryRequest, PermitDenied, consume_permit
from stai.trading.ledger import (
    IdempotencyConflict,
    LedgerInputError,
    append_entry,
    ensure_fund,
    verify_ledger,
)
from stai.trading.reconcile import import_completed_orders
from stai.worker import _persist_worker_state

from .conftest import Harness
from .support import sign_in

D = Decimal


@pytest.fixture
def owner(harness: Harness) -> Harness:
    assert sign_in(harness.client, harness.provider).status_code == 302
    return harness


def test_scanner_real_contract_and_persistence(owner: Harness) -> None:
    response = owner.client.get("/api/market/scanner")
    assert response.status_code == 200, response.text
    rows = response.json()["rows"]
    assert len(rows) == 6
    assert {row["marketType"] for row in rows} == {"spot", "futures"}
    assert all(row["status"] == "fresh" for row in rows)
    assert all(row["instrument"]["tickSize"] == "0.1" for row in rows)
    assert all(row["indicators"]["rsi"] is not None for row in rows)
    with owner.admin.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM market_snapshots")).scalar_one() == 6
    calls = owner.provider.calls_to("/api/v5/market/")
    assert calls and all(request.method == "GET" for request in calls)
    assert not any(request.headers.get("OK-ACCESS-KEY") for request in calls)


@pytest.mark.parametrize("seconds,status", [(61, "stale"), (-30, "unavailable")])
def test_market_freshness(owner: Harness, seconds: int, status: str) -> None:
    owner.provider.okx_time = lambda: owner.clock() - timedelta(seconds=seconds)
    rows = owner.client.get("/api/market/scanner").json()["rows"]
    assert all(row["status"] == status for row in rows)
    assert all(row["indicators"]["screeningState"] == "unavailable" for row in rows)


@pytest.mark.parametrize("payload", [{"code": "0", "data": [None]}, [], "bad json"])
def test_malformed_public_data_fails_explicitly(owner: Harness, payload: object) -> None:
    owner.provider.okx_body = lambda: payload
    response = owner.client.get("/api/market/scanner")
    assert response.status_code == 200
    assert all(row["status"] == "unavailable" for row in response.json()["rows"])


@pytest.mark.parametrize(
    "path",
    [
        "/api/market/scanner",
        "/api/portfolio/summary",
        "/api/portfolio/ledger",
        "/api/portfolio/ledger/verify",
    ],
)
def test_phase2_requires_owner_session(harness: Harness, path: str) -> None:
    assert harness.client.get(path).status_code == 401


def test_fund_is_persistent_once_and_decimal(owner: Harness) -> None:
    first = owner.client.get("/api/portfolio/summary").json()
    second = owner.client.get("/api/portfolio/summary").json()
    assert first["fundId"] == second["fundId"] == 1
    assert D(first["equity"]) == D("1000")
    assert {row["marketType"]: D(row["balance"]) for row in first["allocations"]} == {
        "spot": D("600"),
        "futures": D("400"),
    }
    assert second["ledgerEvents"] == 2
    assert second["positions"] == []
    assert owner.client.get("/api/portfolio/ledger/verify").json()["ok"] is True


def test_concurrent_fund_and_ledger_retries_do_not_double_count(owner: Harness) -> None:
    def write_once(_index):
        with owner.runtime.database.session() as session:
            ensure_fund(session)
            append_entry(
                session,
                event_type="test",
                market_type="spot",
                amount=D("0"),
                idempotency_key="same-concurrent-event",
            )

    with ThreadPoolExecutor(max_workers=4) as threads:
        list(threads.map(write_once, range(4)))
    with owner.runtime.database.session() as session:
        assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 3
        assert verify_ledger(session).ok


def test_ledger_precision_idempotency_and_tampering(owner: Harness) -> None:
    with owner.runtime.database.session() as session:
        ensure_fund(session)
        kwargs = dict(
            event_type="fee", market_type="spot", amount=D("-0.1"), idempotency_key="decimal-check"
        )
        first = append_entry(session, **kwargs)
        assert append_entry(session, **kwargs).seq == first.seq
        with pytest.raises(IdempotencyConflict):
            append_entry(session, **(kwargs | {"amount": D("-0.2")}))
    with owner.runtime.database.session() as session:
        assert verify_ledger(session).ok
        assert not accounting_reconciles(session)  # A fee with no fill evidence is a mismatch.
        with pytest.raises(LedgerInputError):
            append_entry(session, **(kwargs | {"amount": D("0.0000000000001")}))
    # Admin tampering bypasses application guards, but breaks the recomputed chain.
    with owner.admin.begin() as connection:
        connection.execute(text("UPDATE ledger_entries SET amount = 3 WHERE seq = 3"))
    assert owner.client.get("/api/portfolio/ledger/verify").json()["ok"] is False


def _fill(
    session,
    *,
    fill_id="entry",
    trade_id="spot:1",
    market_type="spot",
    side="long",
    fill_type="entry",
    quantity=D("1"),
    price=D("100"),
    leverage=D("1"),
):
    return record_fill(
        session,
        fill_id=fill_id,
        trade_id=trade_id,
        market_type=market_type,
        instrument="BTC/USDT",
        side=side,
        fill_type=fill_type,
        quantity=quantity,
        raw_price=price,
        fill_price=price,
        spread_pct=D("0.01"),
        slippage_pct=D("0.02"),
        leverage=leverage,
    )


def test_spot_fill_exit_fees_and_equity(owner: Harness) -> None:
    with owner.runtime.database.session() as session:
        ensure_fund(session)
        _fill(session)
        _fill(session)
        with pytest.raises(FillConflict):
            _fill(session, price=D("101"))
        _fill(session, fill_id="exit", fill_type="exit", price=D("110"))
    body = owner.client.get("/api/portfolio/summary").json()
    assert D(body["fees"]) == D("0.315")
    assert D(body["realizedPnl"]) == D("10")
    assert D(body["equity"]) == D("1009.685")
    assert body["positions"] == []
    assert body["ledgerVerified"] is True
    with owner.runtime.database.session() as session:
        assert session.scalar(select(func.count()).select_from(PaperFill)) == 2


def test_futures_short_fee_notional_not_leverage_and_funding(owner: Harness) -> None:
    with owner.runtime.database.session() as session:
        ensure_fund(session)
        _fill(session, trade_id="futures:1", market_type="futures", side="short", leverage=D("2"))
        record_funding(session, event_id="funding1", trade_id="futures:1", amount=D("-0.02"))
        record_funding(session, event_id="funding1", trade_id="futures:1", amount=D("-0.02"))
        _fill(
            session,
            trade_id="futures:1",
            fill_id="exit",
            market_type="futures",
            side="short",
            fill_type="exit",
            price=D("90"),
            leverage=D("2"),
        )
    body = owner.client.get("/api/portfolio/summary").json()
    assert D(body["fees"]) == D("0.095")
    assert D(body["funding"]) == D("-0.02")
    assert D(body["equity"]) == D("1009.885")
    assert body["ledgerVerified"] is True
    assert FeeSchedule().rate("spot", "maker") == D("0.001")
    assert FeeSchedule().rate("futures", "maker") == D("0.0002")


def test_book_walk_and_depth_guard(owner: Harness) -> None:
    args = dict(
        side="long",
        quantity=D("2"),
        observed_at=owner.clock(),
        bids=[BookLevel(price=D("99"), size=D("100"))],
        asks=[BookLevel(price=D("101"), size=D("1")), BookLevel(price=D("102"), size=D("100"))],
    )
    result = estimate_taker_fill(**args)
    assert result.fill_price == D("101.5")
    assert result.slippage_pct > 0
    with pytest.raises(FillRejected, match="visible depth"):
        estimate_taker_fill(**(args | {"quantity": D("20")}))


def _permit(owner: Harness) -> EntryRequest:
    now = owner.clock()
    rows = asyncio.run(owner.runtime.okx_market_data.scanner())
    with owner.runtime.database.session() as session:
        ensure_fund(session)
        persist_market_rows(session, rows)
        session.add(
            BotState(
                bot_id="spot", saved_at=now, state={"status": "running", "reconciliation": "clear"}
            )
        )
        session.add(
            TradingPermit(
                id="owner-approved",
                instrument="BTC/USDT",
                market_type="spot",
                side="long",
                max_notional=D("50"),
                approved_price=D("100"),
                max_price_drift_pct=D("0.2"),
                leverage=D("1"),
                stop_price=D("95"),
                target_price=D("110"),
                approved_at=now,
                expires_at=now + timedelta(minutes=2),
                consumed=False,
                consumed_at=None,
            )
        )
    return EntryRequest(
        "owner-approved", "BTC/USDT", "spot", "long", D("50"), D("100"), D("1"), D("95"), D("110")
    )


def test_single_use_exact_permit(owner: Harness) -> None:
    request = _permit(owner)
    with owner.runtime.database.session() as session:
        consume_permit(session, request, now=owner.clock())
    with owner.runtime.database.session() as session:
        with pytest.raises(PermitDenied, match="already"):
            consume_permit(session, request, now=owner.clock())


@pytest.mark.parametrize(
    "changes",
    [
        {"notional": D("49")},
        {"price": D("101")},
        {"leverage": D("2")},
        {"instrument": "ETH/USDT"},
        {"stop_price": D("94")},
        {"side": "short"},
        {"permit_id": "unapproved"},
    ],
)
def test_permit_rejects_changed_terms(owner: Harness, changes: dict) -> None:
    request = _permit(owner)
    with owner.runtime.database.session() as session:
        with pytest.raises(PermitDenied):
            consume_permit(session, replace(request, **changes), now=owner.clock())


def test_permit_blocks_stale_feed_and_expiry(owner: Harness) -> None:
    request = _permit(owner)
    with owner.runtime.database.session() as session:
        with pytest.raises(PermitDenied, match="market data"):
            consume_permit(session, request, now=owner.clock() + timedelta(seconds=61))
        with pytest.raises(PermitDenied, match="not current"):
            consume_permit(session, request, now=owner.clock() + timedelta(seconds=121))


def test_bot_configuration_cannot_enable_real_money() -> None:
    from freqtrade.configuration.config_validation import validate_config_schema

    for bot_type in ("spot", "futures"):
        config = build_bot_config(bot_type)
        assert config["dry_run"] is True
        validate_bot_config(config, bot_type)
        validate_config_schema(config.copy())
        with pytest.raises(UnsafeBotConfiguration):
            validate_bot_config(config | {"dry_run": False}, bot_type)
        with pytest.raises(UnsafeBotConfiguration):
            validate_bot_config(
                config | {"exchange": {"name": "okx", "key": "forbidden"}}, bot_type
            )
        with pytest.raises(UnsafeBotConfiguration):
            validate_bot_config(config | {"api_server": {"enabled": True}}, bot_type)


def test_sqlite_snapshot_restore_and_checksum(tmp_path) -> None:
    source = tmp_path / "source.sqlite"
    with sqlite3.connect(source) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE trades(id INTEGER PRIMARY KEY, is_open INTEGER)")
        connection.execute("INSERT INTO trades VALUES(1,1)")
    snapshot = snapshot_freqtrade_database(source)
    digest = hashlib.sha256(snapshot).hexdigest()
    target = tmp_path / "restored.sqlite"
    restore_freqtrade_database(target, snapshot, digest)
    with sqlite3.connect(target) as connection:
        assert connection.execute("SELECT * FROM trades").fetchall() == [(1, 1)]
    with pytest.raises(UnsafeBotConfiguration, match="checksum"):
        restore_freqtrade_database(target, snapshot + b"changed", digest)


def test_worker_reconciles_each_market_and_refuses_unknown_engine_trade(owner: Harness) -> None:
    class Supervisor:
        def status(self):
            return {"spot": "running", "futures": "running"}

        def snapshots(self):
            return {}

        def open_trades(self, bot_type):
            return [{"id": 999, "pair": "BTC/USDT"}] if bot_type == "spot" else []

    with owner.runtime.database.session() as session:
        ensure_fund(session)
    assert _persist_worker_state(owner.runtime, Supervisor()) is False
    with owner.runtime.database.session() as session:
        assert session.get(BotState, "spot").state["reconciliation"] == "blocked"
        assert session.get(BotState, "futures").state["reconciliation"] == "clear"


def test_ledger_cannot_be_changed_via_application_engine(owner: Harness) -> None:
    owner.client.get("/api/portfolio/summary")
    with pytest.raises(Exception, match="[Aa]ppend.only|immutable"):
        with owner.runtime.database.session() as session:
            session.execute(text("DELETE FROM ledger_entries"))
    with owner.runtime.database.session() as session:
        assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2


def test_order_snapshot_import_requires_consumed_approval_and_replays_once(owner: Harness) -> None:
    request = _permit(owner)
    with sqlite3.connect(":memory:") as engine:
        engine.execute(
            "CREATE TABLE trades(id INTEGER, pair TEXT, is_short INTEGER, "
            "leverage REAL, enter_tag TEXT)"
        )
        engine.execute(
            "CREATE TABLE orders(id INTEGER, ft_trade_id INTEGER, ft_order_side TEXT, side TEXT, "
            "average REAL, price REAL, filled REAL, order_filled_date TEXT, funding_fee REAL, "
            "ft_is_open INTEGER)"
        )
        engine.execute("INSERT INTO trades VALUES(1,'BTC/USDT',0,1,'stai:owner-approved')")
        engine.execute(
            "INSERT INTO orders VALUES(1,1,'buy','buy',100,100,0.5,?,0,0)",
            (owner.clock().isoformat(),),
        )
        snapshot = gzip.compress(engine.serialize(), mtime=0)
    with owner.runtime.database.session() as session:
        with pytest.raises(FillRejected, match="consumed owner approval"):
            import_completed_orders(session, "spot", snapshot)
        consume_permit(session, request, now=owner.clock())
        import_completed_orders(session, "spot", snapshot)
        import_completed_orders(session, "spot", snapshot)
        assert session.scalar(select(func.count()).select_from(PaperFill)) == 1
    with owner.runtime.database.session() as session:
        fill = session.get(PaperFill, "spot:order:1")
        assert fill.raw_price == D("100")
        assert fill.fill_price == D("100.1")
        assert fill.fee == D("0.075075")
        assert verify_ledger(session).ok


def test_permit_blocks_unreconciled_engine(owner: Harness) -> None:
    request = _permit(owner)
    with owner.runtime.database.session() as session:
        session.get(BotState, "spot").state = {"status": "running", "reconciliation": "blocked"}
    with owner.runtime.database.session() as session:
        with pytest.raises(PermitDenied, match="reconciliation"):
            consume_permit(session, request, now=owner.clock())


def test_permit_blocks_fourth_position(owner: Harness) -> None:
    request = _permit(owner)
    with owner.runtime.database.session() as session:
        for index in range(3):
            _fill(session, fill_id=f"seed:{index}", trade_id=f"spot:{index}")
    with owner.runtime.database.session() as session:
        with pytest.raises(PermitDenied, match="three-position"):
            consume_permit(session, request, now=owner.clock())
