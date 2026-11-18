"""Read-only Market Scanner endpoints."""

from __future__ import annotations

import math

from fastapi import APIRouter, Depends

from stai.analytics.schemas.market_data import Candle
from stai.analytics.utils.indicators import (
    classify_macd,
    classify_rsi,
    classify_volume,
    compute_indicators,
    detect_rejection_candle,
    detect_strong_momentum,
    detect_trend,
)
from stai.core.errors import ErrorResponse
from stai.core.runtime import Runtime, get_runtime
from stai.core.time import utcnow
from stai.marketdata.schemas import MarketIndicators, MarketScannerResponse, MarketScannerRow
from stai.marketdata.service import persist_market_rows

router = APIRouter(
    prefix="/api",
    tags=["market-data"],
    responses={401: {"model": ErrorResponse, "description": "Owner session required."}},
)


def _safe(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) or not math.isfinite(number) else number


def _indicator_snapshot(candles: list[object]) -> tuple[object, object] | None:
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


def _enrich(row: MarketScannerRow) -> MarketScannerRow:
    if row.status != "fresh" or len(row.candles) < 30 or len(row.candles_15m) < 30:
        row.indicators = MarketIndicators(
            trend="unavailable",
            trend_15m="unavailable",
            rsi=None,
            rsi_state="unavailable",
            macd_direction="unavailable",
            macd_direction_15m="unavailable",
            volume_strength="unavailable",
            volatility_pct=None,
            candle_behavior="unavailable",
            screening_state="unavailable",
        )
        return row
    try:
        h1 = _indicator_snapshot(row.candles)
        m15 = _indicator_snapshot(row.candles_15m)
        if h1 is None or m15 is None:
            raise ValueError("not enough candles")
        h1_row, h1_tail = h1
        m15_row, _ = m15
        trend = detect_trend(h1_row)
        trend_15m = detect_trend(m15_row)
        rsi = _safe(h1_row.get("rsi"))
        rsi_state = classify_rsi(rsi)
        macd = classify_macd(_safe(h1_row.get("macd_hist")))
        macd_15m = classify_macd(_safe(m15_row.get("macd_hist")))
        volume = classify_volume(_safe(h1_row.get("volume_ratio")))
        candle = detect_rejection_candle(h1_row) or detect_strong_momentum(h1_row)
        volatility = None
        closes = [_safe(item.get("close")) for _, item in h1_tail.iterrows()]
        highs = [_safe(item.get("high")) for _, item in h1_tail.iterrows()]
        lows = [_safe(item.get("low")) for _, item in h1_tail.iterrows()]
        valid_closes = [value for value in closes if value is not None]
        valid_highs = [value for value in highs if value is not None]
        valid_lows = [value for value in lows if value is not None]
        if valid_closes and valid_highs and valid_lows and valid_closes[-1] != 0:
            volatility = round((max(valid_highs) - min(valid_lows)) / valid_closes[-1] * 100, 4)
        aligned = (
            trend.value in {"bullish", "bearish"}
            and trend.value == trend_15m.value
            and macd.value == macd_15m.value
            and macd.value == trend.value
        )
        row.indicators = MarketIndicators(
            trend=trend.value,
            trend_15m=trend_15m.value,
            rsi=rsi,
            rsi_state=rsi_state.value,
            macd_direction=macd.value,
            macd_direction_15m=macd_15m.value,
            volume_strength=volume.value,
            volatility_pct=volatility,
            candle_behavior="neutral" if candle is None else candle.value,
            screening_state="watch" if aligned else "no_alignment",
        )
    except (ValueError, KeyError, IndexError, TypeError):
        row.indicators = MarketIndicators(
            trend="unavailable",
            trend_15m="unavailable",
            rsi=None,
            rsi_state="unavailable",
            macd_direction="unavailable",
            macd_direction_15m="unavailable",
            volume_strength="unavailable",
            volatility_pct=None,
            candle_behavior="unavailable",
            screening_state="unavailable",
        )
    return row


@router.get(
    "/market/scanner",
    operation_id="getMarketScanner",
    summary="Latest public OKX spot and futures scanner data",
    response_model=MarketScannerResponse,
    response_description="Public observations with freshness and instrument rules.",
)
async def get_market_scanner(
    runtime: Runtime = Depends(get_runtime),
) -> MarketScannerResponse:
    rows = await runtime.okx_market_data.scanner()
    rows = [_enrich(row) for row in rows]
    with runtime.database.session() as session:
        persist_market_rows(session, rows)
    return MarketScannerResponse(
        provider="OKX",
        scanned_at=utcnow(),
        rows=rows,
    )
