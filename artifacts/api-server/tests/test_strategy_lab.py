from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import httpx
from pydantic import SecretStr
from sqlalchemy import select

from stai.analytics.core.constants import TradeSide
from stai.db.models import TradeProposal, TradingPermit
from stai.marketdata.okx_market import MarketDataUnavailable, OkxMarketData
from stai.marketdata.schemas import CandlePoint
from stai.strategies.schemas import PullbackEvidence
from stai.strategy_lab.engine import (
    _find_exit,
    _funding_coverage,
    _indicator_snapshots,
    _latest_closed_hour,
    _metrics,
    _millis,
    _strategy_trade,
    _trade_from_exit,
)
from stai.strategy_lab.models import StrategyBacktestReview, StrategyBacktestRun
from stai.strategy_lab.schemas import BacktestTrade, HistoricalReviewAnswer
from stai.strategy_lab.service import get_run, list_runs

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


def test_target_is_not_counted_on_the_entry_fill_candle() -> None:
    start = datetime(2026, 11, 18, tzinfo=UTC)
    bars = [
        _bar(start, high="112", low="99", close="108"),
        _bar(start + timedelta(minutes=15), high="109", low="99"),
        _bar(start + timedelta(minutes=30), high="109", low="99"),
        _bar(start + timedelta(minutes=45), high="109", low="99"),
    ]
    assert _find_exit(
        bars,
        entry_index=0,
        end_index=len(bars),
        side=TradeSide.LONG,
        stop=Decimal("95"),
        target=Decimal("110"),
    ) == (3, Decimal("100"), "time_limit")


def test_future_limit_trade_accounts_for_maker_entry_taker_exit_and_no_spread_slippage() -> None:
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
        entry_fee_type="maker",
        exit_fee_type="taker",
        entry_order_price=Decimal("100"),
    )
    assert trade.gross_pnl_usdt == Decimal("1.000000")
    assert trade.fee_usdt == Decimal("0.070500")
    assert trade.maker_fee_usdt == Decimal("0.020000")
    assert trade.taker_fee_usdt == Decimal("0.050500")
    assert trade.funding_usdt == Decimal("0.000000")
    assert trade.spread_cost_usdt == Decimal("0.000000")
    assert trade.slippage_cost_usdt == Decimal("0.000000")
    assert trade.net_pnl_usdt == Decimal("0.929500")


def test_limit_entry_waits_for_touch_and_shows_target_stop_and_actual_fill(monkeypatch) -> None:
    start = datetime(2026, 11, 18, tzinfo=UTC)
    bars = [
        _bar(start, open_price="100", high="103", low="99", close="102"),
        _bar(start + timedelta(minutes=15), open_price="101.5", high="103", low="101.4"),
        _bar(start + timedelta(minutes=30), open_price="102", high="106", low="101.9"),
        _bar(start + timedelta(minutes=45)),
    ]
    signal_close = start + timedelta(minutes=15)
    h1_key = _millis(_latest_closed_hour(signal_close))
    monkeypatch.setattr(
        "stai.strategy_lab.engine.derive_trade_levels",
        lambda *_args: {"stop_loss": 95.0, "tp1": 105.0},
    )
    diagnostics = {
        "confirmed_setups": 0,
        "missing_exit_indicators": 0,
        "invalid_exit_geometry": 0,
        "invalid_entry_reference": 0,
        "entry_orders_filled": 0,
        "entry_orders_cancelled": 0,
        "unfilled_entry_orders": 0,
    }
    trade, order, next_index, censored = _strategy_trade(
        bars=bars,
        target_h1_snapshots={h1_key: SimpleNamespace(ema_7=100, ema_99=99)},
        signal_state=PullbackEvidence(side="long", stage="confirmed", pullback_high=102),
        diagnostics=diagnostics,
        signal_index=0,
        end_index=len(bars),
        symbol="BTCUSDT",
        market_type="spot",
        side=TradeSide.LONG,
        funding=[],
    )
    assert trade is not None
    assert order is not None and order.status == "filled"
    assert order.limit_price == Decimal("102")
    assert order.fill_price == Decimal("101.5")
    assert trade.entry_order_price == Decimal("102")
    assert trade.entry_price == Decimal("101.5")
    assert trade.stop_price == Decimal("95")
    assert trade.target_price == Decimal("105")
    assert trade.exit_price == Decimal("105")
    assert trade.exit_reason == "take_profit_1"
    assert trade.entry_fee_type == "maker"
    assert trade.exit_fee_type == "maker"
    assert next_index == 3
    assert not censored


