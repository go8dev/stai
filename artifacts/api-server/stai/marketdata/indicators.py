"""Shared indicator input preparation for the scanner and committee."""

from __future__ import annotations

import math

from stai.analytics.schemas.market_data import Candle
from stai.analytics.utils.indicators import compute_indicators


def safe_number(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) or not math.isfinite(number) else number


def indicator_snapshot(candles: list[object]) -> tuple[object, object] | None:
    """Compute indicators using completed candles only."""
    candles = [candle for candle in candles if candle.complete]
    if len(candles) < 30:
        return None
    converted = [
        Candle(
            open_time=int(candle.opened_at.timestamp() * 1000),
            open=float(candle.open),
            high=float(candle.high),
            low=float(candle.low),
            close=float(candle.close),
            volume=float(candle.volume),
            close_time=int(candle.opened_at.timestamp() * 1000) + 1,
            quote_volume=float(candle.quote_volume),
            trades=0,
        )
        for candle in candles
    ]
    frame = compute_indicators(converted)
    return frame.iloc[-1], frame.iloc[-24:]
