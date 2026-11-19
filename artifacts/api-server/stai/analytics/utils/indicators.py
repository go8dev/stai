"""
Technical indicator utilities.

All functions are pure and stateless — they accept a DataFrame (or list of
Candles) and return a new / modified DataFrame.  Classification helpers return
enum values from stai.analytics.core.constants so callers never deal with raw strings.

Public API
----------
klines_to_df(klines)          → pd.DataFrame (OHLCV, sorted by open_time)
add_ema(df, period)           → df with  ema_{period} column
add_rsi(df, period=14)        → df with  rsi column
add_macd(df)                  → df with  macd / macd_signal / macd_hist columns
add_volume_metrics(df)        → df with  avg_volume / volume_ratio columns
add_candle_metrics(df)        → df with  body / upper_wick / lower_wick / body_pct
compute_indicators(klines)    → df with ALL of the above
detect_trend(row)             → EMAAlignment
detect_rejection_candle(row)  → CandleBehavior | None
detect_strong_momentum(row)   → CandleBehavior | None
classify_rsi(rsi)             → RSIState
classify_macd(hist)           → MACDDirection
classify_volume(ratio)        → VolumeStrength

Legacy scalar helpers (kept for backward compatibility)
-------------------------------------------------------
compute_rsi(closes, period)   → float | None   (list-based, single value)
compute_ema(closes, period)   → float | None   (list-based, single value)
compute_atr(highs, lows, closes, period) → float | None
compute_risk_reward(entry, sl, tp)       → float
"""
from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd

from stai.analytics.core.constants import (
    BODY_TO_RANGE_STRONG,
    MACD_FAST,
    MACD_SIGNAL,
    MACD_SLOW,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    VOLUME_AVG_WINDOW,
    VOLUME_HIGH_RATIO,
    VOLUME_LOW_RATIO,
    WICK_TO_BODY_REJECTION,
    CandleBehavior,
    EMAAlignment,
    MACDDirection,
    RSIState,
    VolumeStrength,
)
from stai.analytics.schemas.market_data import Candle


# ── DataFrame construction ────────────────────────────────────────────────────

