from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from stai.analytics.core.constants import TradeSide
from stai.db.models import TradeProposal, TradingPermit
from stai.marketdata.schemas import CandlePoint
from stai.strategy_lab.engine import (
    _find_exit,
    _latest_closed_hour,
    _metrics,
    _indicator_snapshots,
    _trade_from_exit,
)
from stai.strategy_lab.models import StrategyBacktestRun
from stai.strategy_lab.schemas import BacktestTrade

from .conftest import Harness
from .support import csrf_headers, sign_in


def _bar(
    opened_at: datetime,
    *,
    open_price: str = "100",
    high: str = "101",
    low: str = "99",
    close: str = "100",
    volume: str = "10",
) -> CandlePoint:
    return CandlePoint(
        opened_at=opened_at,
        open=Decimal(open_price),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        quote_volume=Decimal("1000"),
        complete=True,
    )


def _trade(pnl: str, exited_at: datetime) -> BacktestTrade:
    return BacktestTrade(
        signal_at=exited_at - timedelta(minutes=30),
        entered_at=exited_at - timedelta(minutes=15),
        exited_at=exited_at,
        side="long",
        score=Decimal("75"),
        entry_price=Decimal("100"),
        stop_price=Decimal("98"),
        target_price=Decimal("102"),
        exit_price=Decimal("101"),
        exit_reason="time_limit",
        holding_minutes=15,
        gross_pnl_usdt=Decimal(pnl),
        fee_usdt=Decimal("0"),
        funding_usdt=Decimal("0"),
        spread_cost_usdt=Decimal("0"),
        slippage_cost_usdt=Decimal("0"),
        net_pnl_usdt=Decimal(pnl),
        return_on_notional_pct=Decimal(pnl),
    )


def test_latest_hour_uses_only_the_most_recent_completed_hour() -> None:
    assert _latest_closed_hour(datetime(2026, 11, 18, 14, 0, tzinfo=UTC)) == datetime(
        2026, 11, 18, 13, 0, tzinfo=UTC
    )
    assert _latest_closed_hour(datetime(2026, 11, 18, 14, 15, tzinfo=UTC)) == datetime(
        2026, 11, 18, 13, 0, tzinfo=UTC
    )


def test_future_candle_changes_do_not_change_an_earlier_indicator_snapshot() -> None:
    start = datetime(2026, 11, 1, tzinfo=UTC)
    bars = [
        _bar(
            start + timedelta(minutes=15 * index),
            open_price=str(100 + index / 100),
            high=str(100.5 + index / 100),
            low=str(99.5 + index / 100),
            close=str(100.2 + index / 100),
        )
        for index in range(160)
    ]
    changed = list(bars)
    for index in range(121, len(changed)):
        at = changed[index].opened_at
        changed[index] = _bar(
            at,
            open_price="500",
            high="510",
            low="490",
            close="505",
        )

    original_snapshots = _indicator_snapshots(bars, symbol="ETH/USDT", timeframe="15m")
    changed_snapshots = _indicator_snapshots(changed, symbol="ETH/USDT", timeframe="15m")
    target_key = int((start + timedelta(minutes=15 * 120)).timestamp() * 1000)
    assert original_snapshots[target_key].ema_99 == changed_snapshots[target_key].ema_99
    assert original_snapshots[target_key].rsi == changed_snapshots[target_key].rsi


def test_stop_is_chosen_when_stop_and_target_touch_the_same_candle() -> None:
    start = datetime(2026, 11, 18, tzinfo=UTC)
    result = _find_exit(
        [_bar(start, high="112", low="90", close="105")],
        entry_index=0,
        end_index=1,
        side=TradeSide.LONG,
        stop=Decimal("95"),
        target=Decimal("110"),
    )
    assert result == (0, Decimal("95"), "stop_loss")


def test_exit_uses_four_closed_bars_and_refuses_to_bridge_a_data_gap() -> None:
    start = datetime(2026, 11, 18, tzinfo=UTC)
    bars = [_bar(start + timedelta(minutes=15 * i)) for i in range(4)]
    time_exit = _find_exit(
        bars,
        entry_index=0,
        end_index=4,
        side=TradeSide.LONG,
        stop=Decimal("95"),
        target=Decimal("110"),
    )
    assert time_exit == (3, Decimal("100"), "time_limit")

    gap = [bars[0], bars[1], bars[3]]
    assert (
        _find_exit(
            gap,
            entry_index=0,
            end_index=3,
            side=TradeSide.LONG,
            stop=Decimal("95"),
            target=Decimal("110"),
        )
        is None
    )


