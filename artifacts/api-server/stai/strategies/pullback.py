"""Shared causal EMA25 pullback state machine for scanner and historical research."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from stai.analytics.schemas.market_data import Candle
from stai.analytics.utils.indicators import compute_indicators
from stai.marketdata.schemas import CandlePoint
from stai.strategies.schemas import PullbackEvidence

STRATEGY_VERSION = "ema25-pullback-v2"
BAR = timedelta(minutes=15)
HOUR = timedelta(hours=1)


@dataclass(frozen=True)
class EntryBar:
    candle: CandlePoint
    ema25: float | None
    ema99: float | None


def utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Research candles must have timezone-aware timestamps.")
    return value.astimezone(UTC)


def indicator_series(bars: list[CandlePoint], interval: timedelta) -> dict[datetime, EntryBar]:
    """Reset EMA warm-up at every missing/unfinished/duplicate candle."""
    result: dict[datetime, EntryBar] = {}
    segment: list[CandlePoint] = []

    def flush() -> None:
        if not segment:
            return
        frame = compute_indicators(
            [
                Candle(
                    open_time=int(utc(b.opened_at).timestamp() * 1000),
                    close_time=int((utc(b.opened_at) + interval).timestamp() * 1000) - 1,
                    open=float(b.open),
                    high=float(b.high),
                    low=float(b.low),
                    close=float(b.close),
                    volume=float(b.volume),
                    quote_volume=float(b.quote_volume),
                    trades=0,
                )
                for b in segment
            ]
        )
        for index, candle in enumerate(segment):
            row = frame.iloc[index]
            values = [float(row[key]) for key in ("ema_25", "ema_99")]
            result[utc(candle.opened_at)] = EntryBar(
                candle, *(v if math.isfinite(v) else None for v in values)
            )

    for candle in sorted(bars, key=lambda b: utc(b.opened_at)):
        if not candle.complete:
            flush()
            segment = []
            continue
        if segment and utc(candle.opened_at) != utc(segment[-1].opened_at) + interval:
            flush()
            segment = []
        segment.append(candle)
    flush()
    return result


def hourly_bars(bars: list[CandlePoint]) -> list[CandlePoint]:
    groups: dict[datetime, list[CandlePoint]] = {}
    for bar in bars:
        at = utc(bar.opened_at)
        groups.setdefault(at.replace(minute=0, second=0, microsecond=0), []).append(bar)
    result = []
    for at, group in sorted(groups.items()):
        group = sorted(group, key=lambda b: utc(b.opened_at))
        if (
            len(group) != 4
            or not all(b.complete for b in group)
            or [utc(b.opened_at) for b in group] != [at + i * BAR for i in range(4)]
        ):
            continue
        result.append(
            CandlePoint(
                opened_at=at,
                open=group[0].open,
                high=max(b.high for b in group),
                low=min(b.low for b in group),
                close=group[-1].close,
                volume=sum(b.volume for b in group),
                quote_volume=sum(b.quote_volume for b in group),
                complete=True,
            )
        )
    return result


def closed_hour(signal_close: datetime) -> datetime:
    return utc(signal_close).replace(minute=0, second=0, microsecond=0) - HOUR


def directional(bar: EntryBar | None, side: str, *, hourly: bool) -> bool:
    if bar is None or bar.ema25 is None or bar.ema99 is None:
        return False
    close = float(bar.candle.close)
    if side == "long":
        return bar.ema25 > bar.ema99 and (not hourly or close > bar.ema99)
    return bar.ema25 < bar.ema99 and (not hourly or close < bar.ema99)


def advance(
    state: PullbackEvidence,
    *,
    symbol: str,
    market_type: str,
    bar: EntryBar,
    h1: EntryBar | None,
    btc_h1: EntryBar | None,
    as_of: datetime,
) -> PullbackEvidence:
    """One transition per closed bar. Replaying the cursor cannot re-emit a setup."""
    at = utc(bar.candle.opened_at)
    now = utc(as_of)
    if not bar.candle.complete or at + BAR > now:
        return state.model_copy(
            update={"stage": "insufficient_data", "reason": "Unfinished/future signal candle."}
        )
    if state.last_candle_at is not None and at <= utc(state.last_candle_at):
        return state
    previous = state.last_candle_at
    active = state.stage == "pullback_detected"
    result = state.model_copy(deep=True)
    result.last_candle_at = at
    result.checks = {}
    if previous is not None and at != utc(previous) + BAR:
        result.stage = "insufficient_data"
        result.reason = "Nonconsecutive 15m history invalidated the setup."
        return result
    expected_hour = closed_hour(at + BAR)
    is_btc = symbol.replace("/", "").replace(":USDT", "") == "BTCUSDT"
    history_ok = all(
        value is not None and value.ema25 is not None and value.ema99 is not None
        for value in ([bar, h1] if is_btc else [bar, h1, btc_h1])
    )
    history_ok = (
        history_ok
        and h1 is not None
        and h1.candle.complete
        and utc(h1.candle.opened_at) == expected_hour
    )
    if not is_btc:
        history_ok = (
            history_ok
            and btc_h1 is not None
            and btc_h1.candle.complete
            and utc(btc_h1.candle.opened_at) == expected_hour
        )
    if not history_ok:
        result.stage = "insufficient_data"
        result.reason = "99 contiguous closed candles and aligned 1h/BTC context required."
        return result
    side = state.side
    close = float(bar.candle.close)
    result.checks = {
        "supportedSide": market_type == "futures" or side == "long",
        "hourlyDirection": directional(h1, side, hourly=True),
        "btcDirection": is_btc or directional(btc_h1, side, hourly=True),
        "m15Structure": directional(bar, side, hourly=False),
        "ema99Boundary": close > bar.ema99 if side == "long" else close < bar.ema99,
    }
    if not all(result.checks.values()):
        result.stage = "invalidated" if active else "waiting"
        result.reason = "Failed: " + ", ".join(
            k for k, passed in result.checks.items() if not passed
        )
        return result
    if active:
        result.bars_waited += 1
        confirms = (
            close > state.pullback_high and close > bar.ema25
            if side == "long"
            else close < state.pullback_low and close < bar.ema25
        )
        result.checks["laterCandleConfirmation"] = confirms
        if result.bars_waited <= 4 and confirms:
            result.stage = "confirmed"
            result.confirmation_at = at + BAR
            result.reason = "Closed candle confirmed beyond the original pullback and EMA25."
        elif result.bars_waited >= 4:
            result.stage = "expired"
            result.reason = "No confirmation in the next four completed 15m candles."
        else:
            result.reason = "Waiting for a close beyond the original pullback and EMA25."
        return result
    # A consumed/cancelled setup is never re-armed on its original touch candle.
    result = PullbackEvidence(side=side, last_candle_at=at, checks=result.checks, stage="waiting")
    touches = float(bar.candle.low) <= bar.ema25 <= float(bar.candle.high)
    result.checks["ema25Touch"] = touches
    if touches:
        identity = f"{STRATEGY_VERSION}|{symbol}|{market_type}|{side}|{at.isoformat()}"
        result.stage = "pullback_detected"
        result.reason = "EMA25 touch recorded; same-candle confirmation is not allowed."
        result.pullback_at = at + BAR
        result.pullback_high = float(bar.candle.high)
        result.pullback_low = float(bar.candle.low)
        result.setup_id = hashlib.sha256(identity.encode()).hexdigest()
    return result


def replay(
    *,
    symbol: str,
    market_type: str,
    m15: dict[datetime, EntryBar],
    h1: dict[datetime, EntryBar],
    btc_h1: dict[datetime, EntryBar],
    as_of: datetime,
    previous: dict[str, PullbackEvidence] | None = None,
) -> tuple[dict[str, PullbackEvidence], dict[str, dict[datetime, PullbackEvidence]]]:
    """Identical sequential evaluation for live resume and historical replay."""
    states: dict[str, PullbackEvidence] = {}
    events: dict[str, dict[datetime, PullbackEvidence]] = {}
    for side in ("long",) if market_type == "spot" else ("long", "short"):
        state = (previous or {}).get(side, PullbackEvidence(side=side))
        confirmed = {}
        for at, bar in sorted(m15.items()):
            if at + BAR > utc(as_of):
                break
            if state.last_candle_at is not None and at <= utc(state.last_candle_at):
                continue
            hour = closed_hour(at + BAR)
            state = advance(
                state,
                symbol=symbol,
                market_type=market_type,
                bar=bar,
                h1=h1.get(hour),
                btc_h1=btc_h1.get(hour),
                as_of=as_of,
            )
            if state.stage == "confirmed":
                confirmed[at] = state
        states[side] = state
        events[side] = confirmed
    return states, events
