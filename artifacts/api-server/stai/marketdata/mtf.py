"""Independent read-only multi-timeframe market intelligence research engine."""
# The deterministic research engine keeps several structured schema constructions compact.
# ruff: noqa: E501

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from typing import Literal

import pandas as pd

from stai.analytics.utils.indicators import add_rsi, add_sma
from stai.core.runtime import Runtime
from stai.marketdata.okx_market import SYMBOLS
from stai.marketdata.schemas import (
    CandlePoint,
    MtfDirectionalEvidence,
    MtfIndicatorSnapshot,
    MtfInstrumentAnalysis,
    MtfMarketIntelligenceResponse,
    MtfOpportunity,
    MtfQuote,
    MtfScoreComponent,
    MtfTimeframe,
    MtfZone,
)
from stai.trading.accounting import FeeSchedule

STRATEGY_VERSION = "stai-mtf-balanced-v1"
OPPORTUNITY_VERSION = "stai-mtf-research-opportunity-v1"
TIMEFRAMES: tuple[MtfTimeframe, ...] = ("1d", "4h", "1h", "15m")
WEIGHTS: dict[MtfTimeframe, int] = {"1d": 15, "4h": 25, "1h": 35, "15m": 25}
INTERVALS = {
    "1d": timedelta(days=1),
    "4h": timedelta(hours=4),
    "1h": timedelta(hours=1),
    "15m": timedelta(minutes=15),
}
STALE_AFTER = {
    "1d": timedelta(days=2),
    "4h": timedelta(hours=8),
    "1h": timedelta(hours=2),
    "15m": timedelta(minutes=30),
}


def _direction(close: float | None, sma20: float | None, sma50: float | None) -> str:
    if close is None or sma20 is None or sma50 is None:
        return "neutral"
    if sma20 > sma50 and close > sma20:
        return "bullish"
    if sma20 < sma50 and close < sma20:
        return "bearish"
    return "neutral"


def _rsi_direction(value: float | None) -> str:
    if value is None:
        return "neutral"
    return "bullish" if value > 55 else "bearish" if value < 45 else "neutral"


def _runs(candles: list[CandlePoint], interval: timedelta) -> list[list[CandlePoint]]:
    runs: list[list[CandlePoint]] = []
    for candle in sorted(
        (item for item in candles if item.complete), key=lambda item: item.opened_at
    ):
        if not runs or candle.opened_at != runs[-1][-1].opened_at + interval:
            runs.append([candle])
        else:
            runs[-1].append(candle)
    return runs


def _indicator_values(
    candles: list[CandlePoint], interval: timedelta
) -> tuple[float | None, float | None, float | None, float | None]:
    last_run = _runs(candles, interval)[-1] if candles else []
    if len(last_run) < 50:
        return None, None, None, None
    frame = pd.DataFrame({"close": [float(candle.close) for candle in last_run]})
    add_sma(frame, 20)
    add_sma(frame, 50)
    add_rsi(frame, 14)
    ranges: list[float] = []
    previous_close: float | None = None
    for candle in last_run:
        high, low, close = float(candle.high), float(candle.low), float(candle.close)
        if previous_close is not None:
            ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
        previous_close = close
    tail = frame.iloc[-1]
    atr = sum(ranges[-14:]) / 14 if len(ranges) >= 14 else None
    return (
        None if pd.isna(tail["rsi"]) else float(tail["rsi"]),
        None if pd.isna(tail["sma_20"]) else float(tail["sma_20"]),
        None if pd.isna(tail["sma_50"]) else float(tail["sma_50"]),
        atr,
    )


def _atr_by_opened(candles: list[CandlePoint], interval: timedelta) -> dict[datetime, Decimal]:
    values: dict[datetime, Decimal] = {}
    for run in _runs(candles, interval):
        true_ranges: list[Decimal] = []
        previous_close: Decimal | None = None
        for candle in run:
            if previous_close is not None:
                true_ranges.append(
                    max(
                        candle.high - candle.low,
                        abs(candle.high - previous_close),
                        abs(candle.low - previous_close),
                    )
                )
            if len(true_ranges) >= 14:
                values[candle.opened_at] = sum(true_ranges[-14:], Decimal("0")) / Decimal("14")
            previous_close = candle.close
    return values