def klines_to_df(klines: List[Candle]) -> pd.DataFrame:
    """
    Convert a list of Candle Pydantic models to a sorted OHLCV DataFrame.

    Columns: open_time (UTC datetime), open, high, low, close, volume, close_time
    Rows are sorted ascending by open_time.
    """
    records = [
        {
            "open_time":  k.open_time,
            "open":       k.open,
            "high":       k.high,
            "low":        k.low,
            "close":      k.close,
            "volume":     k.volume,
            "close_time": k.close_time,
        }
        for k in klines
    ]
    df = pd.DataFrame(records)
    df["open_time"]  = pd.to_datetime(df["open_time"],  unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


# ── Individual indicator adders ───────────────────────────────────────────────

def add_ema(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """
    Attach ``ema_{period}`` column.

    Uses pandas ewm with adjust=False and min_periods=period so that rows
    without enough history produce NaN rather than a partial approximation.
    Covers EMA 7, EMA 25, and EMA 99 out of the box.
    """
    col = f"ema_{period}"
    df[col] = (
        df["close"]
        .ewm(span=period, adjust=False, min_periods=period)
        .mean()
        .round(6)
    )
    return df


def add_sma(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """Attach a simple moving average without changing any legacy EMA values."""
    if period < 1:
        raise ValueError("SMA period must be positive.")
    df[f"sma_{period}"] = df["close"].rolling(window=period, min_periods=period).mean()
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Attach ``rsi`` column using Wilder's smoothed RSI.

    Uses ewm(com=period-1) which is equivalent to Wilder's alpha = 1/period.
    Values outside [0, 100] are theoretically impossible here.
    """
    delta    = df["close"].diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)

    avg_gain = gain.ewm(com=period - 1, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False, min_periods=period).mean()

    # Guard: when all moves are gains avg_loss=0 → RSI=100; all losses → RSI=0
    rs        = avg_gain / avg_loss.replace(0, np.nan)
    rsi_raw   = (100 - (100 / (1 + rs))).round(2)
    rsi_raw   = rsi_raw.where(avg_loss != 0, 100.0)   # all-gain rows → 100
    rsi_raw   = rsi_raw.where(avg_gain != 0, 0.0)     # all-loss rows → 0
    df["rsi"] = rsi_raw
    return df


def add_macd(
    df: pd.DataFrame,
    fast: int = MACD_FAST,
    slow: int = MACD_SLOW,
    signal: int = MACD_SIGNAL,
) -> pd.DataFrame:
    """
    Attach ``macd``, ``macd_signal``, and ``macd_hist`` columns.

    Default configuration: 12 / 26 / 9 (standard MACD).
    Histogram = MACD line − signal line.
    Rows with fewer than ``slow`` candles will have NaN.
    """
    ema_fast          = df["close"].ewm(span=fast,   adjust=False, min_periods=fast).mean()
    ema_slow          = df["close"].ewm(span=slow,   adjust=False, min_periods=slow).mean()
    df["macd"]        = (ema_fast - ema_slow).round(6)
    df["macd_signal"] = (
        df["macd"].ewm(span=signal, adjust=False, min_periods=signal).mean().round(6)
    )
    df["macd_hist"]   = (df["macd"] - df["macd_signal"]).round(6)
    return df


def add_volume_metrics(df: pd.DataFrame, avg_window: int = VOLUME_AVG_WINDOW) -> pd.DataFrame:
    """
    Attach ``avg_volume`` (rolling mean) and ``volume_ratio`` (current ÷ avg).

    ratio > 1.0  → above-average volume
    ratio < 1.0  → below-average volume
    """
    df["avg_volume"]   = (
        df["volume"].rolling(window=avg_window, min_periods=1).mean().round(4)
    )
    df["volume_ratio"] = (
        df["volume"] / df["avg_volume"].replace(0, np.nan)
    ).round(4)
    return df


def add_candle_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attach candlestick shape columns.

    - ``body``       absolute |close − open|
    - ``range``      high − low (total candle height)
    - ``upper_wick`` high − max(close, open)
    - ``lower_wick`` min(close, open) − low
    - ``body_pct``   body as a percentage of the total range (0–100)
    """
    df["body"]       = (df["close"] - df["open"]).abs().round(6)
    df["range"]      = (df["high"] - df["low"]).round(6)
    df["upper_wick"] = (df["high"] - df[["close", "open"]].max(axis=1)).round(6)
    df["lower_wick"] = (df[["close", "open"]].min(axis=1) - df["low"]).round(6)
    df["body_pct"]   = (
        df["body"] / df["range"].replace(0, np.nan) * 100
    ).round(2)
    return df


# ── Master compute function ───────────────────────────────────────────────────

def compute_indicators(klines: List[Candle]) -> pd.DataFrame:
    """
    Convert a list of Candles to a fully annotated indicator DataFrame.

    Equivalent to calling klines_to_df → add_ema(7) → add_ema(25) →
    add_ema(99) → add_rsi → add_macd → add_volume_metrics → add_candle_metrics.
    """
    df = klines_to_df(klines)
    df = add_ema(df, 7)
    df = add_ema(df, 25)
    df = add_ema(df, 99)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_volume_metrics(df)
    df = add_candle_metrics(df)
    return df


# ── Pattern detection helpers ─────────────────────────────────────────────────

def detect_trend(row: pd.Series) -> EMAAlignment:
    """
    Classify the EMA stack alignment for a single candle row.

    Bullish : EMA7 > EMA25 > EMA99 and close is above EMA7 (fully stacked up)
    Bearish : EMA7 < EMA25 < EMA99 and close is below EMA7 (fully stacked down)
    Neutral : any mixed alignment or NaN values in EMA columns
    """
    ema7  = row.get("ema_7")
    ema25 = row.get("ema_25")
    ema99 = row.get("ema_99")
    close = float(row["close"])

    def _is_nan(v: object) -> bool:
        return v is None or (isinstance(v, float) and np.isnan(v))

    if any(_is_nan(v) for v in [ema7, ema25, ema99]):
        return EMAAlignment.NEUTRAL

    if float(ema7) > float(ema25) > float(ema99) and close > float(ema7):
        return EMAAlignment.BULLISH
    if float(ema7) < float(ema25) < float(ema99) and close < float(ema7):
        return EMAAlignment.BEARISH
    return EMAAlignment.NEUTRAL


def detect_rejection_candle(row: pd.Series) -> Optional[CandleBehavior]:
    """
    Detect long-wick rejection candles on a single row.

    A wick is considered a rejection when it is at least ``WICK_TO_BODY_REJECTION``
    (default 2×) larger than the candle body.

    Returns
    -------
    CandleBehavior.REJECTION_BEAR  — long upper wick (sellers rejected higher prices)
    CandleBehavior.REJECTION_BULL  — long lower wick (buyers defended lower prices)
    None                           — no clear rejection pattern
    """
    body  = float(row.get("body",       0) or 0)
    upper = float(row.get("upper_wick", 0) or 0)
    lower = float(row.get("lower_wick", 0) or 0)

    if body == 0:
        return None  # doji — skip to avoid division issues

    if upper >= WICK_TO_BODY_REJECTION * body:
        return CandleBehavior.REJECTION_BEAR
    if lower >= WICK_TO_BODY_REJECTION * body:
        return CandleBehavior.REJECTION_BULL
    return None


def detect_strong_momentum(row: pd.Series) -> Optional[CandleBehavior]:
    """
    Detect strong directional momentum candles on a single row.

    Criteria: body ≥ ``BODY_TO_RANGE_STRONG`` (60 %) of total range
              AND volume ratio ≥ ``VOLUME_HIGH_RATIO`` (1.5×).

    Returns
    -------
    CandleBehavior.STRONG_BULL — large bullish candle with high volume
    CandleBehavior.STRONG_BEAR — large bearish candle with high volume
    None                       — criteria not met
    """
    body_pct     = float(row.get("body_pct",     0) or 0)
    volume_ratio = float(row.get("volume_ratio", 1) or 1)

    if body_pct < BODY_TO_RANGE_STRONG * 100:
        return None
    if volume_ratio < VOLUME_HIGH_RATIO:
        return None

    is_bullish = float(row["close"]) > float(row["open"])
    return CandleBehavior.STRONG_BULL if is_bullish else CandleBehavior.STRONG_BEAR


# ── Classification helpers ────────────────────────────────────────────────────

def classify_rsi(rsi: Optional[float]) -> RSIState:
    """Map a raw RSI value to an RSIState enum."""
    if rsi is None or (isinstance(rsi, float) and np.isnan(rsi)):
        return RSIState.NEUTRAL
    if rsi >= RSI_OVERBOUGHT:
        return RSIState.OVERBOUGHT
    if rsi <= RSI_OVERSOLD:
        return RSIState.OVERSOLD
    return RSIState.NEUTRAL


def classify_macd(hist: Optional[float]) -> MACDDirection:
    """Map a MACD histogram value to a MACDDirection enum."""
    if hist is None or (isinstance(hist, float) and np.isnan(hist)):
        return MACDDirection.NEUTRAL
    if hist > 0:
        return MACDDirection.BULLISH
    if hist < 0:
        return MACDDirection.BEARISH
    return MACDDirection.NEUTRAL


def classify_volume(ratio: Optional[float]) -> VolumeStrength:
    """Map a volume ratio (current ÷ rolling average) to a VolumeStrength enum."""
    if ratio is None or (isinstance(ratio, float) and np.isnan(ratio)):
        return VolumeStrength.NORMAL
    if ratio >= VOLUME_HIGH_RATIO:
        return VolumeStrength.HIGH
    if ratio <= VOLUME_LOW_RATIO:
        return VolumeStrength.LOW
    return VolumeStrength.NORMAL


# ── Legacy scalar helpers (backward compatibility) ────────────────────────────

def compute_rsi(closes: List[float], period: int = 14) -> Optional[float]:
    """Single-value RSI from a plain list of closes. Kept for backward compat."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, period + 1):
        delta = closes[-period - 1 + i] - closes[-period - 2 + i]
        (gains if delta > 0 else losses).append(abs(delta))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def compute_ema(closes: List[float], period: int) -> Optional[float]:
    """Single-value EMA from a plain list of closes. Kept for backward compat."""
    if len(closes) < period:
        return None
    k = 2 / (period + 1)
    ema = sum(closes[:period]) / period
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
    return round(ema, 6)


def compute_atr(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14,
) -> Optional[float]:
    """Single-value ATR from plain lists. Kept for backward compat."""
    if len(closes) < period + 1:
        return None
    true_ranges = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        true_ranges.append(tr)
    return round(sum(true_ranges[-period:]) / period, 6)


def compute_risk_reward(entry: float, stop_loss: float, take_profit: float) -> float:
    """Compute risk-to-reward ratio. Kept for backward compat."""
    risk   = abs(entry - stop_loss)
    reward = abs(take_profit - entry)
    if risk == 0:
        return 0.0
    return round(reward / risk, 2)
