from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
from sqlalchemy import select

from stai.db.models import TradeProposal, TradingPermit
from stai.marketdata.okx_market import OkxMarketData
from stai.marketdata.schemas import CandlePoint, InstrumentRules
from stai.strategy_lab.models import StrategyBacktestRun
from stai.strategy_lab.structural_engine import (
    BAR_1H,
    BAR_1M,
    DEVELOPMENT_END,
    DEVELOPMENT_START,
    FUTURE_VALIDATION_END,
    Candidate,
    Zone,
    _find_exit,
    _find_minute_fill,
    _point_in_time_atr,
    _setup_candidates,
    _zone_levels,
    research_windows,
    run_structural_backtest,
    strategy_configuration,
)
from stai.strategy_lab.structural_service import persist_run

from .conftest import Harness
from .support import OWNER_ID, csrf_headers, sign_in


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


def _candidate(*, side: str = "long") -> Candidate:
    entry_zone = Zone(
        kind="support" if side == "long" else "resistance",
        lower=Decimal("98"),
        upper=Decimal("99"),
        known_at=datetime(2026, 10, 1, tzinfo=UTC),
        source_count=2,
        interaction_count=3,
    )
    opposing_zone = Zone(
        kind="resistance" if side == "long" else "support",
        lower=Decimal("105"),
        upper=Decimal("107"),
        known_at=datetime(2026, 10, 1, tzinfo=UTC),
        source_count=2,
        interaction_count=2,
    )
    return Candidate(
        candidate_id="candidate",
        symbol="BTCUSDT",
        market_type="futures",
        side=side,  # type: ignore[arg-type]
        anchor_at=datetime(2026, 10, 1, tzinfo=UTC),
        signal_at=datetime(2026, 10, 1, 12, tzinfo=UTC),
        confirmation_at=datetime(2026, 10, 1, 12, tzinfo=UTC),
        anchor_high=Decimal("102"),
        anchor_low=Decimal("100"),
        anchor_atr=Decimal("2"),
        atr15=Decimal("2"),
        entry_ema25=Decimal("101"),
        entry_ema99=Decimal("99"),
        trend_close=Decimal("102"),
        trend_ema25=Decimal("101"),
        trend_ema99=Decimal("99"),
        btc_close=Decimal("102"),
        btc_ema25=Decimal("101"),
        btc_ema99=Decimal("99"),
        confirmation_close=Decimal("103"),
        stop=Decimal("97"),
        target=Decimal("104"),
        support_zone=entry_zone,
        opposing_zone=opposing_zone,
    )


def test_confirmed_hourly_swing_is_hidden_until_both_right_candles_close() -> None:
    start = datetime(2026, 10, 1, tzinfo=UTC)
    bars = []
    for index in range(30):
        bars.append(
            _bar(
                start + BAR_1H * index,
                low="90" if index == 20 else "99",
            )
        )
    atr = _point_in_time_atr(bars, BAR_1H)
    before_confirmation = start + BAR_1H * 22
    confirmed_at = start + BAR_1H * 23

    before_supports, _ = _zone_levels(
        as_of=before_confirmation,
        hourly=bars,
        m15=[],
        atr1h=atr,
    )
    after_supports, _ = _zone_levels(
        as_of=confirmed_at,
        hourly=bars,
        m15=[],
        atr1h=atr,
    )

    assert all(zone.lower != Decimal("90") for zone in before_supports)
    assert any(zone.lower == Decimal("90") for zone in after_supports)


def test_limit_requires_one_tick_through_and_reports_touch_only_as_unfilled() -> None:
    candidate = _candidate()
    start = candidate.confirmation_at
    bars = [
        _bar(
            start + BAR_1M * index,
            open_price="103",
            low="102" if index == 0 else "103",
            high="104",
        )
        for index in range(60)
    ]
    order, fill_index, fill_price, _ = _find_minute_fill(
        candidate=candidate,
        method="anchor_limit",
        minute_bars=bars,
        tick_size=Decimal("1"),
        sample_end=start + timedelta(hours=2),
    )
    assert order.status == "unfilled"
    assert "exact touch" in order.reason
    assert fill_index is None
    assert fill_price is None

    bars[0] = _bar(start, open_price="102", low="101", high="103")
    order, fill_index, fill_price, _ = _find_minute_fill(
        candidate=candidate,
        method="anchor_limit",
        minute_bars=bars,
        tick_size=Decimal("1"),
        sample_end=start + timedelta(hours=2),
    )
    assert order.status == "filled"
    assert fill_index == 0
    assert fill_price == Decimal("102")