def test_limit_entry_expires_unfilled_without_counting_a_trade(monkeypatch) -> None:
    start = datetime(2026, 11, 18, tzinfo=UTC)
    bars = [
        _bar(start + timedelta(minutes=15 * index), open_price="110", high="111", low="109")
        for index in range(5)
    ]
    signal_close = start + timedelta(minutes=15)
    h1_key = _millis(_latest_closed_hour(signal_close))
    monkeypatch.setattr(
        "stai.strategy_lab.engine.derive_trade_levels",
        lambda *_args: {"stop_loss": 95.0, "tp1": 120.0},
    )
    diagnostics = {
        "confirmed_setups": 0,
        "missing_exit_indicators": 0,
        "invalid_exit_geometry": 0,
        "invalid_entry_reference": 0,
        "entry_orders_filled": 0,
        "entry_orders_cancelled": 0,
        "unfilled_entry_orders": 0,
    }
    trade, order, next_index, censored = _strategy_trade(
        bars=bars,
        target_h1_snapshots={h1_key: SimpleNamespace(ema_7=110, ema_99=100)},
        signal_state=PullbackEvidence(side="long", stage="confirmed", pullback_high=102),
        diagnostics=diagnostics,
        signal_index=0,
        end_index=len(bars),
        symbol="BTCUSDT",
        market_type="spot",
        side=TradeSide.LONG,
        funding=[],
    )
    assert trade is None
    assert order is not None and order.status == "unfilled"
    assert "four completed" in order.reason
    assert next_index == len(bars)
    assert not censored


def test_short_limit_entry_uses_pullback_low_and_target_limit_fee(monkeypatch) -> None:
    start = datetime(2026, 11, 18, tzinfo=UTC)
    bars = [
        _bar(start, open_price="100", high="101", low="98", close="99"),
        _bar(
            start + timedelta(minutes=15),
            open_price="98.5",
            high="99",
            low="97",
            close="98",
        ),
        _bar(
            start + timedelta(minutes=30),
            open_price="98",
            high="99",
            low="94",
            close="95",
        ),
        _bar(start + timedelta(minutes=45)),
    ]
    signal_close = start + timedelta(minutes=15)
    h1_key = _millis(_latest_closed_hour(signal_close))
    monkeypatch.setattr(
        "stai.strategy_lab.engine.derive_trade_levels",
        lambda *_args: {"stop_loss": 105.0, "tp1": 95.0},
    )
    diagnostics = {
        "confirmed_setups": 0,
        "missing_exit_indicators": 0,
        "invalid_exit_geometry": 0,
        "invalid_entry_reference": 0,
        "entry_orders_filled": 0,
        "entry_orders_cancelled": 0,
        "unfilled_entry_orders": 0,
    }
    trade, order, _, censored = _strategy_trade(
        bars=bars,
        target_h1_snapshots={h1_key: SimpleNamespace(ema_7=99, ema_99=100)},
        signal_state=PullbackEvidence(side="short", stage="confirmed", pullback_low=98),
        diagnostics=diagnostics,
        signal_index=0,
        end_index=len(bars),
        symbol="BTCUSDT",
        market_type="futures",
        side=TradeSide.SHORT,
        funding=[],
    )
    assert trade is not None and not censored
    assert order is not None and order.status == "filled"
    assert order.limit_price == Decimal("98")
    assert order.fill_price == Decimal("98.5")
    assert trade.entry_price == Decimal("98.5")
    assert trade.stop_price == Decimal("105")
    assert trade.target_price == Decimal("95")
    assert trade.exit_price == Decimal("95")
    assert trade.exit_reason == "take_profit_1"
    assert trade.entry_fee_type == trade.exit_fee_type == "maker"


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


def test_drawdown_percentage_keeps_the_peak_at_the_time_of_the_loss() -> None:
    start = datetime(2026, 11, 18, tzinfo=UTC)
    metrics, _ = _metrics(
        [
            _trade("-100", start + timedelta(minutes=15)),
            _trade("1100", start + timedelta(minutes=30)),
        ],
        excluded=0,
        period_start=start,
    )
    assert metrics.max_drawdown_pct == Decimal("10.0000")