def test_future_trade_accounts_for_taker_fee_spread_slippage_and_funding() -> None:
    start = datetime(2026, 11, 18, tzinfo=UTC)
    signal = _bar(start - timedelta(minutes=15))
    entry_bar = _bar(start)
    exit_bar = _bar(start + timedelta(minutes=15))
    trade = _trade_from_exit(
        side=TradeSide.LONG,
        score=Decimal("75"),
        signal_bar=signal,
        entry_bar=entry_bar,
        exit_bar=exit_bar,
        entry=Decimal("100"),
        exit_price=Decimal("101"),
        stop=Decimal("98"),
        target=Decimal("102"),
        exit_reason="time_limit",
        market_type="futures",
        funding=[(start + timedelta(minutes=5), Decimal("0.001"))],
        spread_bps=Decimal("5"),
        slippage_bps=Decimal("5"),
    )
    assert trade.gross_pnl_usdt == Decimal("1.000000")
    assert trade.fee_usdt == Decimal("0.100500")
    assert trade.funding_usdt == Decimal("0.100000")
    assert trade.spread_cost_usdt == Decimal("0.050250")
    assert trade.slippage_cost_usdt == Decimal("0.100500")
    assert trade.net_pnl_usdt == Decimal("0.648750")


def test_metrics_use_net_trade_results_and_keep_empty_metrics_undefined() -> None:
    start = datetime(2026, 11, 18, tzinfo=UTC)
    metrics, curve = _metrics(
        [_trade("10", start + timedelta(minutes=15)), _trade("-5", start + timedelta(minutes=30))],
        excluded=1,
        period_start=start,
    )
    assert metrics.trade_count == 2
    assert metrics.win_rate_pct == Decimal("50.0000")
    assert metrics.expectancy_usdt == Decimal("2.500000")
    assert metrics.profit_factor == Decimal("2.0000")
    assert metrics.max_drawdown_usdt == Decimal("5.000000")
    assert metrics.cumulative_return_pct == Decimal("0.5000")
    assert metrics.excluded_unclosed_trades == 1
    assert len(curve) == 3

    empty, empty_curve = _metrics([], excluded=0, period_start=start)
    assert empty.trade_count == 0
    assert empty.win_rate_pct is None
    assert empty.expectancy_usdt is None
    assert empty.profit_factor is None
    assert len(empty_curve) == 1


def test_strategy_lab_requires_owner_and_persists_backtests_without_trade_side_effects(
    harness: Harness, monkeypatch
) -> None:
    assert harness.client.get("/api/strategy-lab").status_code == 401
    sign_in(harness.client, harness.provider)

    async def historical_candles(symbol, market_type, start_at, end_at):
        bars: list[CandlePoint] = []
        cursor = start_at
        index = 0
        while cursor < end_at:
            price = Decimal("100") + Decimal(index) / Decimal("1000")
            bars.append(
                _bar(
                    cursor,
                    open_price=str(price),
                    high=str(price + Decimal("0.1")),
                    low=str(price - Decimal("0.1")),
                    close=str(price + Decimal("0.02")),
                )
            )
            cursor += timedelta(minutes=15)
            index += 1
        return bars

    async def historical_funding(symbol, start_at, end_at):
        values = []
        cursor = start_at + timedelta(hours=8)
        while cursor < end_at:
            values.append((cursor, Decimal("0.0001")))
            cursor += timedelta(hours=8)
        return values

    monkeypatch.setattr(
        harness.runtime.okx_market_data, "get_historical_candles", historical_candles
    )
    monkeypatch.setattr(
        harness.runtime.okx_market_data, "get_historical_funding", historical_funding
    )
    response = harness.client.post(
        "/api/strategy-lab/backtests",
        json={"symbol": "ETHUSDT", "days": 7, "spreadBps": 5, "slippageBps": 5},
        headers=csrf_headers(harness.client),
    )
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["symbol"] == "ETHUSDT"
    assert len(result["segments"]) == 6
    assert result["status"]["paidCommitteeReviewEnabled"] is False
    assert result["status"]["tradingEnabled"] is False
    assert result["status"]["proposalCreationEnabled"] is False

    history = harness.client.get("/api/strategy-lab/backtests")
    assert history.status_code == 200
    assert len(history.json()) == 1
    detail = harness.client.get(f"/api/strategy-lab/backtests/{result['id']}")
    assert detail.status_code == 200
    assert detail.json()["dataSha256"] == result["dataSha256"]

    with harness.runtime.database.session() as session:
        assert session.get(StrategyBacktestRun, result["id"]) is not None
        assert session.execute(select(TradeProposal)).scalars().all() == []
        assert session.execute(select(TradingPermit)).scalars().all() == []
