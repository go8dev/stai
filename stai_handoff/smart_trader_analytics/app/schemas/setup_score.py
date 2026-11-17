"""
Setup scoring schemas — Phase 7.

A ScoredSetup represents a scanner candidate that has been evaluated by the
rule-based scoring engine.  All fields are explainable: every reason for the
score is recorded in the ``reasons`` list.

Hierarchy
---------
ScoredSetup         — one fully evaluated candidate with entry/stop/TP levels.
SetupScoringResult  — batch result: list of setups + BTC regime context.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.core.constants import MarketRegime, StrategyType, TradeSide


class ScoredSetup(BaseModel):
    """
    A scored and levelled trade setup derived from a scanner candidate.

    Score components (all additive, no negatives — bad signals simply score 0):
      BTC regime alignment   :   0 – 25 pts
      1H EMA alignment       :   0 – 20 pts
      15M EMA alignment      :   0 – 10 pts
      15M RSI state          :   0 –  5 pts
      15M MACD direction     :   0 –  5 pts
      15M candle behavior    :   0 –  5 pts
      Volume quality         :   0 – 10 pts
      Pullback/bounce zone   :   0 – 20 pts
      ─────────────────────────────────────
      Total max              :       100 pts
    """

    # ── Identity ───────────────────────────────────────────────────────────────
    symbol:          str           = Field(..., description="Trading pair, e.g. ETHUSDT")
    side:            TradeSide     = Field(..., description="LONG or SHORT")
    strategy_type:   StrategyType  = Field(
        ...,
        description=(
            "long_pullback_in_bullish_trend or "
            "short_the_bounce_in_bearish_trend"
        ),
    )

    # ── Score ──────────────────────────────────────────────────────────────────
    score:           float         = Field(..., ge=0.0, le=100.0,
                                          description="Composite score out of 100")

    # ── Trade levels ───────────────────────────────────────────────────────────
    entry_zone_low:      float     = Field(..., description="Lower bound of the entry zone")
    entry_zone_high:     float     = Field(..., description="Upper bound of the entry zone")
    stop_loss:           float     = Field(..., description="Stop-loss price")
    tp1:                 float     = Field(..., description="Take-profit 1 (conservative)")
    tp2:                 float     = Field(..., description="Take-profit 2 (moderate)")
    tp3:                 float     = Field(..., description="Take-profit 3 (extended)")
    invalidation_level:  float     = Field(
        ...,
        description="Hard invalidation: if price breaches this, the setup is void",
    )

    # ── Explainability ─────────────────────────────────────────────────────────
    reasons:         List[str]     = Field(
        default_factory=list,
        description="Ordered list of scoring reasons (strongest signal first)",
    )

    # ── Snapshot metadata ──────────────────────────────────────────────────────
    scored_at:       str           = Field(..., description="ISO-8601 UTC timestamp")


class SetupScoringResult(BaseModel):
    """
    Batch result from the setup scoring engine.

    Contains all setups that passed the minimum score threshold, plus
    the BTC regime context that was used to score them.
    """

    setups:              List[ScoredSetup] = Field(default_factory=list)

    # BTC regime context used during scoring
    btc_regime:          MarketRegime      = Field(..., description="BTC regime at scoring time")
    btc_confidence:      float             = Field(
        ..., ge=0.0, le=1.0, description="BTC regime confidence (0–1)"
    )
    btc_composite_score: float             = Field(
        ..., description="BTC composite score (−5 to +5)"
    )

    # Metadata
    min_score_threshold: float             = Field(
        ..., description="Minimum score for a setup to be included"
    )
    total_candidates:    int               = Field(
        ..., description="Total candidates passed to the scorer"
    )
    total_passed:        int               = Field(
        ..., description="Candidates that met the score threshold"
    )
    scored_at:           str               = Field(
        ..., description="ISO-8601 UTC timestamp of the scoring run"
    )
