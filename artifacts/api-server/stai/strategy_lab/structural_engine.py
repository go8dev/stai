"""Isolated, point-in-time support/resistance pullback challenger."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from typing import Literal

from stai.marketdata.schemas import CandlePoint, MarketType
from stai.strategies.pullback import EntryBar, indicator_series
from stai.strategy_lab.engine import (
    _as_utc,
    _funding_coverage,
    _quantize,
)
from stai.strategy_lab.schemas import BacktestMetrics, EquityPoint, TradeSide
from stai.strategy_lab.structural_schemas import (
    EntryMethod,
    StructuralBacktestResult,
    StructuralCandidateEvidence,
    StructuralCandleCoverage,
    StructuralCostResult,
    StructuralEntryOrder,
    StructuralSegment,
    StructuralStrategyConfiguration,
    StructuralTrade,
    StructuralWindow,
)
from stai.trading.accounting import FeeSchedule

STRATEGY_VERSION = "stai-structural-pullback-v1"
ENGINE_VERSION = "structural-1m-point-in-time-v1"
BAR_1M = timedelta(minutes=1)
BAR_15M = timedelta(minutes=15)
BAR_1H = timedelta(hours=1)
DEVELOPMENT_START = datetime(2026, 9, 19, 14, 0, tzinfo=UTC)
DEVELOPMENT_END = datetime(2026, 10, 19, 14, 0, tzinfo=UTC)
FUTURE_VALIDATION_START = datetime(2026, 11, 18, 14, 30, tzinfo=UTC)
FUTURE_VALIDATION_END = FUTURE_VALIDATION_START + timedelta(days=30)
HOLDING_PERIODS = (60, 240)
ENTRY_METHODS: tuple[EntryMethod, ...] = ("next_candle_market", "anchor_limit")
COST_SENSITIVITY_BPS = (0, 5, 10)
NOTIONAL = Decimal("100")
INITIAL_EQUITY = Decimal("1000")
LEVERAGE = Decimal("1")
ZONE_CLUSTER_ATR = Decimal("0.5")
SUPPORT_PROXIMITY_ATR = Decimal("0.5")
MAX_CHASE_ATR = Decimal("1")
STOP_BUFFER_ATR = Decimal("0.25")
TARGET_OFFSET_ATR = Decimal("0.10")
MINIMUM_NET_RR = Decimal("2")
BASE_MARKET_COST_BPS = 5
_MONEY = Decimal("0.000001")
_PERCENT = Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class Zone:
    kind: Literal["support", "resistance"]
    lower: Decimal
    upper: Decimal
    known_at: datetime
    source_count: int
    interaction_count: int


@dataclass(frozen=True, slots=True)
class Candidate:
    candidate_id: str
    symbol: str
    market_type: MarketType
    side: TradeSide
    anchor_at: datetime
    signal_at: datetime
    confirmation_at: datetime
    anchor_high: Decimal
    anchor_low: Decimal
    anchor_atr: Decimal
    atr15: Decimal
    entry_ema25: Decimal
    entry_ema99: Decimal
    trend_close: Decimal
    trend_ema25: Decimal
    trend_ema99: Decimal
    btc_close: Decimal
    btc_ema25: Decimal
    btc_ema99: Decimal
    confirmation_close: Decimal
    stop: Decimal
    target: Decimal
    support_zone: Zone
    opposing_zone: Zone

    @property
    def limit_price(self) -> Decimal:
        return self.anchor_high if self.side == "long" else self.anchor_low


def strategy_configuration() -> StructuralStrategyConfiguration:
    return StructuralStrategyConfiguration(
        strategy_version=STRATEGY_VERSION,
        trend_timeframe="1h",
        entry_timeframe="15m",
        swing_left_bars=2,
        swing_right_bars=2,
        zone_cluster_atr=ZONE_CLUSTER_ATR,
        support_resistance_proximity_atr=SUPPORT_PROXIMITY_ATR,
        confirmation_expiry_bars=4,
        max_chase_atr=MAX_CHASE_ATR,
        structural_stop_buffer_atr=STOP_BUFFER_ATR,
        target_offset_before_zone_atr=TARGET_OFFSET_ATR,
        minimum_net_reward_risk=MINIMUM_NET_RR,
        holding_periods_minutes=list(HOLDING_PERIODS),
        entry_methods=list(ENTRY_METHODS),
        market_cost_sensitivity_bps=list(COST_SENSITIVITY_BPS),
        notional_usdt=NOTIONAL,
        leverage=LEVERAGE,
        no_lookahead_rule=(
            "Only completed candles and levels confirmed by the simulated timestamp are usable. "
            "A 1h swing needs two completed candles to its right."
        ),
        execution_assumptions=[
            "The market-entry arm uses the first 1m open after confirmation; market orders "
            "and stop/time exits use 0, 5, or 10 bps adverse modeled-cost sensitivity.",
            "The anchor-limit arm requires a 1m candle to trade at least one exchange tick "
            "through the limit with nonzero volume; a mere touch is unfilled.",
            "Minute OHLCV cannot prove queue position, partial fills, intraminute sequencing, "
            "or market impact. These fills are approximations.",
            "Resting limit entries and take-profit exits use maker fees and no added market cost. "
            "Stop and time exits use taker fees.",
            "Fee defaults are not account-specific. Funding uses only returned historical rates.",
            "Each segment uses fixed 100 USDT notional at 1x, no compounding, and no overlapping "
            "positions. The 0.25 ATR stop buffer, 0.10 ATR target offset, and 2:1 net hurdle "
            "are research hypotheses, not validated rules.",
        ],
    )


def research_windows(now: datetime) -> tuple[StructuralWindow, StructuralWindow]:
    now = _as_utc(now)
    return (
        StructuralWindow(
            sample_period="development",
            starts_at=DEVELOPMENT_START,
            ends_at=DEVELOPMENT_END,
            status="ready",
            note="Pre-inspected development window; the viewed 19 Oct–18 Nov window is excluded.",
        ),
        StructuralWindow(
            sample_period="future_validation",
            starts_at=FUTURE_VALIDATION_START,
            ends_at=FUTURE_VALIDATION_END,
            status="ready" if now >= FUTURE_VALIDATION_END else "pending",
            note=(
                "Frozen 30-day validation window; locked until completion and reserved for "
                "one evaluation per instrument."
                if now < FUTURE_VALIDATION_END
                else "Reserved validation data is complete; this instrument may be evaluated once."
            ),
        ),
    )


def _decimal(value: Decimal | float | int) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _close_at(bar: CandlePoint, interval: timedelta) -> datetime:
    return _as_utc(bar.opened_at) + interval


def _point_in_time_atr(
    bars: list[CandlePoint], interval: timedelta, period: int = 14
) -> dict[datetime, Decimal]:
    result: dict[datetime, Decimal] = {}
    true_ranges: list[Decimal] = []
    previous_close: Decimal | None = None
    previous_at: datetime | None = None
    for bar in sorted(bars, key=lambda item: _as_utc(item.opened_at)):
        opened = _as_utc(bar.opened_at)
        if not bar.complete:
            true_ranges.clear()
            previous_close = None
            previous_at = None
            continue
        if previous_at is not None and opened != previous_at + interval:
            true_ranges.clear()
            previous_close = None
        if previous_close is not None:
            true_ranges.append(
                max(
                    bar.high - bar.low,
                    abs(bar.high - previous_close),
                    abs(bar.low - previous_close),
                )
            )
            if len(true_ranges) > period:
                true_ranges.pop(0)
            if len(true_ranges) == period:
                result[opened] = sum(true_ranges, Decimal("0")) / Decimal(period)
        previous_close = bar.close
        previous_at = opened
    return result


def _latest_indicator(
    series: dict[datetime, EntryBar],
    at: datetime,
    interval: timedelta,
) -> EntryBar | None:
    eligible = [
        (opened, value)
        for opened, value in series.items()
        if opened + interval <= at and value.candle.complete
    ]
    return max(eligible, key=lambda item: item[0])[1] if eligible else None


def _direction_ok(bar: EntryBar | None, side: TradeSide, *, hourly: bool) -> bool:
    if bar is None or bar.ema25 is None or bar.ema99 is None:
        return False
    close = float(bar.candle.close)
    if side == "long":
        return bar.ema25 > bar.ema99 and (not hourly or close > bar.ema99)
    return bar.ema25 < bar.ema99 and (not hourly or close < bar.ema99)


def _zone_levels(
    *,
    as_of: datetime,
    hourly: list[CandlePoint],
    m15: list[CandlePoint],
    atr1h: dict[datetime, Decimal],
) -> tuple[list[Zone], list[Zone]]:
    """Build support/resistance only from completed levels knowable at ``as_of``."""
    as_of = _as_utc(as_of)
    current_hour = _latest_indicator(indicator_series(hourly, BAR_1H), as_of, BAR_1H)
    if current_hour is None:
        return [], []
    hour_atr = atr1h.get(_as_utc(current_hour.candle.opened_at))
    if hour_atr is None or hour_atr <= 0:
        return [], []
    tolerance = hour_atr * ZONE_CLUSTER_ATR
    raw: dict[Literal["support", "resistance"], list[tuple[Decimal, datetime]]] = {
        "support": [],
        "resistance": [],
    }

    completed_day = as_of.date() - timedelta(days=1)
    day_start = datetime.combine(completed_day, time.min, tzinfo=UTC)
    prior_levels = [
        bar
        for bar in m15
        if bar.complete
        and day_start <= _as_utc(bar.opened_at)
        and _as_utc(bar.opened_at) < day_start + timedelta(days=1)
        and _close_at(bar, BAR_15M) <= as_of
    ]
    if prior_levels:
        known_at = day_start + timedelta(days=1)
        raw["support"].append((min(bar.low for bar in prior_levels), known_at))
        raw["resistance"].append((max(bar.high for bar in prior_levels), known_at))

    ordered_hourly = sorted(
        (bar for bar in hourly if bar.complete), key=lambda item: _as_utc(item.opened_at)
    )
    for index in range(2, len(ordered_hourly) - 2):
        pivot = ordered_hourly[index]
        right = ordered_hourly[index + 2]
        confirmed_at = _close_at(right, BAR_1H)
        if confirmed_at > as_of:
            break
        neighborhood = ordered_hourly[index - 2 : index + 3]
        if any(
            _as_utc(b.opened_at) != _as_utc(a.opened_at) + BAR_1H
            for a, b in zip(neighborhood, neighborhood[1:], strict=False)
        ):
            continue
        if all(pivot.low < bar.low for j, bar in enumerate(neighborhood) if j != 2):
            raw["support"].append((pivot.low, confirmed_at))
        if all(pivot.high > bar.high for j, bar in enumerate(neighborhood) if j != 2):
            raw["resistance"].append((pivot.high, confirmed_at))

    def cluster(kind: Literal["support", "resistance"]) -> list[Zone]:
        levels = sorted(raw[kind], key=lambda item: item[0])
        groups: list[list[tuple[Decimal, datetime]]] = []
        for level in levels:
            if not groups or level[0] - groups[-1][0][0] > tolerance:
                groups.append([level])
            elif level[0] - groups[-1][0][0] <= tolerance:
                groups[-1].append(level)
        zones: list[Zone] = []
        for group in groups:
            lower = min(price for price, _ in group)
            upper = max(price for price, _ in group)
            known_at = max(at for _, at in group)
            interactions = sum(
                1
                for bar in m15
                if bar.complete
                and _close_at(bar, BAR_15M) > known_at
                and _close_at(bar, BAR_15M) <= as_of
                and bar.low <= upper
                and bar.high >= lower
            )
            zones.append(Zone(kind, lower, upper, known_at, len(group), interactions))
        return zones

    return cluster("support"), cluster("resistance")


def _nearest_support(zones: list[Zone], reference: Decimal) -> Zone | None:
    eligible = [zone for zone in zones if zone.lower <= reference]
    return (
        min(eligible, key=lambda zone: max(Decimal("0"), reference - zone.upper))
        if eligible
        else None
    )


def _nearest_resistance(zones: list[Zone], reference: Decimal) -> Zone | None:
    eligible = [zone for zone in zones if zone.upper >= reference]
    return (
        min(eligible, key=lambda zone: max(Decimal("0"), zone.lower - reference))
        if eligible
        else None
    )


def _next_resistance(zones: list[Zone], reference: Decimal) -> Zone | None:
    eligible = [zone for zone in zones if zone.lower > reference]
    return min(eligible, key=lambda zone: zone.lower) if eligible else None


def _next_support(zones: list[Zone], reference: Decimal) -> Zone | None:
    eligible = [zone for zone in zones if zone.upper < reference]
    return max(eligible, key=lambda zone: zone.upper) if eligible else None


def _setup_candidates(
    *,
    symbol: str,
    market_type: MarketType,
    m15: list[CandlePoint],
    hourly: list[CandlePoint],
    btc_hourly: list[CandlePoint],
) -> list[Candidate]:
    m15 = sorted((bar for bar in m15 if bar.complete), key=lambda item: _as_utc(item.opened_at))
    hourly = sorted(
        (bar for bar in hourly if bar.complete), key=lambda item: _as_utc(item.opened_at)
    )
    btc_hourly = sorted(
        (bar for bar in btc_hourly if bar.complete), key=lambda item: _as_utc(item.opened_at)
    )
    m15_indicators = indicator_series(m15, BAR_15M)
    h1_indicators = indicator_series(hourly, BAR_1H)
    btc_indicators = indicator_series(btc_hourly, BAR_1H)
    atr15 = _point_in_time_atr(m15, BAR_15M)
    atr1h = _point_in_time_atr(hourly, BAR_1H)
    sides: tuple[TradeSide, ...] = ("long",) if market_type == "spot" else ("long", "short")
    candidates: list[Candidate] = []

    for side in sides:
        anchor: tuple[int, CandlePoint, Decimal, Zone] | None = None
        for index, bar in enumerate(m15):
            opened = _as_utc(bar.opened_at)
            close_at = _close_at(bar, BAR_15M)
            current = m15_indicators.get(opened)
            atr = atr15.get(opened)
            h1 = _latest_indicator(h1_indicators, close_at, BAR_1H)
            btc_h1 = (
                h1 if symbol == "BTCUSDT" else _latest_indicator(btc_indicators, close_at, BAR_1H)
            )
            trend_ok = _direction_ok(h1, side, hourly=True) and (
                symbol == "BTCUSDT" or _direction_ok(btc_h1, side, hourly=True)
            )
            structure_ok = _direction_ok(current, side, hourly=False)
            close = bar.close
            ema99_ok = (
                current is not None
                and current.ema99 is not None
                and (
                    float(close) > current.ema99 if side == "long" else float(close) < current.ema99
                )
            )
            if anchor is not None:
                anchor_index, anchor_bar, anchor_atr, support_or_resistance = anchor
                waited = index - anchor_index
                # A missing candle cancels the active setup; never interpolate it.
                if waited > 1 and _as_utc(m15[index - 1].opened_at) + BAR_15M != opened:
                    anchor = None
                    continue
                broken = (
                    close < support_or_resistance.lower
                    if side == "long"
                    else close > support_or_resistance.upper
                )
                if not trend_ok or not structure_ok or not ema99_ok or broken:
                    anchor = None
                    continue
                if not 1 <= waited <= 4:
                    anchor = None
                    continue
                if current is None or current.ema25 is None or atr is None or atr <= 0:
                    if waited == 4:
                        anchor = None
                    continue
                confirms = (
                    close > anchor_bar.high and float(close) > current.ema25
                    if side == "long"
                    else close < anchor_bar.low and float(close) < current.ema25
                )
                chase = close - anchor_bar.high if side == "long" else anchor_bar.low - close
                if confirms and chase <= atr * MAX_CHASE_ATR:
                    supports, resistances = _zone_levels(
                        as_of=close_at, hourly=hourly, m15=m15, atr1h=atr1h
                    )
                    opposing = (
                        _next_resistance(resistances, close)
                        if side == "long"
                        else _next_support(supports, close)
                    )
                    if opposing is not None:
                        stop = (
                            support_or_resistance.lower - STOP_BUFFER_ATR * atr
                            if side == "long"
                            else support_or_resistance.upper + STOP_BUFFER_ATR * atr
                        )
                        target = (
                            opposing.lower - TARGET_OFFSET_ATR * atr
                            if side == "long"
                            else opposing.upper + TARGET_OFFSET_ATR * atr
                        )
                        if stop > 0 and target > 0:
                            candidate_identity = (
                                f"{STRATEGY_VERSION}|{symbol}|{market_type}|{side}|"
                                f"{_as_utc(anchor_bar.opened_at).isoformat()}|{close_at.isoformat()}"
                            )
                            candidate_id = hashlib.sha256(
                                candidate_identity.encode("utf-8")
                            ).hexdigest()
                            candidates.append(
                                Candidate(
                                    candidate_id=candidate_id,
                                    symbol=symbol,
                                    market_type=market_type,
                                    side=side,
                                    anchor_at=_as_utc(anchor_bar.opened_at),
                                    signal_at=close_at,
                                    confirmation_at=close_at,
                                    anchor_high=anchor_bar.high,
                                    anchor_low=anchor_bar.low,
                                    anchor_atr=anchor_atr,
                                    atr15=atr,
                                    entry_ema25=Decimal(str(current.ema25)),
                                    entry_ema99=Decimal(str(current.ema99)),
                                    trend_close=h1.candle.close,
                                    trend_ema25=Decimal(str(h1.ema25)),
                                    trend_ema99=Decimal(str(h1.ema99)),
                                    btc_close=btc_h1.candle.close,
                                    btc_ema25=Decimal(str(btc_h1.ema25)),
                                    btc_ema99=Decimal(str(btc_h1.ema99)),
                                    confirmation_close=close,
                                    stop=stop,
                                    target=target,
                                    support_zone=(
                                        support_or_resistance
                                        if side == "long"
                                        else support_or_resistance
                                    ),
                                    opposing_zone=opposing,
                                )
                            )
                    anchor = None
                    continue
                if waited == 4:
                    anchor = None
                continue

            if (
                current is None
                or current.ema25 is None
                or atr is None
                or atr <= 0
                or not trend_ok
                or not structure_ok
                or not ema99_ok
            ):
                continue
            ema25 = Decimal(str(current.ema25))
            touches = bar.low <= ema25 <= bar.high
            if not touches:
                continue
            supports, resistances = _zone_levels(
                as_of=close_at, hourly=hourly, m15=m15, atr1h=atr1h
            )
            reference = ema25
            nearest = (
                _nearest_support(supports, reference)
                if side == "long"
                else _nearest_resistance(resistances, reference)
            )
            if nearest is None:
                continue
            distance = (
                max(Decimal("0"), reference - nearest.upper)
                if side == "long"
                else max(Decimal("0"), nearest.lower - reference)
            )
            if distance > atr * SUPPORT_PROXIMITY_ATR:
                continue
            anchor = (index, bar, atr, nearest)
    return candidates


def _candidate_method_id(candidate: Candidate, method: EntryMethod) -> str:
    return hashlib.sha256(f"{candidate.candidate_id}|{method}".encode()).hexdigest()


def _adverse_price(price: Decimal, side: TradeSide, *, is_entry: bool, bps: int) -> Decimal:
    factor = Decimal(bps) / Decimal(10_000)
    if not bps:
        return price
    if (side == "long" and is_entry) or (side == "short" and not is_entry):
        return price * (Decimal("1") + factor)
    return price * (Decimal("1") - factor)


def _planned_terms(
    *,
    entry: Decimal,
    raw_entry: Decimal,
    stop: Decimal,
    target: Decimal,
    side: TradeSide,
    market_type: MarketType,
    method: EntryMethod,
    market_cost_bps: int,
) -> tuple[Decimal | None, Decimal, Decimal]:
    direction = Decimal("1") if side == "long" else Decimal("-1")
    adjusted_entry = (
        _adverse_price(entry, side, is_entry=True, bps=market_cost_bps)
        if method == "next_candle_market"
        else entry
    )
    if not (stop < adjusted_entry < target if side == "long" else target < adjusted_entry < stop):
        return None, Decimal("0"), Decimal("0")
    quantity = NOTIONAL / adjusted_entry
    fees = FeeSchedule()
    entry_liquidity = "taker" if method == "next_candle_market" else "maker"
    entry_fee = quantity * adjusted_entry * fees.rate(market_type, entry_liquidity)
    target_fee = quantity * target * fees.rate(market_type, "maker")
    stop_fill = _adverse_price(stop, side, is_entry=False, bps=market_cost_bps)
    stop_fee = quantity * stop_fill * fees.rate(market_type, "taker")
    reward = quantity * (target - adjusted_entry) * direction - entry_fee - target_fee
    risk = -(quantity * (stop_fill - adjusted_entry) * direction) + entry_fee + stop_fee
    if risk <= 0 or reward <= 0:
        return None, max(Decimal("0"), risk), entry_fee + target_fee + stop_fee
    entry_market_cost = (
        quantity * abs(adjusted_entry - raw_entry)
        if method == "next_candle_market"
        else Decimal("0")
    )
    stop_market_cost = quantity * abs(stop_fill - stop)
    return (
        reward / risk,
        risk,
        entry_fee + target_fee + stop_fee + entry_market_cost + stop_market_cost,
    )


def _find_minute_fill(
    *,
    candidate: Candidate,
    method: EntryMethod,
    minute_bars: list[CandlePoint],
    tick_size: Decimal,
    sample_end: datetime,
) -> tuple[StructuralEntryOrder, int | None, Decimal | None, Decimal | None]:
    proposed = candidate.limit_price if method == "anchor_limit" else Decimal("0")
    expiry = (
        candidate.confirmation_at + BAR_15M * 4
        if method == "anchor_limit"
        else candidate.confirmation_at + BAR_1M
    )
    if expiry > sample_end:
        return (
            StructuralEntryOrder(
                candidate_id=_candidate_method_id(candidate, method),
                signal_at=candidate.signal_at,
                side=candidate.side,
                entry_method=method,
                proposed_price=proposed,
                planned_net_reward_risk=None,
                expires_at=expiry,
                status="untestable",
                filled_at=None,
                fill_price=None,
                reason="The complete entry window is outside the selected sample.",
            ),
            None,
            None,
            None,
        )
    times = [_as_utc(bar.opened_at) for bar in minute_bars]
    start_index = next((i for i, at in enumerate(times) if at >= candidate.confirmation_at), None)
    if start_index is None or times[start_index] != candidate.confirmation_at:
        return (
            StructuralEntryOrder(
                candidate_id=_candidate_method_id(candidate, method),
                signal_at=candidate.signal_at,
                side=candidate.side,
                entry_method=method,
                proposed_price=proposed,
                planned_net_reward_risk=None,
                expires_at=expiry,
                status="untestable",
                filled_at=None,
                fill_price=None,
                reason="The first required 1m candle after confirmation is missing.",
            ),
            None,
            None,
            None,
        )
    if method == "next_candle_market":
        bar = minute_bars[start_index]
        if not bar.complete or bar.volume <= 0:
            return (
                StructuralEntryOrder(
                    candidate_id=_candidate_method_id(candidate, method),
                    signal_at=candidate.signal_at,
                    side=candidate.side,
                    entry_method=method,
                    proposed_price=bar.open,
                    planned_net_reward_risk=None,
                    expires_at=expiry,
                    status="untestable",
                    filled_at=None,
                    fill_price=None,
                    reason="The first 1m market-entry candle is incomplete or has no volume.",
                ),
                None,
                None,
                None,
            )
        return (
            StructuralEntryOrder(
                candidate_id=_candidate_method_id(candidate, method),
                signal_at=candidate.signal_at,
                side=candidate.side,
                entry_method=method,
                proposed_price=bar.open,
                planned_net_reward_risk=None,
                expires_at=expiry,
                status="filled",
                filled_at=_as_utc(bar.opened_at),
                fill_price=bar.open,
                reason="Modeled fill at the first 1m open after the confirmed signal.",
            ),
            start_index,
            bar.open,
            bar.open,
        )

    expected_at = candidate.confirmation_at
    touched_exactly = False
    for index in range(start_index, len(minute_bars)):
        bar = minute_bars[index]
        at = _as_utc(bar.opened_at)
        if at >= expiry:
            break
        if at != expected_at or not bar.complete:
            return (
                StructuralEntryOrder(
                    candidate_id=_candidate_method_id(candidate, method),
                    signal_at=candidate.signal_at,
                    side=candidate.side,
                    entry_method=method,
                    proposed_price=proposed,
                    planned_net_reward_risk=None,
                    expires_at=expiry,
                    status="untestable",
                    filled_at=None,
                    fill_price=None,
                    reason="A missing or incomplete 1m candle prevents fill verification.",
                ),
                None,
                None,
                None,
            )
        if bar.volume > 0:
            if candidate.side == "long":
                through = bar.low <= proposed - tick_size
                touched_exactly = touched_exactly or bar.low <= proposed
                if through:
                    fill = bar.open if bar.open <= proposed - tick_size else proposed
                    return (
                        StructuralEntryOrder(
                            candidate_id=_candidate_method_id(candidate, method),
                            signal_at=candidate.signal_at,
                            side=candidate.side,
                            entry_method=method,
                            proposed_price=proposed,
                            planned_net_reward_risk=None,
                            expires_at=expiry,
                            status="filled",
                            filled_at=at,
                            fill_price=fill,
                            reason=(
                                "1m candle traded at least one tick through the limit; "
                                "gap-through opens receive the better opening price."
                            ),
                        ),
                        index,
                        fill,
                        fill,
                    )
            else:
                through = bar.high >= proposed + tick_size
                touched_exactly = touched_exactly or bar.high >= proposed
                if through:
                    fill = bar.open if bar.open >= proposed + tick_size else proposed
                    return (
                        StructuralEntryOrder(
                            candidate_id=_candidate_method_id(candidate, method),
                            signal_at=candidate.signal_at,
                            side=candidate.side,
                            entry_method=method,
                            proposed_price=proposed,
                            planned_net_reward_risk=None,
                            expires_at=expiry,
                            status="filled",
                            filled_at=at,
                            fill_price=fill,
                            reason=(
                                "1m candle traded at least one tick through the limit; "
                                "gap-through opens receive the better opening price."
                            ),
                        ),
                        index,
                        fill,
                        fill,
                    )
        expected_at += BAR_1M
    if expected_at < expiry:
        return (
            StructuralEntryOrder(
                candidate_id=_candidate_method_id(candidate, method),
                signal_at=candidate.signal_at,
                side=candidate.side,
                entry_method=method,
                proposed_price=proposed,
                planned_net_reward_risk=None,
                expires_at=expiry,
                status="untestable",
                filled_at=None,
                fill_price=None,
                reason="The full limit-order window is not covered by continuous 1m history.",
            ),
            None,
            None,
            None,
        )
    return (
        StructuralEntryOrder(
            candidate_id=_candidate_method_id(candidate, method),
            signal_at=candidate.signal_at,
            side=candidate.side,
            entry_method=method,
            proposed_price=proposed,
            planned_net_reward_risk=None,
            expires_at=expiry,
            status="unfilled",
            filled_at=None,
            fill_price=None,
            reason=(
                "Only an exact touch was observed; no one-tick-through evidence."
                if touched_exactly
                else "The anchor limit was not reached before its four-bar expiry."
            ),
        ),
        None,
        None,
        None,
    )


def _find_exit(
    *,
    minute_bars: list[CandlePoint],
    entry_index: int,
    candidate: Candidate,
    hold_minutes: int,
    cost_bps: int,
    sample_end: datetime,
) -> tuple[int, Decimal, Decimal, Literal["stop_loss", "take_profit", "time_limit"]] | None:
    entry_at = _as_utc(minute_bars[entry_index].opened_at)
    time_exit_at = entry_at + timedelta(minutes=hold_minutes)
    if time_exit_at >= sample_end:
        return None
    expected = entry_at
    for index in range(entry_index, len(minute_bars)):
        bar = minute_bars[index]
        at = _as_utc(bar.opened_at)
        if at >= time_exit_at:
            if at != time_exit_at or at + BAR_1M > sample_end or not bar.complete:
                return None
            raw_exit = bar.open
            actual_exit = _adverse_price(raw_exit, candidate.side, is_entry=False, bps=cost_bps)
            return index, actual_exit, raw_exit, "time_limit"
        if at != expected or not bar.complete:
            return None
        raw_stop = (
            min(bar.open, candidate.stop)
            if candidate.side == "long" and bar.open < candidate.stop
            else max(bar.open, candidate.stop)
            if candidate.side == "short" and bar.open > candidate.stop
            else candidate.stop
        )
        stop_hit = (
            bar.low <= candidate.stop if candidate.side == "long" else bar.high >= candidate.stop
        )
        if stop_hit:
            actual = _adverse_price(raw_stop, candidate.side, is_entry=False, bps=cost_bps)
            return index, actual, raw_stop, "stop_loss"
        target_hit = (
            bar.high >= candidate.target
            if candidate.side == "long"
            else bar.low <= candidate.target
        )
        if target_hit and index != entry_index:
            raw_target = (
                max(bar.open, candidate.target)
                if candidate.side == "long"
                else min(bar.open, candidate.target)
            )
            return index, raw_target, raw_target, "take_profit"
        expected += BAR_1M
    return None


def _trade(
    *,
    candidate: Candidate,
    method: EntryMethod,
    order: StructuralEntryOrder,
    minute_bars: list[CandlePoint],
    entry_index: int,
    entry: Decimal,
    raw_entry: Decimal,
    exit_index: int,
    exit_price: Decimal,
    raw_exit: Decimal,
    exit_reason: Literal["stop_loss", "take_profit", "time_limit"],
    cost_bps: int,
    funding: list[tuple[datetime, Decimal]],
) -> StructuralTrade:
    side = candidate.side
    direction = Decimal("1") if side == "long" else Decimal("-1")
    quantity = NOTIONAL / entry
    entry_type = "taker" if method == "next_candle_market" else "maker"
    exit_type = "maker" if exit_reason == "take_profit" else "taker"
    fees = FeeSchedule()
    entry_fee = quantity * entry * fees.rate(candidate.market_type, entry_type)
    exit_fee = quantity * exit_price * fees.rate(candidate.market_type, exit_type)
    market_cost = quantity * abs(entry - raw_entry) + quantity * abs(exit_price - raw_exit)
    # Minute OHLCV cannot identify the exact intraminute fill or exit time.
    entered_at = _as_utc(minute_bars[entry_index].opened_at)
    exit_open = _as_utc(minute_bars[exit_index].opened_at)
    exited_at = exit_open if exit_reason == "time_limit" else exit_open + BAR_1M
    funding_cost = Decimal("0")
    if candidate.market_type == "futures":
        for funding_at, rate in funding:
            funding_at = _as_utc(funding_at)
            if entered_at < funding_at <= exited_at:
                funding_cost += NOTIONAL * rate * direction
    gross = quantity * (raw_exit - raw_entry) * direction
    net = gross - entry_fee - exit_fee - market_cost - funding_cost
    planned_rr, _, _ = _planned_terms(
        entry=order.fill_price or entry,
        raw_entry=raw_entry,
        stop=candidate.stop,
        target=candidate.target,
        side=side,
        market_type=candidate.market_type,
        method=method,
        market_cost_bps=BASE_MARKET_COST_BPS,
    )
    return StructuralTrade(
        candidate_id=order.candidate_id,
        signal_at=candidate.signal_at,
        entered_at=entered_at,
        exited_at=exited_at,
        side=side,
        entry_method=method,
        proposed_entry_price=order.proposed_price,
        entry_price=_quantize(entry, _PERCENT),
        stop_price=_quantize(candidate.stop, _PERCENT),
        target_price=_quantize(candidate.target, _PERCENT),
        planned_net_reward_risk=_quantize(planned_rr or Decimal("0"), _PERCENT),
        exit_price=_quantize(exit_price, _PERCENT),
        exit_reason=exit_reason,
        holding_minutes=max(0, int((exited_at - entered_at).total_seconds() // 60)),
        gross_pnl_usdt=_quantize(gross, _MONEY),
        fees_usdt=_quantize(entry_fee + exit_fee, _MONEY),
        maker_fees_usdt=_quantize(
            (entry_fee if entry_type == "maker" else Decimal("0"))
            + (exit_fee if exit_type == "maker" else Decimal("0")),
            _MONEY,
        ),
        taker_fees_usdt=_quantize(
            (entry_fee if entry_type == "taker" else Decimal("0"))
            + (exit_fee if exit_type == "taker" else Decimal("0")),
            _MONEY,
        ),
        funding_usdt=_quantize(funding_cost, _MONEY),
        modeled_market_cost_usdt=_quantize(market_cost, _MONEY),
        net_pnl_usdt=_quantize(net, _MONEY),
        stop_zone_lower=candidate.support_zone.lower,
        stop_zone_upper=candidate.support_zone.upper,
        target_zone_lower=candidate.opposing_zone.lower,
        target_zone_upper=candidate.opposing_zone.upper,
    )


def _metrics(
    trades: list[StructuralTrade],
    *,
    period_start: datetime,
    excluded: int,
    unfilled: int,
) -> tuple[BacktestMetrics, list[EquityPoint]]:
    wins = sum(trade.net_pnl_usdt > 0 for trade in trades)
    losses = sum(trade.net_pnl_usdt < 0 for trade in trades)
    breakeven = len(trades) - wins - losses
    total = sum((trade.net_pnl_usdt for trade in trades), Decimal("0"))
    gross_wins = sum(
        (trade.net_pnl_usdt for trade in trades if trade.net_pnl_usdt > 0), Decimal("0")
    )
    gross_losses = abs(
        sum(
            (trade.net_pnl_usdt for trade in trades if trade.net_pnl_usdt < 0),
            Decimal("0"),
        )
    )
    profit_factor = gross_wins / gross_losses if gross_losses else None
    equity = INITIAL_EQUITY
    peak = INITIAL_EQUITY
    max_drawdown = Decimal("0")
    max_drawdown_pct = Decimal("0")
    curve = [
        EquityPoint(
            at=_as_utc(period_start),
            equity_usdt=equity,
            cumulative_pnl_usdt=Decimal("0"),
        )
    ]
    for trade in sorted(trades, key=lambda item: item.exited_at):
        equity += trade.net_pnl_usdt
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
        if peak > 0:
            max_drawdown_pct = max(max_drawdown_pct, (peak - equity) / peak * 100)
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
        win_rate_pct=_quantize(Decimal(wins) / count * 100, _PERCENT) if count else None,
        expectancy_usdt=_quantize(total / count, _MONEY) if count else None,
        expectancy_pct_of_notional=(
            _quantize(total / Decimal(count) / NOTIONAL * 100, _PERCENT) if count else None
        ),
        profit_factor=_quantize(profit_factor, _PERCENT) if profit_factor is not None else None,
        profit_factor_note=(
            "No losing trades in this sample."
            if count and gross_losses == 0 and gross_wins > 0
            else "No completed trades."
            if count == 0
            else None
        ),
        max_drawdown_usdt=_quantize(max_drawdown, _MONEY),
        max_drawdown_pct=_quantize(max_drawdown_pct, _PERCENT),
        cumulative_pnl_usdt=_quantize(total, _MONEY),
        cumulative_return_pct=_quantize(total / INITIAL_EQUITY * 100, _PERCENT),
        ending_equity_usdt=_quantize(equity, _MONEY),
        total_fees_usdt=_quantize(sum((trade.fees_usdt for trade in trades), Decimal("0")), _MONEY),
        total_funding_usdt=_quantize(
            sum((trade.funding_usdt for trade in trades), Decimal("0")), _MONEY
        ),
        total_spread_cost_usdt=Decimal("0"),
        total_slippage_cost_usdt=_quantize(
            sum((trade.modeled_market_cost_usdt for trade in trades), Decimal("0")), _MONEY
        ),
        excluded_unclosed_trades=excluded,
        unfilled_entry_orders=unfilled,
        total_maker_fees_usdt=_quantize(
            sum((trade.maker_fees_usdt for trade in trades), Decimal("0")), _MONEY
        ),
        total_taker_fees_usdt=_quantize(
            sum((trade.taker_fees_usdt for trade in trades), Decimal("0")), _MONEY
        ),
    )
    return metrics, curve


def _coverage(
    *,
    symbol: str,
    market_type: MarketType,
    timeframe: Literal["1m", "15m", "1h"],
    bars: list[CandlePoint],
    start: datetime,
    end: datetime,
) -> StructuralCandleCoverage:
    interval = {"1m": BAR_1M, "15m": BAR_15M, "1h": BAR_1H}[timeframe]
    selected = sorted(
        [bar for bar in bars if bar.complete and start <= _as_utc(bar.opened_at) < end],
        key=lambda item: _as_utc(item.opened_at),
    )
    expected = int((end - start) / interval)
    opens = {_as_utc(bar.opened_at) for bar in selected}
    gaps: list[str] = []
    missing_start: datetime | None = None
    cursor = start
    while cursor < end:
        if cursor not in opens and missing_start is None:
            missing_start = cursor
        elif cursor in opens and missing_start is not None:
            gaps.append(f"{missing_start.isoformat()} to {cursor.isoformat()}")
            missing_start = None
        cursor += interval
    if missing_start is not None:
        gaps.append(f"{missing_start.isoformat()} to {end.isoformat()}")
    actual = len(opens)
    return StructuralCandleCoverage(
        symbol=symbol,  # type: ignore[arg-type]
        market_type=market_type,
        timeframe=timeframe,
        requested_start=start,
        requested_end=end,
        first_candle_at=_as_utc(selected[0].opened_at) if selected else None,
        last_candle_at=_as_utc(selected[-1].opened_at) if selected else None,
        actual_closed_candles=actual,
        expected_candles=expected,
        missing_candles=max(0, expected - actual),
        coverage_pct=(
            _quantize(Decimal(actual) / expected * 100, _PERCENT) if expected else Decimal("0")
        ),
        gap_ranges=gaps[:20],
    )


def _evidence(
    candidate: Candidate,
    *,
    method: EntryMethod,
    entry: Decimal,
    ratio: Decimal,
    estimated_cost: Decimal,
    data_sha256: str,
) -> StructuralCandidateEvidence:
    if method == "next_candle_market":
        entry = _adverse_price(entry, candidate.side, is_entry=True, bps=BASE_MARKET_COST_BPS)
    quantity = NOTIONAL / entry
    fees = FeeSchedule()
    direction = Decimal("1") if candidate.side == "long" else Decimal("-1")
    stop_fill = _adverse_price(
        candidate.stop, candidate.side, is_entry=False, bps=BASE_MARKET_COST_BPS
    )
    stop_loss = max(
        Decimal("0"),
        -(quantity * (stop_fill - entry) * direction)
        + quantity
        * entry
        * fees.rate(
            candidate.market_type,
            "taker" if method == "next_candle_market" else "maker",
        )
        + quantity * stop_fill * fees.rate(candidate.market_type, "taker"),
    )
    return StructuralCandidateEvidence(
        candidate_id=_candidate_method_id(candidate, method),
        symbol=candidate.symbol,  # type: ignore[arg-type]
        market_type=candidate.market_type,
        side=candidate.side,
        entry_method=method,
        strategy_version=STRATEGY_VERSION,
        signal_at=candidate.signal_at,
        confirmation_at=candidate.confirmation_at,
        anchor_price=candidate.limit_price,
        proposed_entry_price=entry,
        stop_price=candidate.stop,
        target_price=candidate.target,
        planned_net_reward_risk=_quantize(ratio, _PERCENT),
        notional_usdt=NOTIONAL,
        leverage=LEVERAGE,
        planned_loss_usdt=_quantize(stop_loss, _MONEY),
        estimated_cost_usdt=_quantize(estimated_cost, _MONEY),
        evidence={
            "anchor": {
                "at": candidate.anchor_at.isoformat(),
                "high": str(candidate.anchor_high),
                "low": str(candidate.anchor_low),
                "atr15": str(candidate.anchor_atr),
            },
            "confirmation": {
                "at": candidate.confirmation_at.isoformat(),
                "close": str(candidate.confirmation_close),
                "atr15": str(candidate.atr15),
            },
            "trend1h": {
                "close": str(candidate.trend_close),
                "ema25": str(candidate.trend_ema25),
                "ema99": str(candidate.trend_ema99),
            },
            "btc1h": {
                "close": str(candidate.btc_close),
                "ema25": str(candidate.btc_ema25),
                "ema99": str(candidate.btc_ema99),
            },
            "entry15m": {
                "ema25": str(candidate.entry_ema25),
                "ema99": str(candidate.entry_ema99),
            },
            "entryZoneKind": candidate.support_zone.kind,
            "entryZone": {
                "lower": str(candidate.support_zone.lower),
                "upper": str(candidate.support_zone.upper),
                "knownAt": candidate.support_zone.known_at.isoformat(),
                "sources": candidate.support_zone.source_count,
                "interactions": candidate.support_zone.interaction_count,
            },
            "opposingZone": {
                "lower": str(candidate.opposing_zone.lower),
                "upper": str(candidate.opposing_zone.upper),
                "knownAt": candidate.opposing_zone.known_at.isoformat(),
                "sources": candidate.opposing_zone.source_count,
                "interactions": candidate.opposing_zone.interaction_count,
            },
            "marketCostBpsForResearch": BASE_MARKET_COST_BPS,
            "sourceDataSha256": data_sha256,
            "proposalCompatible": True,
            "researchOnly": True,
        },
        committee_status="not_run",
    )


def _simulate_segment(
    *,
    candidates: list[Candidate],
    minute_bars: list[CandlePoint],
    tick_size: Decimal,
    market_type: MarketType,
    side: TradeSide,
    method: EntryMethod,
    hold_minutes: int,
    sample_start: datetime,
    sample_end: datetime,
    funding: list[tuple[datetime, Decimal]],
    data_sha256: str,
) -> tuple[StructuralSegment, list[StructuralCandidateEvidence]]:
    minute_bars = sorted(
        (bar for bar in minute_bars if bar.complete),
        key=lambda item: _as_utc(item.opened_at),
    )
    orders: list[StructuralEntryOrder] = []
    evidence: list[StructuralCandidateEvidence] = []
    per_cost_trades: dict[int, list[StructuralTrade]] = {bps: [] for bps in COST_SENSITIVITY_BPS}
    per_cost_excluded = dict.fromkeys(COST_SENSITIVITY_BPS, 0)
    diagnostics = {
        "reward_rejected": 0,
        "orders_placed": 0,
        "orders_filled": 0,
        "unfilled": 0,
        "cancelled": 0,
        "untestable": 0,
        "overlapping": 0,
    }
    busy_until: datetime | None = None
    for candidate in candidates:
        if busy_until is not None and candidate.signal_at < busy_until:
            diagnostics["overlapping"] += 1
            continue
        limit_ratio: Decimal | None = None
        if method == "anchor_limit":
            limit_ratio, _, limit_cost = _planned_terms(
                entry=candidate.limit_price,
                raw_entry=candidate.limit_price,
                stop=candidate.stop,
                target=candidate.target,
                side=side,
                market_type=market_type,
                method=method,
                market_cost_bps=BASE_MARKET_COST_BPS,
            )
            if limit_ratio is None or limit_ratio < MINIMUM_NET_RR:
                orders.append(
                    StructuralEntryOrder(
                        candidate_id=_candidate_method_id(candidate, method),
                        signal_at=candidate.signal_at,
                        side=side,
                        entry_method=method,
                        proposed_price=candidate.limit_price,
                        planned_net_reward_risk=(
                            _quantize(limit_ratio, _PERCENT) if limit_ratio else None
                        ),
                        expires_at=candidate.confirmation_at + BAR_15M * 4,
                        status="rejected",
                        filled_at=None,
                        fill_price=None,
                        reason=(
                            "The proposed anchor limit has invalid geometry or less than "
                            "2.00 net reward/risk after estimated costs."
                        ),
                    )
                )
                diagnostics["reward_rejected"] += 1
                continue
            evidence.append(
                _evidence(
                    candidate,
                    method=method,
                    entry=candidate.limit_price,
                    ratio=limit_ratio,
                    estimated_cost=limit_cost,
                    data_sha256=data_sha256,
                )
            )
        order, fill_index, fill_price, raw_fill = _find_minute_fill(
            candidate=candidate,
            method=method,
            minute_bars=minute_bars,
            tick_size=tick_size,
            sample_end=sample_end,
        )
        if limit_ratio is not None:
            order = order.model_copy(
                update={"planned_net_reward_risk": _quantize(limit_ratio, _PERCENT)}
            )
        if order.status == "untestable":
            orders.append(order)
            diagnostics["untestable"] += 1
            busy_until = order.expires_at
            continue
        if order.status == "unfilled":
            orders.append(order)
            diagnostics["orders_placed"] += 1
            diagnostics["unfilled"] += 1
            busy_until = order.expires_at
            continue
        if fill_index is None or fill_price is None or raw_fill is None:
            orders.append(order)
            diagnostics["cancelled"] += 1
            continue
        ratio, _, estimated_cost = _planned_terms(
            entry=fill_price,
            raw_entry=raw_fill,
            stop=candidate.stop,
            target=candidate.target,
            side=side,
            market_type=market_type,
            method=method,
            market_cost_bps=BASE_MARKET_COST_BPS,
        )
        order = order.model_copy(
            update={"planned_net_reward_risk": _quantize(ratio, _PERCENT) if ratio else None}
        )
        if ratio is None or ratio < MINIMUM_NET_RR:
            order = order.model_copy(
                update={
                    "status": "rejected",
                    "reason": (
                        "Planned net reward/risk at the base 5 bps market-cost assumption "
                        "is below 2.00 or has invalid geometry."
                    ),
                }
            )
            orders.append(order)
            diagnostics["reward_rejected"] += 1
            continue
        orders.append(order)
        diagnostics["orders_placed"] += 1
        diagnostics["orders_filled"] += 1
        if method == "next_candle_market":
            evidence.append(
                _evidence(
                    candidate,
                    method=method,
                    entry=fill_price,
                    ratio=ratio,
                    estimated_cost=estimated_cost,
                    data_sha256=data_sha256,
                )
            )
        busy_until = order.filled_at or candidate.confirmation_at
        successful_any = False
        for bps in COST_SENSITIVITY_BPS:
            actual_entry = (
                _adverse_price(fill_price, side, is_entry=True, bps=bps)
                if method == "next_candle_market"
                else fill_price
            )
            result = _find_exit(
                minute_bars=minute_bars,
                entry_index=fill_index,
                candidate=candidate,
                hold_minutes=hold_minutes,
                cost_bps=bps,
                sample_end=sample_end,
            )
            if result is None:
                per_cost_excluded[bps] += 1
                continue
            exit_index, exit_price, raw_exit, exit_reason = result
            trade = _trade(
                candidate=candidate,
                method=method,
                order=order,
                minute_bars=minute_bars,
                entry_index=fill_index,
                entry=actual_entry,
                raw_entry=raw_fill,
                exit_index=exit_index,
                exit_price=exit_price,
                raw_exit=raw_exit,
                exit_reason=exit_reason,
                cost_bps=bps,
                funding=funding,
            )
            per_cost_trades[bps].append(trade)
            successful_any = True
            if bps == BASE_MARKET_COST_BPS:
                busy_until = trade.exited_at
        if not successful_any:
            busy_until = max(
                busy_until,
                (order.filled_at or candidate.confirmation_at) + timedelta(minutes=hold_minutes),
            )

    costs: list[StructuralCostResult] = []
    for bps in COST_SENSITIVITY_BPS:
        trades = sorted(per_cost_trades[bps], key=lambda item: item.exited_at)
        metrics, _curve = _metrics(
            trades,
            period_start=sample_start,
            excluded=per_cost_excluded[bps],
            unfilled=diagnostics["unfilled"],
        )
        costs.append(
            StructuralCostResult(
                market_cost_bps=bps,
                metrics=metrics,
                trades=trades,
            )
        )
    return (
        StructuralSegment(
            market_type=market_type,
            side=side,
            entry_method=method,
            max_hold_minutes=hold_minutes,
            candidate_count=len(candidates),
            reward_risk_rejected=diagnostics["reward_rejected"],
            orders_placed=diagnostics["orders_placed"],
            orders_filled=diagnostics["orders_filled"],
            unfilled_limits=diagnostics["unfilled"],
            cancelled_orders=diagnostics["cancelled"],
            untestable_candidates=diagnostics["untestable"],
            overlapping_signals_skipped=diagnostics["overlapping"],
            orders=orders,
            cost_results=costs,
        ),
        evidence,
    )


def run_structural_backtest(
    *,
    run_id: str,
    created_at: datetime,
    symbol: str,
    sample_period: Literal["development", "future_validation"],
    sample_start: datetime,
    sample_end: datetime,
    m15_by_market: dict[MarketType, list[CandlePoint]],
    hourly_by_market: dict[MarketType, list[CandlePoint]],
    btc_hourly_by_market: dict[MarketType, list[CandlePoint]],
    minute_by_market: dict[MarketType, list[CandlePoint]],
    tick_sizes: dict[MarketType, Decimal],
    funding: list[tuple[datetime, Decimal]],
    data_sha256: str,
    now: datetime,
) -> StructuralBacktestResult:
    """Evaluate a frozen structural strategy without touching EMA baseline state."""
    sample_start, sample_end, created_at, now = (
        _as_utc(sample_start),
        _as_utc(sample_end),
        _as_utc(created_at),
        _as_utc(now),
    )
    if sample_period == "development" and (
        sample_start != DEVELOPMENT_START or sample_end != DEVELOPMENT_END
    ):
        raise ValueError("The structural development window is fixed and cannot be retuned.")
    if sample_period == "future_validation" and (
        sample_start != FUTURE_VALIDATION_START
        or sample_end != FUTURE_VALIDATION_END
        or now < FUTURE_VALIDATION_END
    ):
        raise ValueError("The reserved future holdout is locked until its full window closes.")

    segments: list[StructuralSegment] = []
    evidence_by_id: dict[str, StructuralCandidateEvidence] = {}
    for market_type in ("spot", "futures"):
        market_candidates = _setup_candidates(
            symbol=symbol,
            market_type=market_type,
            m15=m15_by_market[market_type],
            hourly=hourly_by_market[market_type],
            btc_hourly=btc_hourly_by_market[market_type],
        )
        by_side: dict[TradeSide, list[Candidate]] = {
            "long": [candidate for candidate in market_candidates if candidate.side == "long"],
            "short": [candidate for candidate in market_candidates if candidate.side == "short"],
        }
        supported_sides: tuple[TradeSide, ...] = (
            ("long",) if market_type == "spot" else ("long", "short")
        )
        for side in supported_sides:
            candidates = by_side[side]
            for method in ENTRY_METHODS:
                for hold in HOLDING_PERIODS:
                    segment, evidence = _simulate_segment(
                        candidates=candidates,
                        minute_bars=minute_by_market[market_type],
                        tick_size=tick_sizes[market_type],
                        market_type=market_type,
                        side=side,
                        method=method,
                        hold_minutes=hold,
                        sample_start=sample_start,
                        sample_end=sample_end,
                        funding=funding,
                        data_sha256=data_sha256,
                    )
                    segments.append(segment)
                    if hold == HOLDING_PERIODS[0]:
                        for item in evidence:
                            evidence_by_id[item.candidate_id] = item

    coverage: list[StructuralCandleCoverage] = []
    for market_type in ("spot", "futures"):
        for timeframe, data in (
            ("1m", minute_by_market[market_type]),
            ("15m", m15_by_market[market_type]),
            ("1h", hourly_by_market[market_type]),
        ):
            coverage.append(
                _coverage(
                    symbol=symbol,
                    market_type=market_type,
                    timeframe=timeframe,  # type: ignore[arg-type]
                    bars=data,
                    start=sample_start,
                    end=sample_end,
                )
            )
    future_window = research_windows(now)[1]
    notes = [
        (
            "This separate strategy does not change the EMA baseline, Scanner, portfolio, "
            "or live risk settings."
        ),
        (
            "The 0.25 ATR stop buffer, 0.10 ATR target offset, and 2:1 net reward/risk hurdle "
            "are unvalidated research hypotheses."
        ),
        (
            "The previously viewed 19 Oct–18 Nov 2026 window is excluded. Development results "
            "use the earlier fixed window."
        ),
        (
            "The next 30-day validation window is frozen and remains pending until every candle "
            "has closed; each instrument can use it once."
        ),
        (
            "One-minute OHLCV cannot establish queue position, partial fills, intraminute "
            "sequencing, or actual market impact."
        ),
        (
            "The one-tick-through rule uses today's public instrument tick size; historical "
            "tick-size changes are unavailable in this snapshot."
        ),
        (
            "Deterministic results are reported separately. Committee review is not run, and "
            "no provider calls, proposals, approvals, or orders are created."
        ),
        (
            "Each market, side, entry method, holding cap, and cost sensitivity is an "
            "independent fixed-notional simulation."
        ),
    ]
    if sample_period == "development":
        notes.append(
            f"Future validation is reserved for {future_window.starts_at.isoformat()} to "
            f"{future_window.ends_at.isoformat()} UTC and is not used for tuning."
        )
    minute_missing = any(item.timeframe == "1m" and item.missing_candles > 0 for item in coverage)
    if minute_missing:
        notes.append(
            "Some minute candles are missing. Affected candidate windows are marked untestable; "
            "they are not treated as unfilled or as no-trade periods."
        )
    return StructuralBacktestResult(
        id=run_id,
        created_at=created_at,
        symbol=symbol,  # type: ignore[arg-type]
        strategy=strategy_configuration(),
        sample_period=sample_period,
        requested_start=sample_start,
        requested_end=sample_end,
        data_sha256=data_sha256,
        candle_coverage=coverage,
        funding_coverage=_funding_coverage(funding, sample_start, sample_end),
        future_validation_window=future_window,
        segments=segments,
        candidate_evidence=list(evidence_by_id.values()),
        committee_review_status="not_run",
        committee_notice=(
            "Candidate snapshots are proposal-compatible research evidence. No AI review, "
            "proposal, approval, permit, or order is created by this backtest."
        ),
        notes=notes,
    )
