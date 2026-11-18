"""Causal backtest calculations over closed OKX 15-minute candles."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from stai.analytics.core.constants import (
    CandleBehavior,
    MarketRegime,
    Timeframe,
    TradeSide,
)
from stai.analytics.schemas.market_data import Candle
from stai.analytics.schemas.market_snapshot import MarketSnapshot
from stai.analytics.schemas.scanner import ScannerCandidate
from stai.analytics.services.btc_regime_service import (
    REGIME_WEIGHT_H1,
    REGIME_WEIGHT_M15,
    _classify_composite,
    _score_snapshot,
)
from stai.analytics.services.setup_scoring_service import (
    derive_trade_levels,
    score_candidate,
)
from stai.analytics.utils.indicators import (
    classify_macd,
    classify_rsi,
    classify_volume,
    compute_indicators,
    detect_rejection_candle,
    detect_strong_momentum,
    detect_trend,
)
from stai.marketdata.schemas import CandlePoint, MarketType
from stai.proposals.service import STRATEGY_THRESHOLD, STRATEGY_VERSION
from stai.strategy_lab.schemas import (
    BacktestMetrics,
    BacktestResult,
    BacktestSegment,
    BacktestTrade,
    CandleCoverage,
    EquityPoint,
    FundingCoverage,
    PeriodName,
    StrategyConfiguration,
    StrategyLabStatus,
)
from stai.trading.accounting import FeeSchedule

ENGINE_VERSION = "okx-closed-candle-v1"
INITIAL_EQUITY = Decimal("1000")
TRADE_NOTIONAL = Decimal("100")
LEVERAGE = Decimal("1")
BAR_INTERVAL = timedelta(minutes=15)
MAX_HOLD_BARS = 4
INDICATOR_WARMUP = timedelta(days=7)
_MONEY_QUANTUM = Decimal("0.000001")
_PERCENT_QUANTUM = Decimal("0.0001")


def strategy_configuration(
    *, spread_bps: Decimal = Decimal("5"), slippage_bps: Decimal = Decimal("5")
) -> StrategyConfiguration:
    return StrategyConfiguration(
        strategy_version=STRATEGY_VERSION,
        score_threshold=STRATEGY_THRESHOLD,
        trend_timeframe="1h",
        confirmation_timeframe="15m",
        spot_sides=["long"],
        futures_sides=["long", "short"],
        take_profit_level="TP1: EMA-7 × 1.015 long / EMA-7 × 0.985 short",
        stop_rule="EMA-99 minus 1.5% long / plus 1.5% short",
        max_hold_minutes=60,
        sample_split="Chronological 70% development / 30% out-of-sample",
        notional_usdt=TRADE_NOTIONAL,
        leverage=LEVERAGE,
        spread_bps=spread_bps,
        slippage_bps=slippage_bps,
        no_lookahead_rule=(
            "Evaluate only a closed 15m signal candle using the latest closed 1h and BTC "
            "regime candles; enter at the next 15m candle open."
        ),
        execution_assumptions=[
            "Fixed 100 USDT notional per trade; 1x exposure; no compounding.",
            "Taker fees use STAI's configurable defaults, not an account-specific OKX tier.",
            "Historical candles do not contain order-book spreads; the selected spread and "
            "slippage values are assumptions, not measured historical fills.",
            "Stops win ties when both stop and target are touched in one 15m candle.",
        ],
    )


def canonical_data_hash(snapshot: dict[str, object]) -> str:
    raw = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Backtest timestamps must be timezone-aware.")
    return value.astimezone(UTC)


def _millis(value: datetime) -> int:
    return int(_as_utc(value).timestamp() * 1000)


def _as_candle(bar: CandlePoint, interval: timedelta) -> Candle:
    opened_ms = _millis(bar.opened_at)
    return Candle(
        open_time=opened_ms,
        open=float(bar.open),
        high=float(bar.high),
        low=float(bar.low),
        close=float(bar.close),
        volume=float(bar.volume),
        close_time=opened_ms + int(interval.total_seconds() * 1000) - 1,
        quote_volume=float(bar.quote_volume),
        trades=0,
    )


def _finite(row: object, key: str) -> float | None:
    try:
        value = float(row[key])  # type: ignore[index]
    except (KeyError, TypeError, ValueError, IndexError):
        return None
    return value if math.isfinite(value) else None


def _snapshot_from_indicator(
    *,
    symbol: str,
    timeframe: Timeframe,
    bar: CandlePoint,
    indicator_row: object,
) -> MarketSnapshot:
    values = {
        key: _finite(indicator_row, key)
        for key in (
            "ema_7",
            "ema_25",
            "ema_99",
            "rsi",
            "macd",
            "macd_signal",
            "macd_hist",
            "avg_volume",
            "volume_ratio",
            "body",
            "upper_wick",
            "lower_wick",
            "body_pct",
        )
    }
    return MarketSnapshot(
        symbol=symbol,
        timeframe=timeframe,
        current_price=float(bar.close),
        ema_7=values["ema_7"],
        ema_25=values["ema_25"],
        ema_99=values["ema_99"],
        ema_alignment=detect_trend(indicator_row),
        rsi=values["rsi"],
        rsi_state=classify_rsi(values["rsi"]),
        macd=values["macd"],
        macd_signal=values["macd_signal"],
        macd_hist=values["macd_hist"],
        macd_direction=classify_macd(values["macd_hist"]),
        volume=float(bar.volume),
        avg_volume=values["avg_volume"],
        volume_ratio=values["volume_ratio"],
        volume_strength=classify_volume(values["volume_ratio"]),
        body=values["body"],
        upper_wick=values["upper_wick"],
        lower_wick=values["lower_wick"],
        body_pct=values["body_pct"],
        candle_behavior=(
            detect_rejection_candle(indicator_row)
            or detect_strong_momentum(indicator_row)
            or CandleBehavior.NEUTRAL
        ),
        computed_at=(_as_utc(bar.opened_at) + timeframe_delta(timeframe)).isoformat(),
    )


def timeframe_delta(timeframe: Timeframe) -> timedelta:
    return timedelta(hours=1) if timeframe == Timeframe.H1 else timedelta(minutes=15)


def _indicator_snapshots(
    bars: list[CandlePoint],
    *,
    symbol: str,
    timeframe: Timeframe,
) -> dict[int, MarketSnapshot]:
    """Calculate causal indicators independently within contiguous candle segments."""
    interval = timeframe_delta(timeframe)
    result: dict[int, MarketSnapshot] = {}
    segments: list[list[CandlePoint]] = []
    for bar in bars:
        if not segments or bar.opened_at != segments[-1][-1].opened_at + interval:
            segments.append([])
        segments[-1].append(bar)

    for segment in segments:
        if len(segment) < 30:
            continue
        frame = compute_indicators([_as_candle(bar, interval) for bar in segment])
        for index, bar in enumerate(segment):
            result[_millis(bar.opened_at)] = _snapshot_from_indicator(
                symbol=symbol,
                timeframe=timeframe,
                bar=bar,
                indicator_row=frame.iloc[index],
            )
    return result


def _hourly_bars(bars: list[CandlePoint]) -> list[CandlePoint]:
    grouped: dict[int, list[CandlePoint]] = defaultdict(list)
    for bar in bars:
        opened_ms = _millis(bar.opened_at)
        grouped[(opened_ms // 3_600_000) * 3_600_000].append(bar)
    hourly: list[CandlePoint] = []
    for hour_ms, group in sorted(grouped.items()):
        group.sort(key=lambda candle: candle.opened_at)
        expected = [hour_ms + offset * 900_000 for offset in range(4)]
        if [_millis(bar.opened_at) for bar in group] != expected:
            continue
        hourly.append(
            CandlePoint(
                opened_at=datetime.fromtimestamp(hour_ms / 1000, tz=UTC),
                open=group[0].open,
                high=max(bar.high for bar in group),
                low=min(bar.low for bar in group),
                close=group[-1].close,
                volume=sum((bar.volume for bar in group), Decimal("0")),
                quote_volume=sum((bar.quote_volume for bar in group), Decimal("0")),
                complete=True,
            )
        )
    return hourly


def _latest_closed_hour(signal_close: datetime) -> datetime:
    signal_ms = _millis(signal_close)
    hour_open_ms = ((signal_ms // 3_600_000) - 1) * 3_600_000
    return datetime.fromtimestamp(hour_open_ms / 1000, tz=UTC)


def _btc_regime(
    btc_h1: MarketSnapshot | None, btc_m15: MarketSnapshot | None
) -> MarketRegime:
    if btc_h1 is None or btc_m15 is None:
        return MarketRegime.UNKNOWN
    h1_score, _ = _score_snapshot(btc_h1)
    m15_score, _ = _score_snapshot(btc_m15)
    composite = h1_score * REGIME_WEIGHT_H1 + m15_score * REGIME_WEIGHT_M15
    regime, _, _ = _classify_composite(composite, h1_score, m15_score)
    return regime


def _has_recent_warmup(
    bars: list[CandlePoint],
    index: int,
    count: int,
    interval: timedelta = BAR_INTERVAL,
) -> bool:
    if index + 1 < count:
        return False
    selected = bars[index - count + 1 : index + 1]
    return all(
        right.opened_at - left.opened_at == interval
        for left, right in zip(selected, selected[1:], strict=False)
    )


def _eligible_setup(
    *,
    symbol: str,
    side: TradeSide,
    signal_bar: CandlePoint,
    h1: MarketSnapshot | None,
    m15: MarketSnapshot | None,
    btc_regime: MarketRegime,
) -> tuple[Decimal, dict[str, float]] | None:
    if h1 is None or m15 is None:
        return None
    expected = "bullish" if side == TradeSide.LONG else "bearish"
    if btc_regime.value != expected:
        return None
    if h1.ema_alignment.value != expected:
        return None
    if m15.ema_alignment.value != expected or m15.macd_direction.value != expected:
        return None
    confirmation = (
        {CandleBehavior.STRONG_BULL, CandleBehavior.REJECTION_BULL}
        if side == TradeSide.LONG
        else {CandleBehavior.STRONG_BEAR, CandleBehavior.REJECTION_BEAR}
    )
    if m15.candle_behavior not in confirmation:
        return None
    if h1.ema_7 is None or h1.ema_99 is None:
        return None
    current_price = float(signal_bar.close)
    in_zone = h1.ema_99 <= h1.current_price <= h1.ema_7
    in_zone = in_zone and h1.ema_99 <= current_price <= h1.ema_7
    if not in_zone:
        return None

    candidate = ScannerCandidate(
        symbol=symbol,
        last_price=current_price,
        change_percent_24h=0,
        quote_volume=0,
        candidate_side=side,
        scan_reasons=["Historical closed-candle evaluation"],
        scanned_at=(_as_utc(signal_bar.opened_at) + BAR_INTERVAL).isoformat(),
    )
    scored = score_candidate(candidate, btc_regime, h1, m15)
    if scored.score < STRATEGY_THRESHOLD:
        return None
    levels = derive_trade_levels(h1, side, current_price)
    return Decimal(str(scored.score)), {key: float(value) for key, value in levels.items()}


def _valid_levels(side: TradeSide, entry: Decimal, levels: dict[str, float]) -> bool:
    stop = Decimal(str(levels["stop_loss"]))
    target = Decimal(str(levels["tp1"]))
    return stop < entry < target if side == TradeSide.LONG else target < entry < stop


def _find_exit(
    bars: list[CandlePoint],
    *,
    entry_index: int,
    end_index: int,
    side: TradeSide,
    stop: Decimal,
    target: Decimal,
) -> tuple[int, Decimal, Literal["stop_loss", "take_profit_1", "time_limit"]] | None:
    last_index = min(entry_index + MAX_HOLD_BARS - 1, end_index - 1, len(bars) - 1)
    for index in range(entry_index, last_index + 1):
        bar = bars[index]
        if index > entry_index and bar.opened_at != bars[index - 1].opened_at + BAR_INTERVAL:
            return None
        open_price = bar.open
        high = bar.high
        low = bar.low
        if side == TradeSide.LONG:
            stop_hit = low <= stop
            target_hit = high >= target
            if stop_hit:
                return index, min(open_price, stop) if open_price < stop else stop, "stop_loss"
            if target_hit:
                exit_price = max(open_price, target) if open_price > target else target
                return index, exit_price, "take_profit_1"
        else:
            stop_hit = high >= stop
            target_hit = low <= target
            if stop_hit:
                return index, max(open_price, stop) if open_price > stop else stop, "stop_loss"
            if target_hit:
                exit_price = min(open_price, target) if open_price < target else target
                return index, exit_price, "take_profit_1"
        if index == entry_index + MAX_HOLD_BARS - 1:
            return index, bar.close, "time_limit"
    return None


def _quantize(value: Decimal, quantum: Decimal = _MONEY_QUANTUM) -> Decimal:
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def _trade_from_exit(
    *,
    side: TradeSide,
    score: Decimal,
    signal_bar: CandlePoint,
    entry_bar: CandlePoint,
    exit_bar: CandlePoint,
    entry: Decimal,
    exit_price: Decimal,
    stop: Decimal,
    target: Decimal,
    exit_reason: Literal["stop_loss", "take_profit_1", "time_limit"],
    market_type: MarketType,
    funding: list[tuple[datetime, Decimal]],
    spread_bps: Decimal,
    slippage_bps: Decimal,
) -> BacktestTrade:
    direction = Decimal("1") if side == TradeSide.LONG else Decimal("-1")
    quantity = TRADE_NOTIONAL / entry
    exit_notional = quantity * exit_price
    gross = quantity * (exit_price - entry) * direction
    fee_rate = FeeSchedule().rate(market_type, "taker")
    fees = (TRADE_NOTIONAL + exit_notional) * fee_rate
    spread_cost = (TRADE_NOTIONAL + exit_notional) * spread_bps / Decimal("20000")
    slippage_cost = (TRADE_NOTIONAL + exit_notional) * slippage_bps / Decimal("10000")
    exit_at = _as_utc(exit_bar.opened_at) + BAR_INTERVAL
    funding_cost = Decimal("0")
    if market_type == "futures":
        for funding_at, rate in funding:
            funding_at = _as_utc(funding_at)
            if _as_utc(entry_bar.opened_at) < funding_at <= exit_at:
                funding_cost += TRADE_NOTIONAL * rate * direction
    net = gross - fees - spread_cost - slippage_cost - funding_cost
    return BacktestTrade(
        signal_at=_as_utc(signal_bar.opened_at) + BAR_INTERVAL,
        entered_at=_as_utc(entry_bar.opened_at),
        exited_at=exit_at,
        side=side.value,
        score=_quantize(score, _PERCENT_QUANTUM),
        entry_price=_quantize(entry, _PERCENT_QUANTUM),
        stop_price=_quantize(stop, _PERCENT_QUANTUM),
        target_price=_quantize(target, _PERCENT_QUANTUM),
        exit_price=_quantize(exit_price, _PERCENT_QUANTUM),
        exit_reason=exit_reason,
        holding_minutes=int((exit_at - _as_utc(entry_bar.opened_at)).total_seconds() // 60),
        gross_pnl_usdt=_quantize(gross),
        fee_usdt=_quantize(fees),
        funding_usdt=_quantize(funding_cost),
        spread_cost_usdt=_quantize(spread_cost),
        slippage_cost_usdt=_quantize(slippage_cost),
        net_pnl_usdt=_quantize(net),
        return_on_notional_pct=_quantize(net / TRADE_NOTIONAL * 100, _PERCENT_QUANTUM),
    )


def _metrics(
    trades: list[BacktestTrade],
    *,
    excluded: int,
    period_start: datetime,
) -> tuple[BacktestMetrics, list[EquityPoint]]:
    wins = sum(trade.net_pnl_usdt > 0 for trade in trades)
    losses = sum(trade.net_pnl_usdt < 0 for trade in trades)
    breakeven = len(trades) - wins - losses
    total = sum((trade.net_pnl_usdt for trade in trades), Decimal("0"))
    gross_wins = sum(
        (trade.net_pnl_usdt for trade in trades if trade.net_pnl_usdt > 0), Decimal("0")
    )
    gross_losses = abs(
        sum((trade.net_pnl_usdt for trade in trades if trade.net_pnl_usdt < 0), Decimal("0"))
    )
    factor = gross_wins / gross_losses if gross_losses > 0 else None
    equity = INITIAL_EQUITY
    peak = INITIAL_EQUITY
    max_drawdown = Decimal("0")
    curve = [
        EquityPoint(at=_as_utc(period_start), equity_usdt=equity, cumulative_pnl_usdt=Decimal("0"))
    ]
    for trade in trades:
        equity += trade.net_pnl_usdt
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
        curve.append(
            EquityPoint(
                at=trade.exited_at,
                equity_usdt=_quantize(equity),
                cumulative_pnl_usdt=_quantize(equity - INITIAL_EQUITY),
            )
        )
    count = len(trades)
    metrics = BacktestMetrics(
        trade_count=count,
        wins=wins,
        losses=losses,
        breakeven=breakeven,
        win_rate_pct=_quantize(Decimal(wins) / count * 100, _PERCENT_QUANTUM) if count else None,
        expectancy_usdt=_quantize(total / count) if count else None,
        expectancy_pct_of_notional=(
            _quantize(total / Decimal(count) / TRADE_NOTIONAL * 100, _PERCENT_QUANTUM)
            if count
            else None
        ),
        profit_factor=_quantize(factor, _PERCENT_QUANTUM) if factor is not None else None,
        profit_factor_note=(
            "No losing trades in this sample."
            if count and gross_losses == 0 and gross_wins > 0
            else ("No completed trades." if count == 0 else None)
        ),
        max_drawdown_usdt=_quantize(max_drawdown),
        max_drawdown_pct=(
            _quantize(max_drawdown / peak * 100, _PERCENT_QUANTUM) if peak else Decimal("0")
        ),
        cumulative_pnl_usdt=_quantize(total),
        cumulative_return_pct=_quantize(total / INITIAL_EQUITY * 100, _PERCENT_QUANTUM),
        ending_equity_usdt=_quantize(equity),
        total_fees_usdt=_quantize(sum((trade.fee_usdt for trade in trades), Decimal("0"))),
        total_funding_usdt=_quantize(sum((trade.funding_usdt for trade in trades), Decimal("0"))),
        total_spread_cost_usdt=_quantize(
            sum((trade.spread_cost_usdt for trade in trades), Decimal("0"))
        ),
        total_slippage_cost_usdt=_quantize(
            sum((trade.slippage_cost_usdt for trade in trades), Decimal("0"))
        ),
        excluded_unclosed_trades=excluded,
    )
    return metrics, curve


def _coverage(
    *,
    symbol: str,
    market_type: MarketType,
    bars: list[CandlePoint],
    start_at: datetime,
    end_at: datetime,
) -> CandleCoverage:
    selected = [
        bar for bar in bars if _as_utc(start_at) <= _as_utc(bar.opened_at) < _as_utc(end_at)
    ]
    expected = max(0, int((_as_utc(end_at) - _as_utc(start_at)).total_seconds() // 900))
    opens = {_millis(bar.opened_at) for bar in selected}
    gap_ranges: list[str] = []
    run_start: int | None = None
    previous: int | None = None
    for slot in range(_millis(start_at), _millis(end_at), 900_000):
        if slot not in opens and run_start is None:
            run_start = slot
        if slot in opens and run_start is not None:
            gap_ranges.append(
                f"{datetime.fromtimestamp(run_start / 1000, tz=UTC).isoformat()} to "
                f"{datetime.fromtimestamp(slot / 1000, tz=UTC).isoformat()}"
            )
            run_start = None
        previous = slot
    if run_start is not None and previous is not None:
        gap_ranges.append(
            f"{datetime.fromtimestamp(run_start / 1000, tz=UTC).isoformat()} to "
            f"{_as_utc(end_at).isoformat()}"
        )
    missing = max(0, expected - len(opens))
    return CandleCoverage(
        symbol=symbol,  # type: ignore[arg-type]
        market_type=market_type,
        requested_start=_as_utc(start_at),
        requested_end=_as_utc(end_at),
        first_candle_at=_as_utc(selected[0].opened_at) if selected else None,
        last_candle_at=_as_utc(selected[-1].opened_at) if selected else None,
        actual_closed_candles=len(selected),
        expected_candles=expected,
        missing_candles=missing,
        coverage_pct=(
            _quantize(Decimal(len(opens)) / expected * 100, _PERCENT_QUANTUM)
            if expected
            else Decimal("0")
        ),
        gap_ranges=gap_ranges[:20],
    )


def _funding_coverage(
    funding: list[tuple[datetime, Decimal]], start_at: datetime, end_at: datetime
) -> FundingCoverage:
    selected = [
        (at, rate)
        for at, rate in funding
        if _as_utc(start_at) <= _as_utc(at) < _as_utc(end_at)
    ]
    if not selected:
        return FundingCoverage(
            status="unavailable",
            records=0,
            first_event_at=None,
            last_event_at=None,
            note="No historical settlement rates were returned; futures P&L excludes funding.",
        )
    gaps = [
        right[0] - left[0]
        for left, right in zip(selected, selected[1:], strict=False)
    ]
    partial = any(gap > timedelta(hours=12) for gap in gaps)
    return FundingCoverage(
        status="partial" if partial else "available",
        records=len(selected),
        first_event_at=_as_utc(selected[0][0]),
        last_event_at=_as_utc(selected[-1][0]),
        note=(
            "Funding events use the returned historical settlement rates."
            if not partial
            else "Funding history has gaps over 12 hours; uncovered settlements are excluded."
        ),
    )


def _strategy_trade(
    *,
    bars: list[CandlePoint],
    target_h1_snapshots: dict[int, MarketSnapshot],
    target_m15_snapshots: dict[int, MarketSnapshot],
    btc_h1_snapshots: dict[int, MarketSnapshot],
    btc_m15_snapshots: dict[int, MarketSnapshot],
    signal_index: int,
    end_index: int,
    symbol: str,
    market_type: MarketType,
    side: TradeSide,
    funding: list[tuple[datetime, Decimal]],
    spread_bps: Decimal,
    slippage_bps: Decimal,
) -> tuple[BacktestTrade | None, int, bool]:
    signal_bar = bars[signal_index]
    signal_close = _as_utc(signal_bar.opened_at) + BAR_INTERVAL
    hourly_open = _latest_closed_hour(signal_close)
    h1_key = _millis(hourly_open)
    m15_key = _millis(signal_bar.opened_at)
    btc_h1 = btc_h1_snapshots.get(h1_key)
    btc_m15 = btc_m15_snapshots.get(m15_key)
    regime = _btc_regime(btc_h1, btc_m15)
    score, levels = _eligible_setup(
        symbol=f"{symbol[:-4]}/USDT",
        side=side,
        signal_bar=signal_bar,
        h1=target_h1_snapshots.get(h1_key),
        m15=target_m15_snapshots.get(m15_key),
        btc_regime=regime,
    ) or (None, {})
    if score is None:
        return None, signal_index + 1, False

    entry_index = signal_index + 1
    if entry_index >= end_index or entry_index >= len(bars):
        return None, signal_index + 1, False
    entry_bar = bars[entry_index]
    if entry_bar.opened_at != signal_close:
        return None, signal_index + 1, False
    entry = entry_bar.open
    stop = Decimal(str(levels["stop_loss"]))
    target = Decimal(str(levels["tp1"]))
    if not _valid_levels(side, entry, levels):
        return None, signal_index + 1, False
    exit_details = _find_exit(
        bars,
        entry_index=entry_index,
        end_index=end_index,
        side=side,
        stop=stop,
        target=target,
    )
    if exit_details is None:
        return None, signal_index + 1, True
    exit_index, exit_price, reason = exit_details
    trade = _trade_from_exit(
        side=side,
        score=score,
        signal_bar=signal_bar,
        entry_bar=entry_bar,
        exit_bar=bars[exit_index],
        entry=entry,
        exit_price=exit_price,
        stop=stop,
        target=target,
        exit_reason=reason,
        market_type=market_type,
        funding=funding,
        spread_bps=spread_bps,
        slippage_bps=slippage_bps,
    )
    return trade, exit_index + 1, False


def run_backtest(
    *,
    run_id: str,
    created_at: datetime,
    symbol: str,
    days: int,
    requested_start: datetime,
    requested_end: datetime,
    spot_bars: list[CandlePoint],
    futures_bars: list[CandlePoint],
    btc_spot_bars: list[CandlePoint],
    funding: list[tuple[datetime, Decimal]],
    spread_bps: Decimal,
    slippage_bps: Decimal,
    data_sha256: str,
) -> BacktestResult:
    """Evaluate one pair on spot and swap using a chronological holdout."""
    start_at, end_at = _as_utc(requested_start), _as_utc(requested_end)
    evaluated_spot = [
        bar for bar in spot_bars if start_at <= _as_utc(bar.opened_at) < end_at
    ]
    if len(evaluated_spot) < 4:
        raise ValueError("Not enough closed 15-minute candles for a backtest.")
    split_position = max(1, min(len(evaluated_spot) - 1, int(len(evaluated_spot) * 0.70)))
    split_at = _as_utc(evaluated_spot[split_position].opened_at)
    selected_ranges: list[tuple[PeriodName, datetime, datetime]] = [
        ("development", start_at, split_at),
        ("out_of_sample", split_at, end_at),
    ]

    series_by_market: dict[MarketType, list[CandlePoint]] = {
        "spot": spot_bars,
        "futures": futures_bars,
    }
    btc_bars = btc_spot_bars
    btc_h1_bars = _hourly_bars(btc_bars)
    btc_m15_snapshots = _indicator_snapshots(
        btc_bars, symbol="BTC/USDT", timeframe=Timeframe.M15
    )
    btc_h1_snapshots = _indicator_snapshots(
        btc_h1_bars, symbol="BTC/USDT", timeframe=Timeframe.H1
    )
    segments: list[BacktestSegment] = []
    for market_type, bars in series_by_market.items():
        h1_bars = _hourly_bars(bars)
        m15_snapshots = _indicator_snapshots(
            bars, symbol=f"{symbol[:-4]}/USDT", timeframe=Timeframe.M15
        )
        h1_snapshots = _indicator_snapshots(
            h1_bars, symbol=f"{symbol[:-4]}/USDT", timeframe=Timeframe.H1
        )
        supported_sides: tuple[TradeSide, ...] = (
            (TradeSide.LONG,) if market_type == "spot" else (TradeSide.LONG, TradeSide.SHORT)
        )
        for period, period_start, period_end in selected_ranges:
            first_index = next(
                (i for i, bar in enumerate(bars) if _as_utc(bar.opened_at) >= period_start),
                len(bars),
            )
            end_index = next(
                (i for i, bar in enumerate(bars) if _as_utc(bar.opened_at) >= period_end),
                len(bars),
            )
            for side in supported_sides:
                trades: list[BacktestTrade] = []
                excluded = 0
                index = first_index
                while index < end_index:
                    # Avoid running indicators on a stale/gapped EMA history.
                    m15_position = index
                    if not _has_recent_warmup(bars, m15_position, 99):
                        index += 1
                        continue
                    signal_close = _as_utc(bars[index].opened_at) + BAR_INTERVAL
                    hour_open = _latest_closed_hour(signal_close)
                    h1_position = next(
                        (
                            pos
                            for pos, hourly in enumerate(h1_bars)
                            if _as_utc(hourly.opened_at) == hour_open
                        ),
                        -1,
                    )
                    if h1_position < 98 or not _has_recent_warmup(
                        h1_bars, h1_position, 99, timedelta(hours=1)
                    ):
                        index += 1
                        continue
                    trade, next_index, censored = _strategy_trade(
                        bars=bars,
                        target_h1_snapshots=h1_snapshots,
                        target_m15_snapshots=m15_snapshots,
                        btc_h1_snapshots=btc_h1_snapshots,
                        btc_m15_snapshots=btc_m15_snapshots,
                        signal_index=index,
                        end_index=end_index,
                        symbol=symbol,
                        market_type=market_type,
                        side=side,
                        funding=funding,
                        spread_bps=spread_bps,
                        slippage_bps=slippage_bps,
                    )
                    if trade is None:
                        if censored:
                            excluded += 1
                        index += 1
                    else:
                        trades.append(trade)
                        index = max(next_index, index + 1)
                metrics, curve = _metrics(trades, excluded=excluded, period_start=period_start)
                segments.append(
                    BacktestSegment(
                        market_type=market_type,
                        side=side.value,
                        period=period,
                        period_start=period_start,
                        period_end=period_end,
                        metrics=metrics,
                        equity_curve=curve,
                        trades=trades,
                    )
                )

    coverage: list[CandleCoverage] = []
    coverage_sources = [
        (symbol, "spot", spot_bars),
        (symbol, "futures", futures_bars),
    ]
    if symbol != "BTCUSDT":
        coverage_sources.append(("BTCUSDT", "spot", btc_spot_bars))
    for source_symbol, market_type, bars in coverage_sources:
        coverage.append(
            _coverage(
                symbol=source_symbol,
                market_type=market_type,
                bars=bars,
                start_at=start_at,
                end_at=end_at,
            )
        )
    fund_coverage = _funding_coverage(funding, start_at, end_at)
    notes = [
        "Historical and hypothetical only. Results are not a forecast, recommendation, or "
        "guarantee of profit.",
        "The 70/100 rule score is an eligibility screen, not a probability or expected win rate.",
        "One instrument is evaluated at a time. Spot is long-only; the swap is evaluated long "
        "and short.",
        "Only closed 15-minute candles are used. Hourly bars aggregate four consecutive "
        "closed 15-minute candles.",
        "Stops take precedence when a stop and target touch within the same candle. Gaps are "
        "not interpolated.",
        "Entries use the next 15-minute open, must remain in the EMA entry zone, and last at "
        "most four bars.",
        "Spread and slippage are assumptions because historical order-book depth is not "
        "included.",
        "Live quote and order-book quality gates are not simulated from OHLCV candles.",
        "The first 70% is development; the final 30% is out-of-sample. No random shuffle or "
        "parameter fitting is used.",
        "EMA-99 stop and EMA-7 TP1 are inherited rules under evaluation, not validated for a "
        "15–60-minute hold.",
    ]
    if fund_coverage.status in {"partial", "unavailable"}:
        notes.append(
            "Futures net results include only returned historical funding observations; "
            "uncovered settlements are excluded."
        )
    return BacktestResult(
        id=run_id,
        created_at=_as_utc(created_at),
        symbol=symbol,  # type: ignore[arg-type]
        requested_days=days,
        strategy=strategy_configuration(spread_bps=spread_bps, slippage_bps=slippage_bps),
        engine_version=ENGINE_VERSION,
        requested_start=start_at,
        requested_end=end_at,
        development_end=split_at,
        out_of_sample_start=split_at,
        data_sha256=data_sha256,
        candle_coverage=coverage,
        funding_coverage=fund_coverage,
        segments=segments,
        notes=notes,
        status=StrategyLabStatus(
            paid_committee_review_enabled=False,
            trading_enabled=False,
            proposal_creation_enabled=False,
            notice=(
                "Committee review, proposal creation, permits, and orders are disabled for "
                "Strategy Laboratory runs."
            ),
        ),
    )