def test_market_entry_uses_first_minute_open_and_conservative_same_bar_exit() -> None:
    candidate = _candidate()
    start = candidate.confirmation_at
    bars = [
        _bar(start, open_price="101", high="105", low="96"),
        _bar(start + BAR_1M, high="103", low="99"),
    ]
    order, fill_index, fill_price, raw_fill = _find_minute_fill(
        candidate=candidate,
        method="next_candle_market",
        minute_bars=bars,
        tick_size=Decimal("1"),
        sample_end=start + timedelta(hours=2),
    )
    assert order.status == "filled"
    assert fill_index == 0
    assert fill_price == raw_fill == Decimal("101")

    exit_result = _find_exit(
        minute_bars=bars,
        entry_index=fill_index,
        candidate=candidate,
        hold_minutes=60,
        cost_bps=0,
        sample_end=start + timedelta(hours=2),
    )
    assert exit_result is not None
    assert exit_result[3] == "stop_loss"


def test_research_config_and_reserved_holdout_are_fixed_and_pending() -> None:
    now = datetime(2026, 11, 18, 15, tzinfo=UTC)
    development, future = research_windows(now)
    config = strategy_configuration()

    assert development.starts_at == datetime(2026, 9, 19, 14, tzinfo=UTC)
    assert development.ends_at == datetime(2026, 10, 19, 14, tzinfo=UTC)
    assert future.status == "pending"
    assert config.structural_stop_buffer_atr == Decimal("0.25")
    assert config.target_offset_before_zone_atr == Decimal("0.10")
    assert config.minimum_net_reward_risk == Decimal("2")
    assert config.holding_periods_minutes == [60, 240]


def test_okx_history_adapter_requests_300_closed_one_minute_candles() -> None:
    start = datetime(2026, 9, 19, 14, tzinfo=UTC)
    start_ms = int(start.timestamp() * 1000)
    request_params: list[dict[str, str]] = []

    def transport(request: httpx.Request) -> httpx.Response:
        request_params.append(dict(request.url.params))
        rows = [
            [
                str(start_ms + offset * 60_000),
                "100",
                "101",
                "99",
                "100",
                "10",
                "10",
                "1000",
                "1",
            ]
            for offset in (2, 1, 0)
        ]
        return httpx.Response(200, json={"code": "0", "data": rows})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            market = OkxMarketData(client, "https://www.okx.com")
            return await market.get_historical_candles(
                "BTCUSDT",
                "spot",
                start,
                start + timedelta(minutes=3),
                timeframe="1m",
            )

    candles = asyncio.run(run())
    assert request_params[0]["bar"] == "1m"
    assert request_params[0]["limit"] == "300"
    assert len(candles) == 3
    assert all(candle.complete for candle in candles)


def test_limit_and_market_research_sides_are_isolated_by_market_rules() -> None:
    assert _candidate(side="long").side == "long"
    assert _candidate(side="short").side == "short"

    # Spot does not produce short candidates; futures can evaluate both directions.
    assert (
        len(
            _setup_candidates(
                symbol="BTCUSDT",
                market_type="spot",
                m15=[],
                hourly=[],
                btc_hourly=[],
            )
        )
        == 0
    )
    assert (
        len(
            _setup_candidates(
                symbol="BTCUSDT",
                market_type="futures",
                m15=[],
                hourly=[],
                btc_hourly=[],
            )
        )
        == 0
    )


def test_structural_run_is_separate_from_ema_history_and_has_no_trade_side_effects(
    harness: Harness,
) -> None:
    sign_in(harness.client, harness.provider)
    run_id = "structural-test-run"
    now = datetime(2026, 11, 18, 15, tzinfo=UTC)
    result = run_structural_backtest(
        run_id=run_id,
        created_at=now,
        symbol="BTCUSDT",
        sample_period="development",
        sample_start=DEVELOPMENT_START,
        sample_end=DEVELOPMENT_END,
        m15_by_market={"spot": [], "futures": []},
        hourly_by_market={"spot": [], "futures": []},
        btc_hourly_by_market={"spot": [], "futures": []},
        minute_by_market={"spot": [], "futures": []},
        tick_sizes={"spot": Decimal("0.1"), "futures": Decimal("0.1")},
        funding=[],
        data_sha256="a" * 64,
        now=now,
    )
    with harness.runtime.database.session() as session:
        persist_run(
            session,
            result=result,
            source_snapshot={"samplePeriod": "development"},
            user_id=OWNER_ID,
        )

    structural_list = harness.client.get("/api/strategy-lab/structural/backtests")
    assert structural_list.status_code == 200
    assert len(structural_list.json()) == 1
    structural_detail = harness.client.get(f"/api/strategy-lab/structural/backtests/{run_id}")
    assert structural_detail.status_code == 200
    assert len(structural_detail.json()["segments"]) == 12
    assert structural_detail.json()["committeeReviewStatus"] == "not_run"

    assert harness.client.get("/api/strategy-lab/backtests").json() == []
    assert harness.client.get(f"/api/strategy-lab/backtests/{run_id}").status_code == 404
    assert (
        harness.client.post(
            f"/api/strategy-lab/backtests/{run_id}/reviews",
            json={"question": "Review this structural research run."},
            headers=csrf_headers(harness.client),
        ).status_code
        == 404
    )
    with harness.runtime.database.session() as session:
        assert session.get(StrategyBacktestRun, run_id) is not None
        assert session.execute(select(TradeProposal)).scalars().all() == []
        assert session.execute(select(TradingPermit)).scalars().all() == []


