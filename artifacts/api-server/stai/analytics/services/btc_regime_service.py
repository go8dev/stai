"""
BTC multi-timeframe regime classifier.

Architecture
------------
This module is the single source of truth for BTC market regime detection.
It deliberately contains NO exchange API calls, NO route logic, and NO I/O
beyond delegating to market_service.  Everything is pure signal-scoring.

Classification flow
-------------------
1. Fetch MarketSnapshot for BTCUSDT on 1h and 15m via market_service.
2. Score each snapshot independently on four axes (EMA, RSI, MACD, candle).
3. Weight the timeframe scores (1h × 0.60, 15m × 0.40) into a composite.
4. Threshold the composite to pick a MarketRegime label.
5. Derive confidence from normalised absolute score + timeframe-agreement bonus.
6. Collect ordered, human-readable reason strings.
7. Return a BTCRegimeResponse.

Score scale
-----------
Per timeframe, the score is in the range [−5, +5]:
  EMA alignment   :  ±2.0   (strongest structural signal)
  MACD histogram  :  ±1.0
  RSI state       :  ±1.0   (only at extremes — not neutral)
  Candle behavior :  ±1.0 for strong, ±0.5 for rejection

Positive score → bullish bias.  Negative → bearish.

After timeframe weighting the composite is also in [−5, +5].

Confidence
----------
  base        = abs(composite_score) / REGIME_MAX_RAW_SCORE  →  0.0–1.0
  agreement   = +REGIME_AGREE_BONUS if both TFs lean the same direction
  confidence  = min(1.0, base + agreement)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from stai.analytics.core.constants import (
    REGIME_AGREE_BONUS,
    REGIME_BEARISH_THRESHOLD,
    REGIME_BULLISH_THRESHOLD,
    REGIME_MAX_RAW_SCORE,
    REGIME_SCORE_CANDLE_REJECT,
    REGIME_SCORE_CANDLE_STRONG,
    REGIME_SCORE_EMA_STRONG,
    REGIME_SCORE_MACD,
    REGIME_SCORE_RSI,
    REGIME_WEIGHT_H1,
    REGIME_WEIGHT_M15,
    CandleBehavior,
    EMAAlignment,
    MACDDirection,
    MarketRegime,
    RSIState,
    Timeframe,
)
from stai.core.logging import StructuredLogger
from stai.analytics.schemas.btc_regime import BTCRegimeResponse, SnapshotSummary
from stai.analytics.schemas.market_snapshot import MarketSnapshot
from stai.analytics.services.market_service import get_market_snapshot

logger = StructuredLogger(__name__)

BTC_SYMBOL   = "BTCUSDT"
_CANDLE_LIMIT = 200  # enough for all EMAs and RSI warmup


# ── Per-snapshot scoring ───────────────────────────────────────────────────────

def _score_snapshot(snap: MarketSnapshot) -> Tuple[float, List[str]]:
    """
    Convert a MarketSnapshot into a directional score and a list of reasons.

    Returns
    -------
    score   : float in [−5, +5]; positive = bullish evidence
    reasons : human-readable explanation strings for each contributing signal
    """
    score:   float       = 0.0
    reasons: List[str]   = []
    tf_label             = snap.timeframe.value.upper()

    # ── EMA alignment (±2.0) ─────────────────────────────────────────────────
    if snap.ema_alignment == EMAAlignment.BULLISH:
        score += REGIME_SCORE_EMA_STRONG
        reasons.append(
            f"[{tf_label}] EMA stack is bullish (7 > 25 > 99, price above EMA-7)"
        )
    elif snap.ema_alignment == EMAAlignment.BEARISH:
        score -= REGIME_SCORE_EMA_STRONG
        reasons.append(
            f"[{tf_label}] EMA stack is bearish (7 < 25 < 99, price below EMA-7)"
        )
    else:
        reasons.append(f"[{tf_label}] EMA stack is neutral or mixed")

    # ── MACD histogram direction (±1.0) ───────────────────────────────────────
    if snap.macd_direction == MACDDirection.BULLISH:
        score += REGIME_SCORE_MACD
        reasons.append(f"[{tf_label}] MACD histogram is positive (bullish momentum)")
    elif snap.macd_direction == MACDDirection.BEARISH:
        score -= REGIME_SCORE_MACD
        reasons.append(f"[{tf_label}] MACD histogram is negative (bearish momentum)")

    # ── RSI state (±1.0 only at extremes) ────────────────────────────────────
    if snap.rsi_state == RSIState.OVERSOLD:
        score -= REGIME_SCORE_RSI
        reasons.append(
            f"[{tf_label}] RSI is oversold ({snap.rsi:.1f})"
            if snap.rsi is not None
            else f"[{tf_label}] RSI is oversold"
        )
    elif snap.rsi_state == RSIState.OVERBOUGHT:
        score += REGIME_SCORE_RSI
        reasons.append(
            f"[{tf_label}] RSI is overbought ({snap.rsi:.1f})"
            if snap.rsi is not None
            else f"[{tf_label}] RSI is overbought"
        )

    # ── Candle behavior (±0.5 or ±1.0) ───────────────────────────────────────
    if snap.candle_behavior == CandleBehavior.STRONG_BULL:
        score += REGIME_SCORE_CANDLE_STRONG
        reasons.append(f"[{tf_label}] Strong bullish candle with elevated volume")
    elif snap.candle_behavior == CandleBehavior.STRONG_BEAR:
        score -= REGIME_SCORE_CANDLE_STRONG
        reasons.append(f"[{tf_label}] Strong bearish candle with elevated volume")
    elif snap.candle_behavior == CandleBehavior.REJECTION_BULL:
        score += REGIME_SCORE_CANDLE_REJECT
        reasons.append(f"[{tf_label}] Bullish rejection candle (long lower wick)")
    elif snap.candle_behavior == CandleBehavior.REJECTION_BEAR:
        score -= REGIME_SCORE_CANDLE_REJECT
        reasons.append(f"[{tf_label}] Bearish rejection candle (long upper wick)")

    return score, reasons


def _to_summary(snap: MarketSnapshot, tf_score: float) -> SnapshotSummary:
    """Project a MarketSnapshot + its tf_score into a SnapshotSummary."""
    return SnapshotSummary(
        timeframe       = snap.timeframe,
        current_price   = snap.current_price,
        ema_7           = snap.ema_7,
        ema_25          = snap.ema_25,
        ema_99          = snap.ema_99,
        ema_alignment   = snap.ema_alignment,
        rsi             = snap.rsi,
        rsi_state       = snap.rsi_state,
        macd_hist       = snap.macd_hist,
        macd_direction  = snap.macd_direction,
        volume_ratio    = snap.volume_ratio,
        volume_strength = snap.volume_strength,
        body_pct        = snap.body_pct,
        candle_behavior = snap.candle_behavior,
        tf_score        = round(tf_score, 4),
    )


# ── Regime label + confidence ─────────────────────────────────────────────────

def _classify_composite(
    composite: float,
    h1_score:  float,
    m15_score: float,
) -> Tuple[MarketRegime, float, List[str]]:
    """
    Convert a composite score into a MarketRegime label + confidence.

    Confidence
    ----------
    base        = abs(composite) / REGIME_MAX_RAW_SCORE
    + bonus     if both timeframes lean the same direction
    """
    meta_reasons: List[str] = []

    # ── Detect timeframe agreement ────────────────────────────────────────────
    both_bullish = h1_score > 0 and m15_score > 0
    both_bearish = h1_score < 0 and m15_score < 0
    tf_agree     = both_bullish or both_bearish

    if tf_agree:
        direction = "bullish" if both_bullish else "bearish"
        meta_reasons.append(
            f"Both 1H and 15M timeframes lean {direction} — signals are aligned"
        )
    else:
        meta_reasons.append(
            "1H and 15M timeframes are mixed — treat regime with caution"
        )

    # ── Base confidence from score magnitude ──────────────────────────────────
    base_confidence = min(abs(composite) / REGIME_MAX_RAW_SCORE, 1.0)
    bonus           = REGIME_AGREE_BONUS if tf_agree else 0.0
    confidence      = min(1.0, round(base_confidence + bonus, 4))

    # ── Regime label ─────────────────────────────────────────────────────────
    if composite >= REGIME_BULLISH_THRESHOLD:
        regime = MarketRegime.BULLISH
        meta_reasons.append(
            f"Composite score {composite:+.2f} exceeds bullish threshold "
            f"({REGIME_BULLISH_THRESHOLD:+.1f})"
        )
    elif composite <= REGIME_BEARISH_THRESHOLD:
        regime = MarketRegime.BEARISH
        meta_reasons.append(
            f"Composite score {composite:+.2f} is below bearish threshold "
            f"({REGIME_BEARISH_THRESHOLD:+.1f})"
        )
    else:
        # Score is between thresholds — distinguish volatile vs ranging
        # by whether the timeframes conflict strongly
        h1_strong  = abs(h1_score)  >= REGIME_BULLISH_THRESHOLD
        m15_strong = abs(m15_score) >= REGIME_BULLISH_THRESHOLD
        if h1_strong or m15_strong:
            regime = MarketRegime.VOLATILE
            meta_reasons.append(
                f"Composite score {composite:+.2f} is indecisive but one timeframe "
                "shows strong directional pressure — volatile conditions"
            )
        else:
            regime = MarketRegime.RANGING
            meta_reasons.append(
                f"Composite score {composite:+.2f} shows no clear directional bias"
            )

    return regime, confidence, meta_reasons


# ── Public API ────────────────────────────────────────────────────────────────

async def get_btc_regime_multi_tf() -> BTCRegimeResponse:
    """
    Fetch live BTC snapshots on 1H and 15M, score each, and return a
    BTCRegimeResponse with regime label, confidence, reasons, and summaries.

    Falls back gracefully when one or both timeframes are unavailable.
    """
    now = datetime.now(timezone.utc).isoformat()

    # ── Fetch snapshots (concurrent-safe — both are independent reads) ────────
    h1_snap:  Optional[MarketSnapshot] = await get_market_snapshot(
        BTC_SYMBOL, Timeframe.H1, limit=_CANDLE_LIMIT
    )
    m15_snap: Optional[MarketSnapshot] = await get_market_snapshot(
        BTC_SYMBOL, Timeframe.M15, limit=_CANDLE_LIMIT
    )

    # ── Handle total data loss ────────────────────────────────────────────────
    if h1_snap is None and m15_snap is None:
        logger.warning("Both BTC snapshots unavailable — returning UNKNOWN regime")
        return BTCRegimeResponse(
            regime          = MarketRegime.UNKNOWN,
            confidence      = 0.0,
            composite_score = 0.0,
            reasons         = ["No market data available — the market-data provider may be unreachable"],
            h1_summary      = None,
            m15_summary     = None,
            updated_at      = now,
        )

    # ── Score each available timeframe ────────────────────────────────────────
    all_reasons: List[str] = []

    h1_raw_score:  float = 0.0
    m15_raw_score: float = 0.0
    h1_reasons:    List[str] = []
    m15_reasons:   List[str] = []

    if h1_snap is not None:
        h1_raw_score, h1_reasons = _score_snapshot(h1_snap)
        all_reasons.extend(h1_reasons)
    else:
        logger.warning("1H BTC snapshot unavailable — using 0 for H1 score")
        all_reasons.append("[1H] No data available — H1 score set to zero")

    if m15_snap is not None:
        m15_raw_score, m15_reasons = _score_snapshot(m15_snap)
        all_reasons.extend(m15_reasons)
    else:
        logger.warning("15M BTC snapshot unavailable — using 0 for M15 score")
        all_reasons.append("[15M] No data available — M15 score set to zero")

    # ── Composite score ───────────────────────────────────────────────────────
    # When one TF is missing we still apply its weight (score stays 0) so
    # confidence is naturally penalised.
    composite = round(
        h1_raw_score  * REGIME_WEIGHT_H1 +
        m15_raw_score * REGIME_WEIGHT_M15,
        4,
    )

    # ── Classify ──────────────────────────────────────────────────────────────
    regime, confidence, meta_reasons = _classify_composite(
        composite, h1_raw_score, m15_raw_score
    )
    all_reasons.extend(meta_reasons)

    # ── Build summaries ───────────────────────────────────────────────────────
    h1_summary  = _to_summary(h1_snap,  h1_raw_score)  if h1_snap  else None
    m15_summary = _to_summary(m15_snap, m15_raw_score) if m15_snap else None

    logger.info(
        "BTC multi-TF regime classified",
        regime          = regime.value,
        confidence      = confidence,
        composite_score = composite,
        h1_score        = h1_raw_score,
        m15_score       = m15_raw_score,
    )

    return BTCRegimeResponse(
        regime          = regime,
        confidence      = confidence,
        composite_score = composite,
        reasons         = all_reasons,
        h1_summary      = h1_summary,
        m15_summary     = m15_summary,
        updated_at      = now,
    )