def test_funding_coverage_marks_missing_history_at_the_edges() -> None:
    start = datetime(2026, 11, 18, tzinfo=UTC)
    coverage = _funding_coverage(
        [(start + timedelta(hours=16), Decimal("0.0001"))],
        start,
        start + timedelta(days=1),
    )
    assert coverage.status == "partial"


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
        json={"symbol": "ETHUSDT", "days": 7},
        headers=csrf_headers(harness.client),
    )
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["symbol"] == "ETHUSDT"
    assert len(result["segments"]) == 6
    assert result["status"]["paidCommitteeReviewEnabled"] is False
    assert result["status"]["historicalAiReviewEnabled"] is False
    assert result["status"]["tradingEnabled"] is False
    assert result["status"]["proposalCreationEnabled"] is False
    assert all(segment["metrics"]["tradeCount"] == 0 for segment in result["segments"])
    assert all(segment["metrics"]["winRatePct"] is None for segment in result["segments"])
    assert result["strategy"]["strategyVersion"] == "ema25-pullback-v2"
    assert result["strategy"]["scoreGateEnabled"] is False
    assert "inherited" in result["notes"][0]
    assert result["segments"][0]["entryDiagnostics"]["confirmed_setups"] == 0
    assert result["developmentEnd"] == result["outOfSampleStart"]
    assert "entryOrders" in result["segments"][0]
    review = harness.client.post(
        f"/api/strategy-lab/backtests/{result['id']}/reviews",
        json={"question": "What do these historical results show?"},
        headers=csrf_headers(harness.client),
    )
    assert review.status_code == 409
    assert (
        harness.client.get("/api/strategy-lab").json()["status"]["paidCommitteeReviewEnabled"]
        is False
    )

    history = harness.client.get("/api/strategy-lab/backtests")
    assert history.status_code == 200
    assert len(history.json()) == 1
    detail = harness.client.get(f"/api/strategy-lab/backtests/{result['id']}")
    assert detail.status_code == 200
    assert detail.json()["dataSha256"] == result["dataSha256"]

    with harness.runtime.database.session() as session:
        assert session.get(StrategyBacktestRun, result["id"]) is not None
        assert session.execute(select(StrategyBacktestReview)).scalars().all() == []
        assert get_run(session, user_id="another-owner", run_id=result["id"]) is None
        assert list_runs(session, user_id="another-owner") == []
        assert session.execute(select(TradeProposal)).scalars().all() == []
        assert session.execute(select(TradingPermit)).scalars().all() == []

    # Simulate a saved v1 payload which predates the additive research fields.
    legacy = dict(result)
    legacy["strategy"] = dict(result["strategy"])
    legacy["strategy"]["strategyVersion"] = "btc-regime-pullback-v1"
    legacy["strategy"].pop("entryRules")
    legacy["strategy"].pop("scoreGateEnabled")
    legacy["status"] = dict(result["status"])
    legacy["status"].pop("historicalAiReviewEnabled")
    legacy["notes"] = ["Legacy rules cannot both pass."]
    with harness.runtime.database.session() as session:
        saved = session.get(StrategyBacktestRun, result["id"])
        saved.strategy_version = "btc-regime-pullback-v1"
        saved.result = legacy
    detail = harness.client.get(f"/api/strategy-lab/backtests/{result['id']}").json()
    assert detail["strategy"]["strategyVersion"] == "btc-regime-pullback-v1"
    assert detail["strategy"]["scoreGateEnabled"] is True
    assert detail["notes"] == legacy["notes"]
    overview = harness.client.get("/api/strategy-lab").json()
    assert overview["strategy"]["strategyVersion"] == "ema25-pullback-v2"
    with harness.runtime.database.session() as session:
        assert session.get(StrategyBacktestRun, result["id"]).result == legacy


def test_strategy_lab_rejects_bad_inputs_csrf_and_unavailable_history(
    harness: Harness, monkeypatch
) -> None:
    sign_in(harness.client, harness.provider)
    endpoint = "/api/strategy-lab/backtests"
    assert harness.client.post(endpoint, json={"days": 7}).status_code == 403
    headers = csrf_headers(harness.client)
    assert harness.client.post(endpoint, json={"days": 31}, headers=headers).status_code == 422
    assert (
        harness.client.post(endpoint, json={"symbol": "DOGEUSDT"}, headers=headers).status_code
        == 422
    )

    async def unavailable(*args):
        raise MarketDataUnavailable("Unreachable.")

    monkeypatch.setattr(harness.runtime.okx_market_data, "get_historical_candles", unavailable)
    assert (
        harness.client.post(
            endpoint,
            json={"symbol": "BTCUSDT", "days": 7},
            headers=headers,
        ).status_code
        == 503
    )
    assert harness.client.get(endpoint).json() == []


