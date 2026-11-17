"""
BTC regime response schemas.

BTCRegimeResponse is the primary output of the multi-timeframe regime
classifier.  It replaces the legacy MarketRegimeResponse for BTC-specific
regime detection and is consumed by the dashboard and strategy engine.

SnapshotSummary is a flattened, human-readable view of a MarketSnapshot,
suitable for embedding in API responses without exposing every raw indicator.
"""
from typing import List, Optional

from pydantic import BaseModel, Field

from stai.analytics.core.constants import (
    CandleBehavior,
    EMAAlignment,
    MACDDirection,
    MarketRegime,
    RSIState,
    Timeframe,
    VolumeStrength,
)


class SnapshotSummary(BaseModel):
    """
    Condensed view of a MarketSnapshot for a single timeframe.

    Carries the classification labels and the key scalar values needed
    for regime reasoning.  Raw indicator values are included so the
    caller can render them in the UI without a second request.
    """

    timeframe:        Timeframe
    current_price:    float          = Field(..., description="Last close price")

    # EMA
    ema_7:            Optional[float] = None
    ema_25:           Optional[float] = None
    ema_99:           Optional[float] = None
    ema_alignment:    EMAAlignment

    # RSI
    rsi:              Optional[float] = Field(None, ge=0, le=100)
    rsi_state:        RSIState

    # MACD
    macd_hist:        Optional[float] = None
    macd_direction:   MACDDirection

    # Volume
    volume_ratio:     Optional[float] = None
    volume_strength:  VolumeStrength

    # Candle
    body_pct:         Optional[float] = None
    candle_behavior:  CandleBehavior

    # Computed timeframe score (−5 to +5, positive = bullish)
    tf_score:         float           = Field(
        ...,
        description="Weighted directional score for this timeframe (−5 to +5)",
    )


class BTCRegimeResponse(BaseModel):
    """
    Full output of the BTC multi-timeframe regime classifier.

    Fields
    ------
    regime          : Classified market regime label.
    confidence      : 0.0–1.0.  Higher means the signals are stronger and
                      more consistent across timeframes.
    composite_score : Raw weighted score before thresholding (−5 to +5).
    reasons         : Ordered list of human-readable explanation strings
                      that justify the regime and confidence values.
    h1_summary      : SnapshotSummary for the 1-hour timeframe.
    m15_summary     : SnapshotSummary for the 15-minute timeframe.
    updated_at      : ISO-8601 UTC timestamp of the classification run.
    """

    regime:           MarketRegime
    confidence:       float          = Field(..., ge=0.0, le=1.0)
    composite_score:  float          = Field(
        ...,
        description="Composite directional score (−5 to +5)",
    )
    reasons:          List[str]       = Field(
        default_factory=list,
        description="Ordered explanation strings (strongest signal first)",
    )
    h1_summary:       Optional[SnapshotSummary]  = None
    m15_summary:      Optional[SnapshotSummary]  = None
    updated_at:       str             = Field(
        ..., description="ISO-8601 UTC timestamp of computation"
    )