def test_structural_backtest_endpoint_uses_fixed_window_and_saves_no_trade_state(
    harness: Harness, monkeypatch
) -> None:
    sign_in(harness.client, harness.provider)
    calls: list[tuple[str, str, str, datetime, datetime]] = []

    async def historical_candles(
        symbol: str,
        market_type: str,
        start_at: datetime,
        end_at: datetime,
        *,
        timeframe: str,
    ) -> list[CandlePoint]:
        calls.append((symbol, market_type, timeframe, start_at, end_at))
        return []

    async def instrument_rule(symbol: str, market_type: str) -> InstrumentRules:
        return InstrumentRules(
            instrument_id=f"{symbol}-{market_type}",
            min_size=Decimal("0.01"),
            lot_size=Decimal("0.01"),
            tick_size=Decimal("0.1"),
            contract_value=None,
            max_leverage=Decimal("100"),
        )

    async def historical_funding(symbol: str, start_at: datetime, end_at: datetime):
        return []

    monkeypatch.setattr(
        harness.runtime.okx_market_data,
        "get_historical_candles",
        historical_candles,
    )
    monkeypatch.setattr(
        harness.runtime.okx_market_data,
        "get_instrument_rule",
        instrument_rule,
    )
    monkeypatch.setattr(
        harness.runtime.okx_market_data,
        "get_historical_funding",
        historical_funding,
    )
    response = harness.client.post(
        "/api/strategy-lab/structural/backtests",
        json={"symbol": "BTCUSDT", "samplePeriod": "development"},
        headers=csrf_headers(harness.client),
    )

    assert response.status_code == 201, response.text
    result = response.json()
    assert result["samplePeriod"] == "development"
    assert datetime.fromisoformat(result["requestedStart"].replace("Z", "+00:00")) == (
        DEVELOPMENT_START
    )
    assert datetime.fromisoformat(result["requestedEnd"].replace("Z", "+00:00")) == (
        DEVELOPMENT_END
    )
    assert len(result["segments"]) == 12
    assert result["committeeReviewStatus"] == "not_run"
    assert {call[2] for call in calls} == {"1m", "15m", "1h"}
    assert len([call for call in calls if call[2] == "1m"]) == 2
    assert all(call[0] == "BTCUSDT" for call in calls)
    with harness.runtime.database.session() as session:
        assert session.get(StrategyBacktestRun, result["id"]) is not None
        assert session.execute(select(TradeProposal)).scalars().all() == []
        assert session.execute(select(TradingPermit)).scalars().all() == []


def test_reserved_validation_sample_is_locked_then_used_once_per_instrument(
    harness: Harness, monkeypatch
) -> None:
    harness.clock.now = datetime(2026, 11, 18, 15, tzinfo=UTC)
    sign_in(harness.client, harness.provider)
    calls = 0

    async def unexpected_history(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("Locked holdout must not request market history.")

    monkeypatch.setattr(
        harness.runtime.okx_market_data,
        "get_historical_candles",
        unexpected_history,
    )
    locked = harness.client.post(
        "/api/strategy-lab/structural/backtests",
        json={"symbol": "ETHUSDT", "samplePeriod": "future_validation"},
        headers=csrf_headers(harness.client),
    )
    assert locked.status_code == 409
    assert calls == 0

    harness.clock.now = FUTURE_VALIDATION_END + timedelta(hours=1)
    sign_in(harness.client, harness.provider)
    with harness.runtime.database.session() as session:
        session.add(
            StrategyBacktestRun(
                id="already-used-future-run",
                user_id=OWNER_ID,
                symbol="ETHUSDT",
                requested_days=30,
                strategy_version="stai-structural-pullback-v0",
                data_sha256="b" * 64,
                created_at=harness.clock.now,
                result={"sample_period": "future_validation"},
                source_snapshot={"samplePeriod": "future_validation"},
            )
        )
    reused = harness.client.post(
        "/api/strategy-lab/structural/backtests",
        json={"symbol": "ETHUSDT", "samplePeriod": "future_validation"},
        headers=csrf_headers(harness.client),
    )
    assert reused.status_code == 409
    assert calls == 0
