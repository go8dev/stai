"""
Tests for the technical indicator engine (app/utils/indicators.py).

Covers:
  - DataFrame construction (klines_to_df)
  - Individual indicator adders (EMA, RSI, MACD, volume, candle metrics)
  - compute_indicators end-to-end
  - Pattern detection (detect_trend, detect_rejection_candle, detect_strong_momentum)
  - Classification helpers (classify_rsi, classify_macd, classify_volume)
  - Legacy scalar helpers (compute_rsi, compute_ema, compute_atr, compute_risk_reward)
"""
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
import pytest

from stai.analytics.core.constants import (
    CandleBehavior,
    EMAAlignment,
    MACDDirection,
    RSIState,
    VolumeStrength,
)
from stai.analytics.schemas.market_data import Candle
from stai.analytics.utils.indicators import (
    add_candle_metrics,
    add_ema,
    add_macd,
    add_rsi,
    add_volume_metrics,
    classify_macd,
    classify_rsi,
    classify_volume,
    compute_atr,
    compute_ema,
    compute_indicators,
    compute_risk_reward,
    compute_rsi,
    detect_rejection_candle,
    detect_strong_momentum,
    detect_trend,
    klines_to_df,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_kline(
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float = 1000.0,
    open_time: int = 0,
    close_time: int = 59999,
) -> Candle:
    return Candle(
        open_time=open_time,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        close_time=close_time,
        quote_volume=close * volume,
        trades=100,
    )


def _rising_klines(n: int = 200, base: float = 100.0, step: float = 0.5) -> List[Candle]:
    """Steadily rising candles — useful for bullish EMA tests."""
    klines = []
    for i in range(n):
        open_ = base + i * step
        close = open_ + step * 0.8
        klines.append(
            _make_kline(
                open_=open_,
                high=close + step * 0.2,
                low=open_ - step * 0.1,
                close=close,
                volume=1500.0,
                open_time=i * 60_000,
                close_time=i * 60_000 + 59_999,
            )
        )
    return klines


def _flat_klines(n: int = 200, price: float = 100.0) -> List[Candle]:
    """Flat sideways candles — all values identical."""
    klines = []
    for i in range(n):
        klines.append(
            _make_kline(
                open_=price,
                high=price + 0.1,
                low=price - 0.1,
                close=price,
                volume=1000.0,
                open_time=i * 60_000,
                close_time=i * 60_000 + 59_999,
            )
        )
    return klines


# ── klines_to_df ─────────────────────────────────────────────────────────────

def test_klines_to_df_shape() -> None:
    klines = _flat_klines(10)
    df = klines_to_df(klines)
    assert len(df) == 10
    assert list(df.columns[:6]) == ["open_time", "open", "high", "low", "close", "volume"]


def test_klines_to_df_sorted_by_time() -> None:
    # Provide klines in reverse order; output must be sorted ascending
    klines = list(reversed(_flat_klines(5)))
    df = klines_to_df(klines)
    assert df["open_time"].is_monotonic_increasing


def test_klines_to_df_datetime_utc() -> None:
    """Timestamps must be timezone-aware UTC (ns or us resolution are both fine)."""
    df = klines_to_df(_flat_klines(1))
    dtype = df["open_time"].dtype
    assert hasattr(dtype, "tz") and str(dtype.tz) == "UTC"


# ── add_ema ───────────────────────────────────────────────────────────────────

def test_add_ema_column_created() -> None:
    df = klines_to_df(_flat_klines(50))
    df = add_ema(df, 7)
    assert "ema_7" in df.columns


def test_add_ema_nan_for_insufficient_rows() -> None:
    """Rows before period candles must be NaN."""
    df = klines_to_df(_flat_klines(50))
    df = add_ema(df, 20)
    # First 19 rows should be NaN (min_periods=20)
    assert df["ema_20"].iloc[:19].isna().all()


def test_add_ema_convergence_flat_series() -> None:
    """EMA of a flat series should converge to that price."""
    df = klines_to_df(_flat_klines(100, price=50.0))
    df = add_ema(df, 7)
    assert abs(df["ema_7"].dropna().iloc[-1] - 50.0) < 0.01


def test_add_ema_multiple_periods() -> None:
    df = klines_to_df(_flat_klines(200))
    for period in (7, 25, 99):
        df = add_ema(df, period)
    assert all(f"ema_{p}" in df.columns for p in [7, 25, 99])


# ── add_rsi ───────────────────────────────────────────────────────────────────

def test_add_rsi_column_created() -> None:
    df = klines_to_df(_flat_klines(50))
    df = add_rsi(df)
    assert "rsi" in df.columns


def test_add_rsi_range() -> None:
    """RSI must be in [0, 100] for all non-NaN rows."""
    df = klines_to_df(_rising_klines(100))
    df = add_rsi(df)
    valid = df["rsi"].dropna()
    assert (valid >= 0).all() and (valid <= 100).all()


def test_add_rsi_overbought_on_rising() -> None:
    """A steadily rising series should push RSI above 70."""
    df = klines_to_df(_rising_klines(100))
    df = add_rsi(df)
    assert df["rsi"].dropna().iloc[-1] > 70


# ── add_macd ──────────────────────────────────────────────────────────────────

def test_add_macd_columns_created() -> None:
    df = klines_to_df(_flat_klines(100))
    df = add_macd(df)
    assert {"macd", "macd_signal", "macd_hist"}.issubset(df.columns)


def test_add_macd_histogram_equals_diff() -> None:
    """Histogram must be very close to MACD − signal line (allow float rounding)."""
    df = klines_to_df(_rising_klines(100))
    df = add_macd(df)
    diff = (df["macd"] - df["macd_signal"]).dropna()
    hist = df["macd_hist"].dropna()
    # Align by index before comparing
    common = diff.index.intersection(hist.index)
    np.testing.assert_allclose(
        diff.loc[common].values,
        hist.loc[common].values,
        rtol=1e-3,
        atol=1e-4,
        err_msg="MACD histogram deviates too far from (macd - signal)",
    )


def test_add_macd_positive_on_rising() -> None:
    """MACD line should be positive for a steadily rising series."""
    df = klines_to_df(_rising_klines(100))
    df = add_macd(df)
    assert df["macd"].dropna().iloc[-1] > 0


# ── add_volume_metrics ────────────────────────────────────────────────────────

def test_add_volume_metrics_columns() -> None:
    df = klines_to_df(_flat_klines(50))
    df = add_volume_metrics(df)
    assert "avg_volume" in df.columns
    assert "volume_ratio" in df.columns


def test_add_volume_metrics_ratio_near_one_uniform_volume() -> None:
    """When every candle has the same volume, ratio must be ≈ 1."""
    df = klines_to_df(_flat_klines(30))
    df = add_volume_metrics(df)
    assert abs(df["volume_ratio"].dropna().iloc[-1] - 1.0) < 0.01


# ── add_candle_metrics ────────────────────────────────────────────────────────

def test_add_candle_metrics_columns() -> None:
    df = klines_to_df(_flat_klines(5))
    df = add_candle_metrics(df)
    for col in ("body", "range", "upper_wick", "lower_wick", "body_pct"):
        assert col in df.columns


def test_add_candle_metrics_values() -> None:
    """Manual check on a known candle shape."""
    k = _make_kline(open_=100, high=110, low=90, close=105)
    df = klines_to_df([k])
    df = add_candle_metrics(df)
    row = df.iloc[0]
    assert row["body"]       == pytest.approx(5.0,  abs=1e-4)   # |105 − 100|
    assert row["range"]      == pytest.approx(20.0, abs=1e-4)   # 110 − 90
    assert row["upper_wick"] == pytest.approx(5.0,  abs=1e-4)   # 110 − 105
    assert row["lower_wick"] == pytest.approx(10.0, abs=1e-4)   # 100 − 90
    assert row["body_pct"]   == pytest.approx(25.0, abs=0.1)    # 5/20 × 100


# ── compute_indicators ────────────────────────────────────────────────────────

def test_compute_indicators_all_columns_present() -> None:
    df = compute_indicators(_flat_klines(200))
    expected = {
        "ema_7", "ema_25", "ema_99",
        "rsi",
        "macd", "macd_signal", "macd_hist",
        "avg_volume", "volume_ratio",
        "body", "range", "upper_wick", "lower_wick", "body_pct",
    }
    assert expected.issubset(set(df.columns))


def test_compute_indicators_last_row_no_nan_on_large_series() -> None:
    """With 200 candles the last row should have all indicator values."""
    df = compute_indicators(_rising_klines(200))
    row = df.iloc[-1]
    for col in ("ema_7", "ema_25", "ema_99", "rsi", "macd", "macd_signal", "macd_hist"):
        assert not np.isnan(row[col]), f"{col} is NaN on last row"


# ── detect_trend ──────────────────────────────────────────────────────────────

def test_detect_trend_bullish() -> None:
    df = compute_indicators(_rising_klines(200))
    result = detect_trend(df.iloc[-1])
    assert result == EMAAlignment.BULLISH


def test_detect_trend_neutral_when_nan() -> None:
    """If EMA columns are NaN (insufficient data) → NEUTRAL."""
    df = compute_indicators(_flat_klines(10))  # too few rows for EMA-99
    result = detect_trend(df.iloc[-1])
    assert result == EMAAlignment.NEUTRAL


def test_detect_trend_bearish() -> None:
    """Declining prices should produce a bearish EMA stack."""
    klines = list(reversed(_rising_klines(200)))
    # Re-assign monotonic timestamps so they sort correctly
    for i, k in enumerate(klines):
        k.open_time  = i * 60_000
        k.close_time = i * 60_000 + 59_999
    df = compute_indicators(klines)
    result = detect_trend(df.iloc[-1])
    assert result == EMAAlignment.BEARISH


# ── detect_rejection_candle ───────────────────────────────────────────────────

def test_detect_rejection_candle_upper_wick() -> None:
    """Long upper wick → bearish rejection."""
    # body = 2, upper_wick = 10, lower_wick = 1
    k = _make_kline(open_=100, high=114, low=99, close=102)
    df = klines_to_df([k])
    df = add_candle_metrics(df)
    result = detect_rejection_candle(df.iloc[0])
    assert result == CandleBehavior.REJECTION_BEAR


def test_detect_rejection_candle_lower_wick() -> None:
    """Long lower wick → bullish rejection."""
    # body = 2, upper_wick = 1, lower_wick = 10
    k = _make_kline(open_=110, high=111, low=100, close=112)
    df = klines_to_df([k])
    df = add_candle_metrics(df)
    result = detect_rejection_candle(df.iloc[0])
    assert result == CandleBehavior.REJECTION_BULL


def test_detect_rejection_candle_none_for_large_body() -> None:
    """Candle with large body and small wicks → no rejection."""
    k = _make_kline(open_=100, high=110.5, low=99.5, close=110)
    df = klines_to_df([k])
    df = add_candle_metrics(df)
    result = detect_rejection_candle(df.iloc[0])
    assert result is None


# ── detect_strong_momentum ────────────────────────────────────────────────────

def _high_vol_kline(volume: float) -> Candle:
    """A large bullish candle placed after _flat_klines(30) in time."""
    return _make_kline(
        open_=100, high=110, low=99, close=109,
        volume=volume,
        open_time=30 * 60_000,      # after 30 flat klines
        close_time=30 * 60_000 + 59_999,
    )


def test_detect_strong_momentum_bull() -> None:
    """Large bullish body + high volume → STRONG_BULL."""
    k = _high_vol_kline(volume=5000.0)
    df = klines_to_df(_flat_klines(30) + [k])
    df = add_volume_metrics(df)
    df = add_candle_metrics(df)
    result = detect_strong_momentum(df.iloc[-1])
    assert result == CandleBehavior.STRONG_BULL


def test_detect_strong_momentum_none_low_volume() -> None:
    """Even a large-body candle with low volume → no momentum signal."""
    k = _high_vol_kline(volume=100.0)
    df = klines_to_df(_flat_klines(30) + [k])
    df = add_volume_metrics(df)
    df = add_candle_metrics(df)
    result = detect_strong_momentum(df.iloc[-1])
    assert result is None


# ── classify_rsi ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("rsi, expected", [
    (75.0, RSIState.OVERBOUGHT),
    (70.0, RSIState.OVERBOUGHT),
    (50.0, RSIState.NEUTRAL),
    (30.0, RSIState.OVERSOLD),
    (20.0, RSIState.OVERSOLD),
    (None, RSIState.NEUTRAL),
    (float("nan"), RSIState.NEUTRAL),
])
def test_classify_rsi(rsi: object, expected: RSIState) -> None:
    assert classify_rsi(rsi) == expected  # type: ignore[arg-type]


