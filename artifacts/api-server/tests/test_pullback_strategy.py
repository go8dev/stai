"""The approved entry hypothesis, independent of unapproved exits and AI scoring."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from math import sin

import pytest
from sqlalchemy import func, select

from stai.db.models import MarketSnapshot, SetupCandidate, TradeProposal, TradingPermit
from stai.proposals.service import persist_market_scan
from stai.strategies.pullback import (
    BAR,
    HOUR,
    EntryBar,
    advance,
    closed_hour,
    hourly_bars,
    indicator_series,
    replay,
)
from stai.strategies.schemas import EntryResearch, PullbackEvidence

from .conftest import Harness
from .test_proposals import _scan_row, _seed_synthetic_review
from .test_strategy_lab import _bar

START = datetime(2026, 11, 18, tzinfo=UTC)


def frame(index=0, *, side="long", close=101, high=102, low=99):
    def price(value):
        return str(value if side == "long" else 200 - value)

    candle = _bar(
        START + index * BAR,
        open_price=price(101),
        high=price(high if side == "long" else low),
        low=price(low if side == "long" else high),
        close=price(close),
    )
    return EntryBar(candle, 100, 90 if side == "long" else 110)


def step(state, bar, *, symbol="BTCUSDT", market="futures", btc=None, h1=None):
    hour = closed_hour(bar.candle.opened_at + BAR)
    context = frame(side=state.side)
    context = EntryBar(context.candle.model_copy(update={"opened_at": hour}), 100, context.ema99)
    return advance(
        state,
        symbol=symbol,
        market_type=market,
        bar=bar,
        h1=h1 or context,
        btc_h1=btc,
        as_of=bar.candle.opened_at + BAR,
    )


@pytest.mark.parametrize("side", ["long", "short"])
def test_touch_then_later_confirmation_without_any_legacy_indicators(side):
    state = step(PullbackEvidence(side=side), frame(side=side))
    assert state.stage == "pullback_detected"
    assert state.confirmation_at is None
    assert state.pullback_at == START + BAR
    confirmed = step(state, frame(1, side=side, close=103, high=104, low=102))
    assert confirmed.stage == "confirmed"
    assert confirmed.setup_id == state.setup_id
    assert confirmed.confirmation_at == START + 2 * BAR
    assert confirmed.bars_waited == 1


@pytest.mark.parametrize("side", ["long", "short"])
def test_confirmation_uses_original_touch_not_previous_bar_and_allows_fourth(side):
    state = step(PullbackEvidence(side=side), frame(side=side))
    for i in range(1, 4):
        state = step(state, frame(i, side=side, close=101.8, high=101.9, low=100.1))
        assert state.stage == "pullback_detected"
        assert state.pullback_at == START + BAR
    state = step(state, frame(4, side=side, close=103, high=104, low=102))
    assert state.stage == "confirmed"
    assert state.bars_waited == 4


@pytest.mark.parametrize("side", ["long", "short"])
def test_expiry_and_equal_high_or_low_are_not_confirmation(side):
    state = step(PullbackEvidence(side=side), frame(side=side))
    for i in range(1, 5):
        state = step(state, frame(i, side=side, close=102, high=103, low=100.5))
    assert state.stage == "expired"
    assert state.confirmation_at is None
    assert step(state, frame(5, side=side, close=103, high=104, low=102)).stage == "waiting"


@pytest.mark.parametrize("failure", ["gap", "h1", "m15", "ema99", "btc", "missing_context"])
def test_setup_cancels_on_bad_data_or_failed_direction(failure):
    state = step(PullbackEvidence(side="long"), frame())
    bar = frame(2 if failure == "gap" else 1, close=103, high=104, low=102)
    kwargs = {}
    if failure == "h1":
        h1 = EntryBar(frame().candle.model_copy(update={"opened_at": START - HOUR}), 90, 90)
        kwargs["h1"] = h1
    if failure == "m15":
        bar = EntryBar(bar.candle, 90, 90)
    if failure == "ema99":
        bar = EntryBar(bar.candle.model_copy(update={"close": Decimal("90")}), 100, 90)
    if failure == "btc":
        kwargs["symbol"] = "ETHUSDT"
        kwargs["btc"] = EntryBar(
            frame().candle.model_copy(update={"opened_at": START - HOUR}), 90, 110
        )
    if failure == "missing_context":
        kwargs["symbol"] = "SOLUSDT"
    state = step(state, bar, **kwargs)
    assert state.stage in {"invalidated", "insufficient_data"}
    assert state.confirmation_at is None


def test_spot_cannot_produce_short_and_eth_requires_matching_btc_context():
    assert (
        step(PullbackEvidence(side="short"), frame(side="short"), market="spot").stage == "waiting"
    )
    btc = EntryBar(frame().candle.model_copy(update={"opened_at": START - HOUR}), 100, 90)
    assert step(PullbackEvidence(side="long"), frame(), symbol="ETHUSDT", btc=btc).stage == (
        "pullback_detected"
    )
    stale_btc = EntryBar(btc.candle.model_copy(update={"opened_at": START - 2 * HOUR}), 100, 90)
    assert (
        step(PullbackEvidence(side="long"), frame(), symbol="SOLUSDT", btc=stale_btc).stage
        == "insufficient_data"
    )


def test_future_or_unfinished_candle_cannot_confirm():
    state = step(PullbackEvidence(side="long"), frame())
    bar = frame(1, close=103, high=104, low=102)
    for complete, now in [(False, START + 3 * BAR), (True, START + BAR)]:
        changed = EntryBar(bar.candle.model_copy(update={"complete": complete}), 100, 90)
        result = advance(
            state,
            symbol="BTCUSDT",
            market_type="spot",
            bar=changed,
            h1=None,
            btc_h1=None,
            as_of=now,
        )
        assert result.stage == "insufficient_data"
        assert result.confirmation_at is None


def test_refresh_and_serialized_restart_do_not_reemit_confirmation():
    bars = {b.candle.opened_at: b for b in [frame(), frame(1, close=103, high=104, low=102)]}
    h1 = {
        START - HOUR: EntryBar(
            frame().candle.model_copy(update={"opened_at": START - HOUR}), 100, 90
        )
    }
    kwargs = dict(
        symbol="BTCUSDT", market_type="spot", m15=bars, h1=h1, btc_h1={}, as_of=START + 2 * BAR
    )
    states, signals = replay(**kwargs)
    assert len(signals["long"]) == 1
    restored = EntryResearch.model_validate_json(EntryResearch(sides=states).model_dump_json())
    repeated, events = replay(**kwargs, previous=restored.sides)
    assert events == {"long": {}}
    assert repeated == states
    next_touch = step(states["long"], frame(2))
    assert next_touch.stage == "pullback_detected"
    assert next_touch.setup_id != states["long"].setup_id


def wave_bars(count=720):
    result = []
    for index in range(count):
        close = 100 + index * 0.015 + sin(index * 0.2) * 0.6
        result.append(
            _bar(
                START - 8 * timedelta(days=1) + index * BAR,
                open_price=str(close),
                high=str(close + 0.12),
                low=str(close - 0.12),
                close=str(close),
            )
        )
    return result


def test_indicator_warmup_resets_on_gap_and_future_data_cannot_rewrite_signals():
    bars = wave_bars(110)
    series = indicator_series(bars, BAR)
    assert series[bars[97].opened_at].ema99 is None
    assert series[bars[98].opened_at].ema99 is not None
    missing = indicator_series(bars[:100] + bars[101:], BAR)
    assert missing[bars[-1].opened_at].ema99 is None
    unfinished = indicator_series(
        bars[:100] + [bars[100].model_copy(update={"complete": False})] + bars[101:], BAR
    )
    assert unfinished[bars[-1].opened_at].ema99 is None
    changed = bars[:100] + [_bar(b.opened_at, close="900") for b in bars[100:]]
    assert indicator_series(changed, BAR)[bars[99].opened_at] == series[bars[99].opened_at]


def test_scanner_resumes_saved_research_and_matches_historical_evaluator(harness: Harness):
    bars = wave_bars()
    hours = hourly_bars(bars)
    now = bars[-1].opened_at + BAR
    row = _scan_row(now).model_copy(update={"candles": hours, "candles_15m": bars})
    _, historical = replay(
        symbol=row.symbol,
        market_type="spot",
        m15=indicator_series(bars, BAR),
        h1=indicator_series(hours, HOUR),
        btc_h1={},
        as_of=now,
    )
    assert historical["long"], "Synthetic waves must exercise at least one real signal."
    signal_at = next(reversed(historical["long"]))
    row.candles_15m = [b for b in bars if b.opened_at <= signal_at]
    row.candles = [b for b in hours if b.opened_at + HOUR <= signal_at + BAR]
    now = signal_at + BAR
    row.observed_at = row.exchange_at = now
    with harness.runtime.database.session() as session:
        persist_market_scan(session, [row], now=now)
    assert row.entry_research.sides["long"] == historical["long"][signal_at]
    assert row.entry_research.ai_eligible is False
    expected = row.entry_research.model_dump(mode="json")
    # Resume using a new row object, as a new worker process would.
    repeated = row.model_copy(
        update={"entry_research": None, "observed_at": now + timedelta(seconds=1)}
    )
    with harness.runtime.database.session() as session:
        persist_market_scan(session, [repeated], now=now + timedelta(seconds=1))
        assert repeated.entry_research.model_dump(mode="json") == expected
        assert session.scalar(select(func.count()).select_from(SetupCandidate)) == 0
        assert session.scalar(select(func.count()).select_from(TradeProposal)) == 0
        assert session.scalar(select(func.count()).select_from(TradingPermit)) == 0
        latest = session.execute(
            select(MarketSnapshot).order_by(MarketSnapshot.observed_at.desc()).limit(1)
        ).scalar_one()
        assert latest.details["entryResearch"] == expected


def test_revised_candidate_cannot_enter_proposal_path(harness: Harness):
    from stai.proposals.service import create_proposal_from_committee_run

    now, candidate_id, run_id, _ = _seed_synthetic_review(harness)
    with harness.runtime.database.session() as session:
        session.get(SetupCandidate, candidate_id).strategy_version = "ema25-pullback-v2"
        session.flush()
        with pytest.raises(ValueError, match="not authorized"):
            create_proposal_from_committee_run(
                session, candidate_id=candidate_id, run_id=run_id, now=now
            )


def test_lab_generates_real_rule_trades_without_score_gate_and_counts_invalid_exits():
    from stai.analytics.core.constants import TradeSide
    from stai.strategy_lab.engine import _strategy_trade, run_backtest

    bars = wave_bars(1344)
    end = bars[-1].opened_at + BAR
    result = run_backtest(
        run_id="synthetic-wave",
        created_at=end,
        symbol="BTCUSDT",
        days=7,
        requested_start=end - timedelta(days=7),
        requested_end=end,
        spot_bars=bars,
        futures_bars=bars,
        btc_spot_bars=bars,
        funding=[],
        spread_bps=Decimal("5"),
        slippage_bps=Decimal("5"),
        data_sha256="test-only",
    )
    trades = [trade for segment in result.segments for trade in segment.trades]
    assert trades, "A coherent strategy must have achievable entries on constructed data."
    assert all(trade.score is None for trade in trades)
    assert all(trade.signal_at == trade.entered_at for trade in trades)
    assert all(trade.holding_minutes <= 60 for trade in trades)
    assert result.engine_version == "okx-closed-candle-v2"
    assert result.strategy.score_gate_enabled is False
    assert not any("cannot both pass" in note for note in result.notes)
    # A confirmed entry with unusable inherited levels is rejected, never fixed to force a trade.
    from stai.strategy_lab.engine import _indicator_snapshots

    hours = _indicator_snapshots(hourly_bars(bars), symbol="BTC/USDT", timeframe="1h")
    diagnostics = {
        "confirmed_setups": 0,
        "missing_exit_indicators": 0,
        "missing_next_open": 0,
        "invalid_exit_geometry": 0,
    }
    changed = list(bars)
    index = 800
    changed[index + 1] = changed[index + 1].model_copy(update={"open": Decimal("10000")})
    trade, _, _ = _strategy_trade(
        bars=changed,
        target_h1_snapshots=hours,
        qualified=True,
        diagnostics=diagnostics,
        signal_index=index,
        end_index=len(changed),
        symbol="BTCUSDT",
        market_type="spot",
        side=TradeSide.LONG,
        funding=[],
        spread_bps=Decimal("5"),
        slippage_bps=Decimal("5"),
    )
    assert trade is None
    assert diagnostics["invalid_exit_geometry"] == 1