def _snapshot(
    timeframe: MtfTimeframe, candles: list[CandlePoint], now: datetime, detail: str | None = None
) -> MtfIndicatorSnapshot:
    interval = INTERVALS[timeframe]
    completed = sorted((item for item in candles if item.complete), key=lambda item: item.opened_at)
    deltas = [
        right.opened_at - left.opened_at
        for left, right in zip(completed, completed[1:], strict=False)
    ]
    gaps = sum(1 for delta in deltas if delta != interval)
    missing = sum(
        max(0, int(delta.total_seconds() // interval.total_seconds()) - 1) for delta in deltas
    )
    latest = completed[-1] if completed else None
    rsi, sma20, sma50, atr = _indicator_values(completed, interval)
    status: Literal["fresh", "stale", "insufficient", "unavailable"] = "insufficient"
    if not completed:
        status = "unavailable" if detail else "insufficient"
    elif rsi is None or sma20 is None or sma50 is None or atr is None:
        status = "insufficient"
        detail = (
            detail or "At least 50 contiguous completed candles and ATR14 warm-up are required."
        )
    elif (
        latest.opened_at + interval
        < datetime.fromtimestamp(
            int(now.timestamp() // interval.total_seconds() * interval.total_seconds()),
            tz=UTC,
        )
        or now - (latest.opened_at + interval) > STALE_AFTER[timeframe]
    ):
        status = "stale"
        detail = (
            "The most recent expected completed candle is missing or outside the freshness window."
        )
    else:
        status = "fresh"
        if gaps:
            detail = f"{gaps} internal candle gap(s), {missing} missing bar(s); indicators use the latest contiguous run."
    close = float(latest.close) if latest else None
    return MtfIndicatorSnapshot(
        timeframe=timeframe,
        status=status,
        latest_completed_at=latest.opened_at + interval if latest else None,
        close=latest.close if latest else None,
        rsi14=rsi,
        sma20=sma20,
        sma50=sma50,
        atr14=atr,
        sma_direction=_direction(close, sma20, sma50),
        rsi_direction=_rsi_direction(rsi),
        candles=completed[-100:],
        expected_candles=len(completed) + missing,
        actual_candles=len(completed),
        gap_count=gaps,
        detail=detail,
    )


def _score(snapshots: list[MtfIndicatorSnapshot]) -> MtfDirectionalEvidence:
    indicators_ready = len(snapshots) == 4 and all(
        item.status in {"fresh", "stale"}
        and item.rsi14 is not None
        and item.sma20 is not None
        and item.sma50 is not None
        and item.atr14 is not None
        for item in snapshots
    )
    stale = any(item.status == "stale" for item in snapshots)
    components: list[MtfScoreComponent] = []
    bull = bear = neutral = Decimal("0")
    reasons: list[str] = []
    for item in snapshots:
        weight = WEIGHTS[item.timeframe]
        per_indicator = Decimal(weight) / Decimal("2")
        sma_available = item.sma20 is not None and item.sma50 is not None
        rsi_available = item.rsi14 is not None
        sma_direction = item.sma_direction if sma_available else "neutral"
        rsi_direction = item.rsi_direction if rsi_available else "neutral"
        sma_bull = per_indicator if sma_direction == "bullish" else Decimal("0")
        sma_bear = per_indicator if sma_direction == "bearish" else Decimal("0")
        rsi_bull = per_indicator if rsi_direction == "bullish" else Decimal("0")
        rsi_bear = per_indicator if rsi_direction == "bearish" else Decimal("0")
        sma_neutral = per_indicator if sma_direction == "neutral" else Decimal("0")
        rsi_neutral = per_indicator if rsi_direction == "neutral" else Decimal("0")
        components.append(
            MtfScoreComponent(
                timeframe=item.timeframe,
                weight=weight,
                sma_direction=sma_direction,
                sma_points=(sma_bull if sma_bull else sma_bear if sma_bear else sma_neutral)
                if sma_available
                else None,
                rsi_direction=rsi_direction,
                rsi_points=(rsi_bull if rsi_bull else rsi_bear if rsi_bear else rsi_neutral)
                if rsi_available
                else None,
            )
        )
        bull += sma_bull + rsi_bull
        bear += sma_bear + rsi_bear
        neutral += sma_neutral + rsi_neutral
    if not indicators_ready:
        return MtfDirectionalEvidence(
            strategy_version=STRATEGY_VERSION,
            status="insufficient",
            bullish_score=None,
            bearish_score=None,
            neutral_points=None,
            classification="insufficient",
            components=components,
            disagreement_reasons=["One or more timeframes lack fresh, complete indicator history."],
            note="Directional scores are unavailable until all four timeframes have sufficient history.",
        )
    by_tf = {item.timeframe: item.sma_direction for item in snapshots}
    if (
        by_tf["1d"] in {"bullish", "bearish"}
        and by_tf["1h"] in {"bullish", "bearish"}
        and by_tf["1d"] != by_tf["1h"]
    ):
        reasons.append(f"Daily SMA direction ({by_tf['1d']}) conflicts with 1H ({by_tf['1h']}).")
    if (
        by_tf["4h"] in {"bullish", "bearish"}
        and by_tf["1h"] in {"bullish", "bearish"}
        and by_tf["4h"] != by_tf["1h"]
    ):
        reasons.append(f"4H SMA direction ({by_tf['4h']}) conflicts with 1H ({by_tf['1h']}).")
    directional = max(bull, bear)
    if directional >= 75:
        classification = "strong_bullish" if bull > bear else "strong_bearish"
    elif directional >= 60:
        classification = "moderate_bullish" if bull > bear else "moderate_bearish"
    else:
        classification = "mixed"
    return MtfDirectionalEvidence(
        strategy_version=STRATEGY_VERSION,
        status="stale" if stale else "complete",
        bullish_score=bull,
        bearish_score=bear,
        neutral_points=neutral,
        classification=classification,
        components=components,
        disagreement_reasons=reasons,
        note=(
            "Scores use available completed candles, but at least one timeframe is stale; "
            "treat values as last-known diagnostic evidence only."
            if stale
            else "Scores are research classifications, not win probabilities. 4H/1H are "
            "prioritized for intraday discovery; 15M pullbacks may oppose higher-timeframe direction."
        ),
    )


def _zone_id(parts: str) -> str:
    return hashlib.sha256(parts.encode()).hexdigest()[:20]


def _raw_swings(
    timeframe: MtfTimeframe, candles: list[CandlePoint]
) -> list[tuple[str, Decimal, datetime, datetime, Decimal | None, bool]]:
    interval = INTERVALS[timeframe]
    atr_values = _atr_by_opened(candles, interval)
    values: list[tuple[str, Decimal, datetime, datetime, Decimal | None, bool]] = []
    for run in _runs(candles, interval):
        for index in range(2, len(run) - 2):
            neighborhood = run[index - 2 : index + 3]
            pivot = neighborhood[2]
            confirmed_at = neighborhood[-1].opened_at + interval
            atr = atr_values.get(pivot.opened_at)
            if atr is not None and atr > 0:
                atr_decimal = Decimal(str(atr))
            else:
                atr_decimal = None
            if all(pivot.low < candle.low for i, candle in enumerate(neighborhood) if i != 2):
                values.append(
                    ("support", pivot.low, pivot.opened_at, confirmed_at, atr_decimal, False)
                )
            if all(pivot.high > candle.high for i, candle in enumerate(neighborhood) if i != 2):
                values.append(
                    ("resistance", pivot.high, pivot.opened_at, confirmed_at, atr_decimal, False)
                )
    return values


def _build_zones(
    symbol: str,
    snapshots: list[MtfIndicatorSnapshot],
    series: dict[str, list[CandlePoint]],
    now: datetime,
) -> list[MtfZone]:
    raw: list[tuple[MtfTimeframe, str, Decimal, datetime, datetime, Decimal | None, bool]] = []
    for timeframe in TIMEFRAMES:
        candles = series.get(timeframe, [])
        raw.extend((timeframe, *entry) for entry in _raw_swings(timeframe, candles))

    daily = sorted(
        (item for item in series.get("1d", []) if item.complete), key=lambda item: item.opened_at
    )
    if daily:
        last = daily[-1]
        if last.opened_at + timedelta(days=1) <= now:
            prior = last
            confirmed = prior.opened_at + timedelta(days=1)
            raw.extend(
                [
                    ("1d", "support", prior.low, prior.opened_at, confirmed, None, True),
                    ("1d", "resistance", prior.high, prior.opened_at, confirmed, None, True),
                ]
            )
        current_week_start = datetime.combine(
            now.date() - timedelta(days=now.weekday()), time.min, tzinfo=UTC
        )
        prior_week = [
            item for item in daily if item.opened_at + timedelta(days=1) <= current_week_start
        ]
        if prior_week:
            start = prior_week[-1].opened_at - timedelta(days=prior_week[-1].opened_at.weekday())
            week = [
                item for item in prior_week if start <= item.opened_at < start + timedelta(days=7)
            ]
            expected_days = {start + timedelta(days=offset) for offset in range(7)}
            if week and {item.opened_at for item in week} == expected_days:
                end = start + timedelta(days=7)
                raw.extend(
                    [
                        ("1d", "support", min(item.low for item in week), start, end, None, True),
                        (
                            "1d",
                            "resistance",
                            max(item.high for item in week),
                            start,
                            end,
                            None,
                            True,
                        ),
                    ]
                )

    output: list[MtfZone] = []
    for timeframe in TIMEFRAMES:
        for kind in ("support", "resistance"):
            levels = sorted(
                (
                    entry
                    for entry in raw
                    if entry[0] == timeframe and entry[1] == kind and entry[4] <= now
                ),
                key=lambda entry: entry[2],
            )
            clusters: list[
                list[tuple[MtfTimeframe, str, Decimal, datetime, datetime, Decimal | None, bool]]
            ] = []
            for level in levels:
                tolerance = (level[5] or Decimal("0")) * Decimal("0.25")
                if not clusters:
                    clusters.append([level])
                    continue
                previous = clusters[-1]
                prior_price = previous[-1][2]
                prior_tolerance = (previous[-1][5] or Decimal("0")) * Decimal("0.25")
                if level[2] - prior_price <= max(tolerance, prior_tolerance):
                    previous.append(level)
                else:
                    clusters.append([level])
            for group in clusters:
                lower_price, upper_price = (
                    min(item[2] for item in group),
                    max(item[2] for item in group),
                )
                atrs = [item[5] for item in group if item[5] is not None]
                padding = max(atrs, default=Decimal("0")) * Decimal("0.125")
                lower, upper = max(Decimal("0"), lower_price - padding), upper_price + padding
                confirmed = max(item[4] for item in group)
                known_candles = [
                    item
                    for item in series.get(timeframe, [])
                    if item.complete
                    and item.opened_at + INTERVALS[timeframe] > confirmed
                    and item.opened_at + INTERVALS[timeframe] <= now
                ]
                touched = False
                broken = False
                retested = False
                invalidated = False
                for candle in sorted(known_candles, key=lambda item: item.opened_at):
                    close = candle.close
                    crosses = close < lower if kind == "support" else close > upper
                    touches = candle.low <= upper and candle.high >= lower
                    if crosses:
                        broken = True
                        touched = False
                    elif broken and touches:
                        retested = True
                    elif not broken and touches:
                        touched = True
                    if broken:
                        atr = max(atrs, default=Decimal("0"))
                        accepted = close < lower - atr if kind == "support" else close > upper + atr
                        invalidated = invalidated or accepted
                state = (
                    "invalidated"
                    if invalidated
                    else "retested"
                    if retested
                    else "broken"
                    if broken
                    else "tested"
                    if touched
                    else "active"
                )
                snapshot = next(item for item in snapshots if item.timeframe == timeframe)
                reference = snapshot.close
                distance = (
                    min(abs(reference - lower), abs(reference - upper))
                    if reference is not None
                    else None
                )
                pivot_at = min(item[3] for item in group)
                identity = "|".join(
                    [symbol, timeframe, kind, *(item[3].isoformat() for item in group)]
                )
                output.append(
                    MtfZone(
                        id=_zone_id(identity),
                        source_timeframe=timeframe,
                        kind=kind,
                        lower=lower,
                        upper=upper,
                        pivot_at=pivot_at,
                        confirmed_at=confirmed,
                        atr_at_calculation=max(atrs) if atrs else None,
                        independent_reactions=len(group),
                        state=state,
                        distance_from_price=distance,
                        confluence_timeframes=[],
                        is_prior_extreme=any(item[6] for item in group),
                        detail="Two-left/two-right completed swing; 0.25 ATR source-timeframe clustering. Broken resistance is not treated as confirmed support.",
                    )
                )
    for zone in output:
        confluence = sorted(
            {
                other.source_timeframe
                for other in output
                if other.id != zone.id
                and other.kind == zone.kind
                and max(zone.lower, other.lower) <= min(zone.upper, other.upper)
            },
            key=TIMEFRAMES.index,
        )
        zone.confluence_timeframes = confluence
    return output


def _nearest(
    zones: list[MtfZone], kind: Literal["support", "resistance"], price: Decimal | None
) -> MtfZone | None:
    if price is None:
        return None
    eligible = [
        zone
        for zone in zones
        if zone.kind == kind
        and zone.state not in {"broken", "invalidated"}
        and (zone.lower <= price if kind == "support" else zone.upper >= price)
    ]
    if not eligible:
        return None
    return min(eligible, key=lambda zone: min(abs(price - zone.lower), abs(price - zone.upper)))


def _opportunity(
    market_type: Literal["spot", "futures"],
    evidence: MtfDirectionalEvidence,
    snapshots: list[MtfIndicatorSnapshot],
    zones: list[MtfZone],
    *,
    market_data_fresh: bool = True,
) -> MtfOpportunity:
    if evidence.status == "insufficient":
        return MtfOpportunity(
            state="insufficient_data",
            direction=None,
            anchor_id=None,
            anchor_at=None,
            signal_at=None,
            expires_at=None,
            research_rule_version=OPPORTUNITY_VERSION,
            detail="Four-timeframe indicators are incomplete; no opportunity is evaluated.",
            plan=None,
        )
    if (
        evidence.status == "stale"
        or not market_data_fresh
        or any(item.status != "fresh" for item in snapshots)
    ):
        return MtfOpportunity(
            state="insufficient_data",
            direction=None,
            anchor_id=None,
            anchor_at=None,
            signal_at=None,
            expires_at=None,
            research_rule_version=OPPORTUNITY_VERSION,
            detail="Stale quote or timeframe data prevents current opportunity-state evaluation.",
            plan=None,
        )
    bullish, bearish = evidence.bullish_score or 0, evidence.bearish_score or 0
    direction: Literal["long", "short"] | None = None
    if bullish >= 60 and bullish > bearish:
        direction = "long"
    elif bearish >= 60 and bearish > bullish:
        direction = "short"
    if market_type == "spot" and direction == "short":
        return MtfOpportunity(
            state="bearish_watchlist",
            direction=None,
            anchor_id=None,
            anchor_at=None,
            signal_at=None,
            expires_at=None,
            research_rule_version=OPPORTUNITY_VERSION,
            detail="Bearish bias is visible, but spot remains long-only; no short opportunity is created.",
            plan=None,
        )
    if direction is None:
        return MtfOpportunity(
            state="no_opportunity",
            direction=None,
            anchor_id=None,
            anchor_at=None,
            signal_at=None,
            expires_at=None,
            research_rule_version=OPPORTUNITY_VERSION,
            detail="No dominant directional score reached the 60-point research threshold.",
            plan=None,
        )
    m15 = next(item for item in snapshots if item.timeframe == "15m")
    if m15.status != "fresh" or m15.sma20 is None or m15.atr14 is None or not m15.candles:
        return MtfOpportunity(
            state="insufficient_data",
            direction=direction,
            anchor_id=None,
            anchor_at=None,
            signal_at=None,
            expires_at=None,
            research_rule_version=OPPORTUNITY_VERSION,
            detail="Fresh 15M indicators and candles are required for entry-state evaluation.",
            plan=None,
        )
    current = Decimal(str(m15.close))
    support = _nearest(zones, "support", current)
    resistance = _nearest(zones, "resistance", current)
    target_zone = next(
        (
            zone
            for zone in sorted(zones, key=lambda item: item.lower)
            if zone.kind == ("resistance" if direction == "long" else "support")
            and zone.state not in {"broken", "invalidated"}
            and (zone.lower > current if direction == "long" else zone.upper < current)
        ),
        None,
    )
    relevant = support if direction == "long" else resistance
    if relevant is None:
        return MtfOpportunity(
            state="waiting_for_pullback",
            direction=direction,
            anchor_id=None,
            anchor_at=None,
            signal_at=None,
            expires_at=None,
            research_rule_version=OPPORTUNITY_VERSION,
            detail="Directional bias exists, but no confirmed nearby entry-side structure is available.",
            plan=None,
        )
    bars = m15.candles[-5:]
    if any(
        right.opened_at - left.opened_at != INTERVALS["15m"]
        for left, right in zip(bars, bars[1:], strict=False)
    ):
        return MtfOpportunity(
            state="insufficient_data",
            direction=direction,
            anchor_id=None,
            anchor_at=None,
            signal_at=None,
            expires_at=None,
            research_rule_version=OPPORTUNITY_VERSION,
            detail="A gap in the recent 15M confirmation window prevents opportunity evaluation.",
            plan=None,
        )
    sma20 = Decimal(str(m15.sma20))
    anchor_index: int | None = None
    for i, candle in enumerate(bars[:-1]):
        touches_zone = candle.low <= relevant.upper and candle.high >= relevant.lower
        touches_sma = candle.low <= sma20 <= candle.high
        if touches_zone or touches_sma:
            anchor_index = i
    if anchor_index is None:
        return MtfOpportunity(
            state="waiting_for_pullback",
            direction=direction,
            anchor_id=None,
            anchor_at=None,
            signal_at=None,
            expires_at=None,
            research_rule_version=OPPORTUNITY_VERSION,
            detail="Waiting for a closed 15M candle to reach confirmed structure or the 15M SMA20 area.",
            plan=None,
        )
    anchor = bars[anchor_index]
    following = bars[anchor_index + 1 :]
    confirm = None
    invalidated_at: datetime | None = None
    for candle in following[:4]:
        if (
            candle.close < relevant.lower if direction == "long" else candle.close > relevant.upper
        ) and invalidated_at is None:
            invalidated_at = candle.opened_at + INTERVALS["15m"]
        confirmed = (
            candle.close > anchor.high and candle.close > sma20
            if direction == "long"
            else candle.close < anchor.low and candle.close < sma20
        )
        if confirmed:
            confirm = candle
            break
    anchor_id = _zone_id(
        f"{OPPORTUNITY_VERSION}|{direction}|{anchor.opened_at.isoformat()}|{relevant.id}"
    )
    anchor_at = anchor.opened_at + INTERVALS["15m"]
    if invalidated_at is not None:
        signal_at = invalidated_at
        return MtfOpportunity(
            state="invalidated",
            direction=direction,
            anchor_id=anchor_id,
            anchor_at=anchor_at,
            signal_at=signal_at,
            expires_at=signal_at,
            research_rule_version=OPPORTUNITY_VERSION,
            detail="A subsequent completed 15M close crossed the structural anchor boundary.",
            plan=None,
        )
    if confirm is None:
        expired = len(following) >= 4
        expiry = anchor_at + INTERVALS["15m"] * 4
        if expired:
            return MtfOpportunity(
                state="expired",
                direction=direction,
                anchor_id=anchor_id,
                anchor_at=anchor_at,
                signal_at=expiry,
                expires_at=expiry,
                research_rule_version=OPPORTUNITY_VERSION,
                detail="The four-subsequent-15M-candle confirmation window expired without confirmation.",
                plan=None,
            )
        return MtfOpportunity(
            state="awaiting_confirmation",
            direction=direction,
            anchor_id=anchor_id,
            anchor_at=anchor_at,
            signal_at=None,
            expires_at=expiry,
            research_rule_version=OPPORTUNITY_VERSION,
            detail="A single pullback anchor is active; awaiting a confirming completed 15M close within four bars.",
            plan=None,
        )
    signal_at = confirm.opened_at + INTERVALS["15m"]
    entry = confirm.close
    stop = relevant.lower if direction == "long" else relevant.upper
    target = (
        target_zone.lower
        if direction == "long" and target_zone
        else target_zone.upper
        if target_zone
        else None
    )
    geometry_ok = target is not None and (
        stop < entry < target if direction == "long" else target < entry < stop
    )
    if not geometry_ok:
        return MtfOpportunity(
            state="entry_zone_reached",
            direction=direction,
            anchor_id=anchor_id,
            anchor_at=anchor_at,
            signal_at=signal_at,
            expires_at=signal_at + INTERVALS["15m"] * 4,
            research_rule_version=OPPORTUNITY_VERSION,
            detail="A 15M confirmation occurred, but known structural stop/target geometry is incomplete or invalid. No plan is fabricated.",
            plan=None,
        )
    if target is None:
        return MtfOpportunity(
            state="entry_zone_reached",
            direction=direction,
            anchor_id=anchor_id,
            anchor_at=anchor_at,
            signal_at=signal_at,
            expires_at=signal_at + INTERVALS["15m"] * 4,
            research_rule_version=OPPORTUNITY_VERSION,
            detail="A confirmed entry has no known opposing target zone. No plan is fabricated.",
            plan=None,
        )
    gross_reward = abs(target - entry)
    gross_risk = abs(entry - stop)
    gross_rr = gross_reward / gross_risk
    fees = FeeSchedule()
    entry_rate = fees.rate(market_type, "taker")
    target_rate = fees.rate(market_type, "maker")
    stop_rate = fees.rate(market_type, "taker")
    quantity = Decimal("1") / entry
    reward_net = quantity * (gross_reward - entry * entry_rate - target * target_rate)
    risk_net = quantity * (gross_risk + entry * entry_rate + stop * stop_rate)
    net_rr = reward_net / risk_net if reward_net > 0 and risk_net > 0 else None
    from stai.marketdata.schemas import MtfIndicativePlan

    plan = MtfIndicativePlan(
        direction=direction,
        entry_zone_lower=min(anchor.low, anchor.high),
        entry_zone_upper=max(anchor.low, anchor.high),
        trigger="Closed 15M candle closes beyond the pullback anchor extreme and on the directional side of SMA20.",
        entry_reference=entry,
        stop_reference=stop,
        target_reference=target,
        gross_reward_risk=gross_rr,
        estimated_net_reward_risk=net_rr,
        supporting_zone_ids=[relevant.id, target_zone.id],
        opposing_evidence=evidence.disagreement_reasons,
        signal_at=signal_at,
        expires_at=signal_at + INTERVALS["15m"] * 4,
        price_basis="indicative_only",
        cost_note="Net estimate uses the existing default fee schedule only; excludes spread, slippage, market impact and futures funding. Not account-specific or executable.",
    )
    return MtfOpportunity(
        state="indicative_setup_ready",
        direction=direction,
        anchor_id=anchor_id,
        anchor_at=anchor_at,
        signal_at=signal_at,
        expires_at=plan.expires_at,
        research_rule_version=OPPORTUNITY_VERSION,
        detail="Confirmed research-only setup with known structural geometry; not a proposal, committee approval, or order.",
        plan=plan,
    )


async def _instrument(
    runtime: Runtime, symbol: str, market_type: Literal["spot", "futures"], now: datetime
) -> MtfInstrumentAnalysis:
    market_symbol = f"{symbol[:-4]}/USDT"
    results = await asyncio.gather(
        *(runtime.okx_market_data.get_mtf_candles(symbol, market_type, tf) for tf in TIMEFRAMES),
        runtime.okx_market_data.get_research_ticker(symbol, market_type),
        return_exceptions=True,
    )
    candle_results, ticker_result = results[:4], results[4]
    series: dict[str, list[CandlePoint]] = {
        tf: ([] if isinstance(result, Exception) else result)
        for tf, result in zip(TIMEFRAMES, candle_results, strict=True)
    }
    snapshots = [
        _snapshot(
            tf,
            series[tf],
            now,
            "OKX history unavailable." if isinstance(result, Exception) else None,
        )
        for tf, result in zip(TIMEFRAMES, candle_results, strict=True)
    ]
    evidence = _score(snapshots)
    zones = _build_zones(symbol, snapshots, series, now)
    observed_at = runtime.now()
    ticker = ticker_result if isinstance(ticker_result, dict) else None
    age = (observed_at - ticker["exchange_at"]).total_seconds() if ticker else None
    quote_status = (
        "fresh" if age is not None and age <= 60 else "stale" if age is not None else "unavailable"
    )
    current = ticker["last"] if ticker else None
    support, resistance = (
        _nearest(zones, "support", current),
        _nearest(zones, "resistance", current),
    )
    return MtfInstrumentAnalysis(
        symbol=market_symbol,
        market_type=market_type,
        instrument_id=f"{symbol[:-4]}-USDT" + ("-SWAP" if market_type == "futures" else ""),
        quote=MtfQuote(
            last_price=ticker["last"] if ticker else None,
            change_pct_24h=ticker["change_pct_24h"] if ticker else None,
            volume_24h=ticker["volume_24h"] if ticker else None,
            exchange_at=ticker["exchange_at"] if ticker else None,
            observed_at=observed_at,
            status=quote_status,
        ),
        timeframes=snapshots,
        evidence=evidence,
        btc_context=None,
        zones=zones,
        nearest_support=support,
        nearest_resistance=resistance,
        opportunity=_opportunity(
            market_type, evidence, snapshots, zones, market_data_fresh=quote_status == "fresh"
        ),
        committee_status="Existing committee history is shown separately; no review was triggered.",
        observed_at=observed_at,
    )


async def market_intelligence(runtime: Runtime) -> MtfMarketIntelligenceResponse:
    now = runtime.now().astimezone(UTC)
    instruments = await asyncio.gather(
        *(
            _instrument(runtime, symbol, market_type, now)
            for symbol in SYMBOLS
            for market_type in ("spot", "futures")
        ),
        return_exceptions=True,
    )
    output: list[MtfInstrumentAnalysis] = []
    for symbol, market_type, result in zip(
        (symbol for symbol in SYMBOLS for _ in ("spot", "futures")),
        (market for _ in SYMBOLS for market in ("spot", "futures")),
        instruments,
        strict=True,
    ):
        market_symbol = f"{symbol[:-4]}/USDT"
        if isinstance(result, Exception):
            stamp = runtime.now()
            output.append(
                MtfInstrumentAnalysis(
                    symbol=market_symbol,
                    market_type=market_type,
                    instrument_id=f"{symbol[:-4]}-USDT"
                    + ("-SWAP" if market_type == "futures" else ""),
                    quote=MtfQuote(
                        last_price=None,
                        change_pct_24h=None,
                        volume_24h=None,
                        exchange_at=None,
                        observed_at=stamp,
                        status="unavailable",
                    ),
                    timeframes=[
                        _snapshot(tf, [], stamp, "Market data unavailable.") for tf in TIMEFRAMES
                    ],
                    evidence=_score([_snapshot(tf, [], stamp) for tf in TIMEFRAMES]),
                    btc_context=None,
                    zones=[],
                    nearest_support=None,
                    nearest_resistance=None,
                    opportunity=MtfOpportunity(
                        state="insufficient_data",
                        direction=None,
                        anchor_id=None,
                        anchor_at=None,
                        signal_at=None,
                        expires_at=None,
                        research_rule_version=OPPORTUNITY_VERSION,
                        detail="Market data is unavailable; no research opportunity is evaluated.",
                        plan=None,
                    ),
                    committee_status="No committee invocation; existing history only.",
                    observed_at=stamp,
                )
            )
        else:
            output.append(result)
    for item in output:
        if item.symbol != "BTC/USDT":
            btc = next(
                (
                    row
                    for row in output
                    if row.symbol == "BTC/USDT" and row.market_type == item.market_type
                ),
                None,
            )
            item.btc_context = btc.evidence if btc else None
    return MtfMarketIntelligenceResponse(
        provider="OKX",
        strategy_version=STRATEGY_VERSION,
        observed_at=now,
        instruments=output,
        limitations=[
            "All indicators and structures use completed candles; OKX 1Dutc candles are required to preserve UTC daily alignment.",
            "SMA50/ATR14 and swing detection require contiguous history; gaps are reported and break swing/indicator runs.",
            "0.25 ATR zone clustering and the opportunity anchor/confirmation rule are unvalidated research hypotheses separate from the frozen 0.5 ATR challenger.",
            "Indicative net reward/risk uses default fees only and excludes spread, slippage, impact, funding and account-specific fees.",
            "This endpoint is read-only and does not create proposals, invoke AI, or submit orders.",
        ],
    )