# ── classify_macd ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("hist, expected", [
    (0.5,  MACDDirection.BULLISH),
    (-0.5, MACDDirection.BEARISH),
    (0.0,  MACDDirection.NEUTRAL),
    (None, MACDDirection.NEUTRAL),
    (float("nan"), MACDDirection.NEUTRAL),
])
def test_classify_macd(hist: object, expected: MACDDirection) -> None:
    assert classify_macd(hist) == expected  # type: ignore[arg-type]


# ── classify_volume ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("ratio, expected", [
    (2.0,  VolumeStrength.HIGH),
    (1.5,  VolumeStrength.HIGH),
    (1.0,  VolumeStrength.NORMAL),
    (0.7,  VolumeStrength.LOW),
    (0.5,  VolumeStrength.LOW),
    (None, VolumeStrength.NORMAL),
    (float("nan"), VolumeStrength.NORMAL),
])
def test_classify_volume(ratio: object, expected: VolumeStrength) -> None:
    assert classify_volume(ratio) == expected  # type: ignore[arg-type]


# ── Legacy scalar helpers ─────────────────────────────────────────────────────

def test_legacy_compute_rsi_basic() -> None:
    closes = [float(i) for i in range(1, 30)]
    rsi = compute_rsi(closes)
    assert rsi is not None
    assert 0 <= rsi <= 100


def test_legacy_compute_rsi_none_for_short() -> None:
    assert compute_rsi([100.0, 101.0]) is None


def test_legacy_compute_ema_basic() -> None:
    closes = [float(i) for i in range(1, 25)]
    ema = compute_ema(closes, period=20)
    assert ema is not None
    assert ema > 0


def test_legacy_compute_atr() -> None:
    highs  = [100 + i for i in range(20)]
    lows   = [95 + i  for i in range(20)]
    closes = [98 + i  for i in range(20)]
    atr = compute_atr(highs, lows, closes)
    assert atr is not None
    assert atr > 0


def test_legacy_compute_risk_reward() -> None:
    assert compute_risk_reward(entry=100, stop_loss=95, take_profit=115) == 3.0


def test_legacy_compute_risk_reward_zero_risk() -> None:
    assert compute_risk_reward(entry=100, stop_loss=100, take_profit=115) == 0.0