def test_historical_ai_review_is_manual_fingerprinted_and_budget_capped(
    harness: Harness, monkeypatch
) -> None:
    sign_in(harness.client, harness.provider)

    async def historical_candles(symbol, market_type, start_at, end_at):
        bars = []
        cursor = start_at
        while cursor < end_at:
            bars.append(_bar(cursor))
            cursor += timedelta(minutes=15)
        return bars

    async def historical_funding(symbol, start_at, end_at):
        return []

    monkeypatch.setattr(
        harness.runtime.okx_market_data, "get_historical_candles", historical_candles
    )
    monkeypatch.setattr(
        harness.runtime.okx_market_data, "get_historical_funding", historical_funding
    )
    backtest = harness.client.post(
        "/api/strategy-lab/backtests",
        json={"symbol": "BTCUSDT", "days": 7},
        headers=csrf_headers(harness.client),
    )
    assert backtest.status_code == 201
    run_id = backtest.json()["id"]

    harness.runtime.settings = harness.runtime.settings.model_copy(
        update={
            "openai_api_key": SecretStr("mock-key"),
            "historical_review_enabled": True,
            "historical_review_model": "test-supported-model",
            "historical_review_per_run_cap_usd": Decimal("0.05"),
            "historical_review_daily_cap_usd": Decimal("0.05"),
            "historical_review_input_usd_per_million": Decimal("0.001"),
            "historical_review_output_usd_per_million": Decimal("0.001"),
        }
    )
    status = harness.client.get("/api/strategy-lab").json()["status"]
    assert status["historicalAiReviewEnabled"] is True
    assert status["paidCommitteeReviewEnabled"] is False
    calls = []

    def fake_provider(*, settings, prompt):
        calls.append((settings.historical_review_model, prompt))
        return (
            HistoricalReviewAnswer(
                summary="This saved run contains no closed trades to evaluate.",
                observations=[],
                risks=["No win rate can be inferred from zero completed trades."],
                limitations=["The review is limited to the saved evidence."],
                evidence_ids=["run"],
            ),
            100,
            20,
        )

    monkeypatch.setattr("stai.strategy_lab.historical_review._provider_call", fake_provider)
    endpoint = f"/api/strategy-lab/backtests/{run_id}/reviews"
    first = harness.client.post(
        endpoint,
        json={"question": "What can be concluded from this run?"},
        headers=csrf_headers(harness.client),
    )
    assert first.status_code == 201, first.text
    review = first.json()
    assert review["dataSha256"] == backtest.json()["dataSha256"]
    assert review["answer"]["evidenceIds"] == ["run"]
    assert review["advisoryOnly"] is True
    assert calls[0][0] == "test-supported-model"
    assert "marketCandleSamples" in calls[0][1]
    saved_history = harness.client.get(endpoint)
    assert saved_history.status_code == 200
    assert [item["id"] for item in saved_history.json()] == [review["id"]]
    assert (
        harness.client.get("/api/strategy-lab/backtests/not-the-owner-run/reviews").status_code
        == 404
    )

    second = harness.client.post(
        endpoint,
        json={"question": "Please review it again."},
        headers=csrf_headers(harness.client),
    )
    assert second.status_code == 429
    assert len(calls) == 1
    with harness.runtime.database.session() as session:
        saved_reviews = session.execute(select(StrategyBacktestReview)).scalars().all()
        assert len(saved_reviews) == 1
        assert saved_reviews[0].status == "completed"
        assert saved_reviews[0].data_sha256 == review["dataSha256"]
        assert saved_reviews[0].reserved_usd == Decimal("0")


def test_okx_history_paginates_deduplicates_and_excludes_open_candles() -> None:
    start = datetime(2026, 11, 18, tzinfo=UTC)
    start_ms = int(start.timestamp() * 1000)
    calls = []

    def candle(offset: int, confirmation: str = "1"):
        return [
            str(start_ms + offset * 900_000),
            "100",
            "101",
            "99",
            "100",
            "10",
            "10",
            "1000",
            confirmation,
        ]

    def transport(request):
        calls.append(request)
        assert request.method == "GET"
        assert request.url.path == "/api/v5/market/history-candles"
        cursor = request.url.params["after"]
        rows = (
            [candle(3, "0"), candle(2), candle(1)]
            if cursor == str(start_ms + 4 * 900_000)
            else [candle(1), candle(0), candle(-1)]
        )
        return httpx.Response(200, json={"code": "0", "data": rows})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            market = OkxMarketData(client, "https://www.okx.com")
            return await market.get_historical_candles(
                "BTCUSDT", "spot", start, start + timedelta(hours=1)
            )

    bars = asyncio.run(run())
    assert len(calls) == 2
    assert [bar.opened_at for bar in bars] == [
        start + timedelta(minutes=15 * index) for index in range(3)
    ]
    assert all(bar.complete for bar in bars)
