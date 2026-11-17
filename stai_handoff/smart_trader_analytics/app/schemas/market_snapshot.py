"""
MarketSnapshot schema — structured output of the indicator engine.

One snapshot represents the state of a single symbol on a single timeframe
at the moment the indicators were computed.  All classification fields use
enums from app.core.constants.
"""
from typing import Optional

from pydantic import BaseModel, Field

from app.core.constants import (
    CandleBehavior,
    EMAAlignment,
    MACDDirection,
    RSIState,
    Timeframe,
    VolumeStrength,
)


class MarketSnapshot(BaseModel):
    """Full indicator snapshot for one symbol / timeframe combination."""

    # ── Identity ───────────────────────────────────────────────────────────────
    symbol:        str
    timeframe:     Timeframe

    # ── Price ─────────────────────────────────────────────────────────────────
    current_price: float = Field(..., description="Close price of the last candle")

    # ── EMA stack ─────────────────────────────────────────────────────────────
    ema_7:         Optional[float] = Field(None, description="7-period EMA")
    ema_25:        Optional[float] = Field(None, description="25-period EMA")
    ema_99:        Optional[float] = Field(None, description="99-period EMA")
    ema_alignment: EMAAlignment    = Field(..., description="Bullish / bearish / neutral stack")

    # ── RSI ────────────────────────────────────────────────────────────────────
    rsi:           Optional[float] = Field(None, ge=0, le=100, description="RSI-14 value")
    rsi_state:     RSIState        = Field(..., description="Overbought / oversold / neutral")

    # ── MACD ───────────────────────────────────────────────────────────────────
    macd:          Optional[float] = Field(None, description="MACD line (fast − slow EMA)")
    macd_signal:   Optional[float] = Field(None, description="MACD signal line (9-EMA of MACD)")
    macd_hist:     Optional[float] = Field(None, description="MACD histogram (MACD − signal)")
    macd_direction: MACDDirection  = Field(..., description="Bullish / bearish / neutral histogram")

    # ── Volume ─────────────────────────────────────────────────────────────────
    volume:          float               = Field(..., description="Last candle volume")
    avg_volume:      Optional[float]     = Field(None, description="20-candle rolling average volume")
    volume_ratio:    Optional[float]     = Field(None, description="volume ÷ avg_volume")
    volume_strength: VolumeStrength      = Field(..., description="High / normal / low vs average")

    # ── Candle shape ───────────────────────────────────────────────────────────
    body:            Optional[float]     = Field(None, description="|close − open|")
    upper_wick:      Optional[float]     = Field(None, description="high − max(close, open)")
    lower_wick:      Optional[float]     = Field(None, description="min(close, open) − low")
    body_pct:        Optional[float]     = Field(None, description="body as % of candle range")
    candle_behavior: CandleBehavior      = Field(..., description="Pattern label for the last candle")

    # ── Meta ───────────────────────────────────────────────────────────────────
    computed_at:   str = Field(..., description="ISO-8601 UTC timestamp of computation")
