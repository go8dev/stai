"""
Setup scoring service — Phase 7 (rule-based, no AI).

Architecture
------------
Every major scoring component is a **pure module-level function** so it can be:
  - tested in isolation without mocks
  - called from AI review layers in later phases without re-implementing logic

Public functions
----------------
score_btc_regime_alignment(regime, side)
    → (points: float, reason: str)

score_h1_ema(ema_alignment, side)
    → (points: float, reason: str)

score_m15_ema(ema_alignment, side)
    → (points: float, reason: str)

score_m15_rsi(rsi_state, side)
    → (points: float, reason: str)

score_m15_macd(macd_direction, side)
    → (points: float, reason: str)

score_m15_candle(candle_behavior, side)
    → (points: float, reason: str)

score_volume(volume_strength)
    → (points: float, reason: str)

score_pullback_zone(snap, side)
    → (points: float, reason: str)
    (uses price vs EMA-7, EMA-25, EMA-99 to judge pullback depth)

derive_trade_levels(snap, side)
    → dict with entry_zone_low/high, stop_loss, tp1/2/3, invalidation_level

score_candidate(candidate, btc_regime_resp, h1_snap, m15_snap)
    → ScoredSetup (assembles all sub-scores + derive_trade_levels)

score_all_candidates(candidates, min_score)
    → SetupScoringResult (fetches BTC regime + snapshots, scores all)

Scoring model (max = 100 pts)
------------------------------
  BTC regime alignment    : 0–25
  1H EMA alignment        : 0–20
  15M EMA alignment       : 0–10
  15M RSI state           : 0– 5
  15M MACD direction      : 0– 5
  15M candle behavior     : 0– 5
  Volume quality          : 0–10
  Pullback/bounce zone    : 0–20

Design rules
------------
- Bad signals score 0 — there are no negative points.
- Every scoring call returns (float, str): points and a human-readable reason.
- Business logic is never inside route handlers.
- No AI calls here — this is a pure rule engine.
- All thresholds live in stai.analytics.core.constants (never hard-coded here).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from stai.analytics.core.constants import (
    CandleBehavior,
    EMAAlignment,
    LONG_STOP_LOSS_BUFFER_PCT,
    LONG_TP1_MULT,
    LONG_TP2_MULT,
    LONG_TP3_MULT,
    MACDDirection,
    MarketRegime,
    RSIState,
    SETUP_MIN_SCORE_THRESHOLD,
    SETUP_SCORE_BTC_REGIME_ALIGNED,
    SETUP_SCORE_BTC_REGIME_CONFLICT,
    SETUP_SCORE_BTC_REGIME_NEUTRAL,
    SETUP_SCORE_H1_EMA_ALIGNED,
    SETUP_SCORE_H1_EMA_CONFLICT,
    SETUP_SCORE_H1_EMA_NEUTRAL,
    SETUP_SCORE_M15_CANDLE_CONFLICT,
    SETUP_SCORE_M15_CANDLE_MOMENTUM,
    SETUP_SCORE_M15_CANDLE_NEUTRAL,
    SETUP_SCORE_M15_CANDLE_REVERSAL,
    SETUP_SCORE_M15_EMA_ALIGNED,
    SETUP_SCORE_M15_EMA_CONFLICT,
    SETUP_SCORE_M15_EMA_NEUTRAL,
    SETUP_SCORE_M15_MACD_ALIGNED,
    SETUP_SCORE_M15_MACD_CONFLICT,
    SETUP_SCORE_M15_MACD_NEUTRAL,
    SETUP_SCORE_M15_RSI_CONFLICT,
    SETUP_SCORE_M15_RSI_IDEAL,
    SETUP_SCORE_M15_RSI_NEUTRAL,
    SETUP_SCORE_PULLBACK_EXTENDED,
    SETUP_SCORE_PULLBACK_NEAR,
    SETUP_SCORE_PULLBACK_OPTIMAL,
    SETUP_SCORE_PULLBACK_SHALLOW,
    SETUP_SCORE_VOLUME_HIGH,
    SETUP_SCORE_VOLUME_LOW,
    SETUP_SCORE_VOLUME_NORMAL,
    SHORT_STOP_LOSS_BUFFER_PCT,
    SHORT_TP1_MULT,
    SHORT_TP2_MULT,
    SHORT_TP3_MULT,
    StrategyType,
    Timeframe,
    TradeSide,
    VolumeStrength,
)
from stai.core.logging import StructuredLogger
from stai.analytics.schemas.btc_regime import BTCRegimeResponse
from stai.analytics.schemas.market_snapshot import MarketSnapshot
from stai.analytics.schemas.scanner import ScannerCandidate
from stai.analytics.schemas.setup_score import ScoredSetup, SetupScoringResult
from stai.analytics.services.btc_regime_service import get_btc_regime_multi_tf as get_btc_regime
from stai.analytics.services.market_service import get_market_snapshot

logger = StructuredLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Pure scoring functions — no I/O, no async, fully testable
# ══════════════════════════════════════════════════════════════════════════════

def score_btc_regime_alignment(
    regime: MarketRegime,
    side: TradeSide,
) -> Tuple[float, str]:
    """
    Award points based on whether the BTC macro regime aligns with the trade.

    Max: 25 pts.

    Rules:
      BULLISH + LONG or BEARISH + SHORT → fully aligned (+25)
      RANGING / VOLATILE / UNKNOWN      → neutral environment (+10)
      BULLISH + SHORT or BEARISH + LONG → opposing regime (+0)
    """
    bullish_regimes = {MarketRegime.BULLISH}
    bearish_regimes = {MarketRegime.BEARISH}
    neutral_regimes = {MarketRegime.RANGING, MarketRegime.SIDEWAYS,
                       MarketRegime.VOLATILE, MarketRegime.UNKNOWN}

    if (regime in bullish_regimes and side == TradeSide.LONG) or (
        regime in bearish_regimes and side == TradeSide.SHORT
    ):
        pts = SETUP_SCORE_BTC_REGIME_ALIGNED
        return pts, (
            f"BTC regime is {regime.value} — fully aligned with {side.value} setup (+{pts:.0f})"
        )

    if regime in neutral_regimes:
        pts = SETUP_SCORE_BTC_REGIME_NEUTRAL
        return pts, (
            f"BTC regime is {regime.value} — neutral environment, no strong tailwind (+{pts:.0f})"
        )

    # Conflict: bullish + short or bearish + long
    pts = SETUP_SCORE_BTC_REGIME_CONFLICT
    return pts, (
        f"BTC regime is {regime.value} — opposes {side.value} setup (−25 effective, +{pts:.0f})"
    )


def score_h1_ema(
    ema_alignment: EMAAlignment,
    side: TradeSide,
) -> Tuple[float, str]:
    """
    Score the higher-timeframe (1H) EMA stack alignment.

    Max: 20 pts.

    Rules:
      Stack aligned with trade direction  → +20
      Neutral stack                        → +5
      Stack opposing trade direction       → +0
    """
    if ema_alignment == EMAAlignment.BULLISH and side == TradeSide.LONG:
        pts = SETUP_SCORE_H1_EMA_ALIGNED
        return pts, f"1H EMA stack bullish — higher-TF trend supports long (+{pts:.0f})"

    if ema_alignment == EMAAlignment.BEARISH and side == TradeSide.SHORT:
        pts = SETUP_SCORE_H1_EMA_ALIGNED
        return pts, f"1H EMA stack bearish — higher-TF trend supports short (+{pts:.0f})"

    if ema_alignment == EMAAlignment.NEUTRAL:
        pts = SETUP_SCORE_H1_EMA_NEUTRAL
        return pts, f"1H EMA stack neutral — no clear structural trend (+{pts:.0f})"

    pts = SETUP_SCORE_H1_EMA_CONFLICT
    return pts, (
        f"1H EMA stack {ema_alignment.value} — opposes {side.value} direction (+{pts:.0f})"
    )


def score_m15_ema(
    ema_alignment: EMAAlignment,
    side: TradeSide,
) -> Tuple[float, str]:
    """
    Score the execution timeframe (15M) EMA stack.

    Max: 10 pts.
    """
    if ema_alignment == EMAAlignment.BULLISH and side == TradeSide.LONG:
        pts = SETUP_SCORE_M15_EMA_ALIGNED
        return pts, f"15M EMA stack bullish — execution TF confirms long (+{pts:.0f})"

    if ema_alignment == EMAAlignment.BEARISH and side == TradeSide.SHORT:
        pts = SETUP_SCORE_M15_EMA_ALIGNED
        return pts, f"15M EMA stack bearish — execution TF confirms short (+{pts:.0f})"

    if ema_alignment == EMAAlignment.NEUTRAL:
        pts = SETUP_SCORE_M15_EMA_NEUTRAL
        return pts, f"15M EMA stack neutral — execution TF undecided (+{pts:.0f})"

    pts = SETUP_SCORE_M15_EMA_CONFLICT
    return pts, (
        f"15M EMA stack {ema_alignment.value} — opposes {side.value} direction (+{pts:.0f})"
    )


def score_m15_rsi(
    rsi_state: RSIState,
    side: TradeSide,
) -> Tuple[float, str]:
    """
    Score RSI state on the execution timeframe.

    Max: 5 pts.

    Ideal state:
      LONG  → RSI OVERSOLD  (price exhausted sellers, bounce imminent)
      SHORT → RSI OVERBOUGHT (price exhausted buyers, reversal imminent)

    Neutral RSI earns partial credit: pullback may still be valid,
    but there is no RSI confirmation.
    """
    if rsi_state == RSIState.OVERSOLD and side == TradeSide.LONG:
        pts = SETUP_SCORE_M15_RSI_IDEAL
        return pts, f"15M RSI oversold — momentum exhaustion supports long reversal (+{pts:.0f})"

    if rsi_state == RSIState.OVERBOUGHT and side == TradeSide.SHORT:
        pts = SETUP_SCORE_M15_RSI_IDEAL
        return pts, f"15M RSI overbought — momentum exhaustion supports short reversal (+{pts:.0f})"

    if rsi_state == RSIState.NEUTRAL:
        pts = SETUP_SCORE_M15_RSI_NEUTRAL
        return pts, f"15M RSI neutral — no extreme momentum reading (+{pts:.0f})"

    # Conflicting RSI (overbought on a long, or oversold on a short)
    pts = SETUP_SCORE_M15_RSI_CONFLICT
    return pts, (
        f"15M RSI {rsi_state.value} — conflicts with {side.value} direction (+{pts:.0f})"
    )


def score_m15_macd(
    macd_direction: MACDDirection,
    side: TradeSide,
) -> Tuple[float, str]:
    """
    Score MACD histogram direction on the execution timeframe.

    Max: 5 pts.

    Aligned means MACD histogram matches the trade direction:
      LONG  → histogram > 0 (bullish momentum building)
      SHORT → histogram < 0 (bearish momentum building)
    """
    if macd_direction == MACDDirection.BULLISH and side == TradeSide.LONG:
        pts = SETUP_SCORE_M15_MACD_ALIGNED
        return pts, f"15M MACD histogram bullish — momentum building for long (+{pts:.0f})"

    if macd_direction == MACDDirection.BEARISH and side == TradeSide.SHORT:
        pts = SETUP_SCORE_M15_MACD_ALIGNED
        return pts, f"15M MACD histogram bearish — momentum building for short (+{pts:.0f})"

    if macd_direction == MACDDirection.NEUTRAL:
        pts = SETUP_SCORE_M15_MACD_NEUTRAL
        return pts, f"15M MACD neutral — no histogram confirmation (+{pts:.0f})"

    pts = SETUP_SCORE_M15_MACD_CONFLICT
    return pts, (
        f"15M MACD {macd_direction.value} — opposes {side.value} direction (+{pts:.0f})"
    )


def score_m15_candle(
    candle_behavior: CandleBehavior,
    side: TradeSide,
) -> Tuple[float, str]:
    """
    Score the last candle pattern on the execution timeframe.

    Max: 5 pts.

    Scoring ladder:
      Reversal candle in trade direction  → +5  (best signal: price rejecting key level)
      Momentum candle in trade direction  → +3  (trend continuing, but not a reversal)
      Neutral candle                       → +1  (no helpful information)
      Candle opposing direction            → +0
    """
    reversal_long  = CandleBehavior.REJECTION_BULL
    reversal_short = CandleBehavior.REJECTION_BEAR
    momentum_long  = CandleBehavior.STRONG_BULL
    momentum_short = CandleBehavior.STRONG_BEAR

    if (
        (candle_behavior == reversal_long  and side == TradeSide.LONG) or
        (candle_behavior == reversal_short and side == TradeSide.SHORT)
    ):
        pts = SETUP_SCORE_M15_CANDLE_REVERSAL
        return pts, (
            f"15M candle: {candle_behavior.value} — reversal signal at the zone (+{pts:.0f})"
        )

    if (
        (candle_behavior == momentum_long  and side == TradeSide.LONG) or
        (candle_behavior == momentum_short and side == TradeSide.SHORT)
    ):
        pts = SETUP_SCORE_M15_CANDLE_MOMENTUM
        return pts, (
            f"15M candle: {candle_behavior.value} — momentum confirms direction (+{pts:.0f})"
        )

    if candle_behavior == CandleBehavior.NEUTRAL:
        pts = SETUP_SCORE_M15_CANDLE_NEUTRAL
        return pts, f"15M candle: neutral — no directional signal (+{pts:.0f})"

    pts = SETUP_SCORE_M15_CANDLE_CONFLICT
    return pts, (
        f"15M candle: {candle_behavior.value} — opposing candle pattern (+{pts:.0f})"
    )


def score_volume(volume_strength: VolumeStrength) -> Tuple[float, str]:
    """
    Score volume quality on the execution timeframe.

    Max: 10 pts.

    High volume means institutional participation and confirms the move.
    Low volume suggests weak conviction — the setup is less reliable.
    """
    if volume_strength == VolumeStrength.HIGH:
        pts = SETUP_SCORE_VOLUME_HIGH
        return pts, f"Volume high (≥1.5× avg) — strong participation confirms setup (+{pts:.0f})"

    if volume_strength == VolumeStrength.NORMAL:
        pts = SETUP_SCORE_VOLUME_NORMAL
        return pts, f"Volume normal — adequate liquidity, no strong conviction signal (+{pts:.0f})"

    pts = SETUP_SCORE_VOLUME_LOW
    return pts, f"Volume low (<0.7× avg) — weak participation, low conviction (+{pts:.0f})"


def score_pullback_zone(
    snap: Optional[MarketSnapshot],
    side: TradeSide,
) -> Tuple[float, str]:
    """
    Score how well-positioned the price is within the pullback / bounce zone.

    Max: 20 pts.

    Uses the 1H snapshot's EMA stack to judge the depth of the retracement.

    Long (pullback in bullish trend):
      Optimal  → price ≤ ema_7  and  price ≥ ema_25   (pulled back into EMA cluster)
      Near     → price ≤ ema_7  and  price < ema_25   but  price ≥ ema_99  (deeper pullback)
      Shallow  → price > ema_7  (barely pulled back — trend intact, not ideal entry)
      Extended → price < ema_99 (too deep — structural break risk)

    Short (bounce in bearish trend):
      Optimal  → price ≥ ema_7  and  price ≤ ema_25   (bounced into EMA cluster)
      Near     → price ≥ ema_7  and  price > ema_25   but  price ≤ ema_99  (deeper bounce)
      Shallow  → price < ema_7  (barely bounced — trend intact, not ideal entry)
      Extended → price > ema_99 (too deep a bounce — structural reclaim risk)

    If snap is None or EMAs are unavailable, award NEAR as a conservative default.
    """
    if snap is None or snap.ema_7 is None or snap.ema_25 is None or snap.ema_99 is None:
        pts = SETUP_SCORE_PULLBACK_NEAR
        return pts, (
            f"1H EMA data unavailable — conservative pullback credit awarded (+{pts:.0f})"
        )

    price  = snap.current_price
    ema_7  = snap.ema_7
    ema_25 = snap.ema_25
    ema_99 = snap.ema_99

    if side == TradeSide.LONG:
        if price < ema_99:
            pts = SETUP_SCORE_PULLBACK_EXTENDED
            return pts, (
                f"1H price ({price:.4f}) below EMA-99 ({ema_99:.4f}) — "
                f"pullback too deep, structural break risk (+{pts:.0f})"
            )
        if price <= ema_7 and price >= ema_25:
            pts = SETUP_SCORE_PULLBACK_OPTIMAL
            return pts, (
                f"1H price ({price:.4f}) in EMA-7/25 zone — "
                f"optimal pullback depth for long entry (+{pts:.0f})"
            )
        if price <= ema_7 and price < ema_25 and price >= ema_99:
            pts = SETUP_SCORE_PULLBACK_NEAR
            return pts, (
                f"1H price ({price:.4f}) between EMA-25 and EMA-99 — "
                f"deeper pullback, still valid (+{pts:.0f})"
            )
        # price > ema_7 — barely pulled back
        pts = SETUP_SCORE_PULLBACK_SHALLOW
        return pts, (
            f"1H price ({price:.4f}) above EMA-7 ({ema_7:.4f}) — "
            f"shallow pullback, wait for deeper retracement (+{pts:.0f})"
        )

    else:  # SHORT
        if price > ema_99:
            pts = SETUP_SCORE_PULLBACK_EXTENDED
            return pts, (
                f"1H price ({price:.4f}) above EMA-99 ({ema_99:.4f}) — "
                f"bounce too deep, structure reclaim risk (+{pts:.0f})"
            )
        if price >= ema_7 and price <= ema_25:
            pts = SETUP_SCORE_PULLBACK_OPTIMAL
            return pts, (
                f"1H price ({price:.4f}) in EMA-7/25 zone — "
                f"optimal bounce depth for short entry (+{pts:.0f})"
            )
        if price >= ema_7 and price > ema_25 and price <= ema_99:
            pts = SETUP_SCORE_PULLBACK_NEAR
            return pts, (
                f"1H price ({price:.4f}) between EMA-25 and EMA-99 — "
                f"deeper bounce, still tradable (+{pts:.0f})"
            )
        # price < ema_7 — barely bounced
        pts = SETUP_SCORE_PULLBACK_SHALLOW
        return pts, (
            f"1H price ({price:.4f}) below EMA-7 ({ema_7:.4f}) — "
            f"shallow bounce, wait for price to reclaim EMA-7 (+{pts:.0f})"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Trade level derivation
# ══════════════════════════════════════════════════════════════════════════════

def derive_trade_levels(
    snap: Optional[MarketSnapshot],
    side: TradeSide,
    current_price: float,
) -> dict:
    """
    Derive entry zone, stop-loss, take-profit levels, and invalidation level.

    Uses the 1H EMA stack as the structural reference.  Falls back to
    percentage multiples from current_price when EMAs are unavailable.

    Long pullback strategy
    ----------------------
    entry_zone_low  = ema_25 × 0.998       (just below the 25-EMA support)
    entry_zone_high = ema_7  × 1.002       (just above the 7-EMA — the limit of the zone)
    stop_loss       = ema_99 × (1 − buffer) (below the macro structure)
    tp1             = ema_7  × TP1_MULT    (+1.5% quick scalp)
    tp2             = ema_7  × TP2_MULT    (+3.5% moderate target)
    tp3             = ema_7  × TP3_MULT    (+7.0% extended swing)
    invalidation    = stop_loss × 0.995    (hard close below structure)

    Short bounce strategy
    ---------------------
    entry_zone_low  = ema_7  × 0.998       (just below — limit of entry zone)
    entry_zone_high = ema_25 × 1.002       (just above the 25-EMA resistance)
    stop_loss       = ema_99 × (1 + buffer) (above the macro structure)
    tp1             = ema_7  × TP1_MULT    (−1.5%)
    tp2             = ema_7  × TP2_MULT    (−3.5%)
    tp3             = ema_7  × TP3_MULT    (−7.0%)
    invalidation    = stop_loss × 1.005

    Returns
    -------
    dict with keys: entry_zone_low, entry_zone_high, stop_loss,
                    tp1, tp2, tp3, invalidation_level
    """
    ema_7  = snap.ema_7  if snap and snap.ema_7  is not None else current_price
    ema_25 = snap.ema_25 if snap and snap.ema_25 is not None else current_price
    ema_99 = snap.ema_99 if snap and snap.ema_99 is not None else current_price

    if side == TradeSide.LONG:
        entry_zone_low  = ema_25 * 0.998
        entry_zone_high = ema_7  * 1.002
        stop_loss       = ema_99 * (1.0 - LONG_STOP_LOSS_BUFFER_PCT)
        tp1             = ema_7  * LONG_TP1_MULT
        tp2             = ema_7  * LONG_TP2_MULT
        tp3             = ema_7  * LONG_TP3_MULT
        invalidation    = stop_loss * 0.995
    else:
        entry_zone_low  = ema_7  * 0.998
        entry_zone_high = ema_25 * 1.002
        stop_loss       = ema_99 * (1.0 + SHORT_STOP_LOSS_BUFFER_PCT)
        tp1             = ema_7  * SHORT_TP1_MULT
        tp2             = ema_7  * SHORT_TP2_MULT
        tp3             = ema_7  * SHORT_TP3_MULT
        invalidation    = stop_loss * 1.005

    return {
        "entry_zone_low":     round(entry_zone_low,  8),
        "entry_zone_high":    round(entry_zone_high, 8),
        "stop_loss":          round(stop_loss,        8),
        "tp1":                round(tp1,              8),
        "tp2":                round(tp2,              8),
        "tp3":                round(tp3,              8),
        "invalidation_level": round(invalidation,     8),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Candidate scoring assembly
# ══════════════════════════════════════════════════════════════════════════════

def score_candidate(
    candidate:       ScannerCandidate,
    btc_regime:      MarketRegime,
    h1_snap:         Optional[MarketSnapshot],
    m15_snap:        Optional[MarketSnapshot],
) -> ScoredSetup:
    """
    Score a single scanner candidate against all rule-based criteria.

    Assembles sub-scores from the pure scoring functions above, derives
    trade levels, and returns a fully populated ScoredSetup.

    Parameters
    ----------
    candidate   : Scanner candidate with symbol, side, price data.
    btc_regime  : Current BTC macro regime label.
    h1_snap     : 1-hour MarketSnapshot for the candidate's symbol.
    m15_snap    : 15-minute MarketSnapshot for the candidate's symbol.

    Returns
    -------
    ScoredSetup with score 0–100, full reasons list, and derived levels.
    """
    side = candidate.candidate_side
    strategy = (
        StrategyType.LONG_PULLBACK_BULLISH
        if side == TradeSide.LONG
        else StrategyType.SHORT_BOUNCE_BEARISH
    )

    reasons: List[str] = []
    total_score = 0.0

    # 1. BTC regime alignment (0–25)
    pts, reason = score_btc_regime_alignment(btc_regime, side)
    total_score += pts
    reasons.append(reason)

    # 2. 1H EMA alignment (0–20)
    h1_ema = h1_snap.ema_alignment if h1_snap else EMAAlignment.NEUTRAL
    pts, reason = score_h1_ema(h1_ema, side)
    total_score += pts
    reasons.append(reason)

    # 3. 15M EMA alignment (0–10)
    m15_ema = m15_snap.ema_alignment if m15_snap else EMAAlignment.NEUTRAL
    pts, reason = score_m15_ema(m15_ema, side)
    total_score += pts
    reasons.append(reason)

    # 4. 15M RSI state (0–5)
    m15_rsi = m15_snap.rsi_state if m15_snap else RSIState.NEUTRAL
    pts, reason = score_m15_rsi(m15_rsi, side)
    total_score += pts
    reasons.append(reason)

    # 5. 15M MACD direction (0–5)
    m15_macd = m15_snap.macd_direction if m15_snap else MACDDirection.NEUTRAL
    pts, reason = score_m15_macd(m15_macd, side)
    total_score += pts
    reasons.append(reason)

    # 6. 15M candle behavior (0–5)
    m15_candle = m15_snap.candle_behavior if m15_snap else CandleBehavior.NEUTRAL
    pts, reason = score_m15_candle(m15_candle, side)
    total_score += pts
    reasons.append(reason)

    # 7. Volume quality (0–10) — prefer 15M, fallback to 1H
    vol_strength = (
        (m15_snap.volume_strength if m15_snap else None)
        or (h1_snap.volume_strength if h1_snap else VolumeStrength.NORMAL)
    )
    pts, reason = score_volume(vol_strength)
    total_score += pts
    reasons.append(reason)

    # 8. Pullback / bounce zone quality (0–20) — uses 1H snap
    pts, reason = score_pullback_zone(h1_snap, side)
    total_score += pts
    reasons.append(reason)

    # Derive trade levels from 1H EMA structure
    current_price = (
        h1_snap.current_price if h1_snap else candidate.last_price
    )
    levels = derive_trade_levels(h1_snap, side, current_price)

    logger.info(
        "Scored candidate",
        symbol=candidate.symbol,
        side=side.value,
        score=round(total_score, 1),
    )

    now = datetime.now(timezone.utc).isoformat()
    return ScoredSetup(
        symbol          = candidate.symbol,
        side            = side,
        strategy_type   = strategy,
        score           = round(total_score, 2),
        reasons         = reasons,
        scored_at       = now,
        **levels,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Async entrypoint — fetches all live data and scores the full candidate list
# ══════════════════════════════════════════════════════════════════════════════

async def score_all_candidates(
    candidates:  List[ScannerCandidate],
    min_score:   float = SETUP_MIN_SCORE_THRESHOLD,
) -> SetupScoringResult:
    """
    Score every candidate in *candidates* and return those above *min_score*.

    Flow
    ----
    1. Fetch the BTC regime (live).
    2. For each candidate fetch 1H + 15M MarketSnapshots (via market_service).
    3. Score each candidate.
    4. Filter by min_score.
    5. Sort passed setups by score descending.
    6. Return SetupScoringResult.

    Snapshot fetch errors are non-fatal: a failed fetch yields None,
    and the scorer awards conservative defaults (no crash).
    """
    now = datetime.now(timezone.utc).isoformat()

    # 1. BTC regime
    try:
        btc_resp = await get_btc_regime()
    except Exception as exc:
        logger.warning("BTC regime fetch failed — using UNKNOWN", error=str(exc))
        btc_resp = BTCRegimeResponse(
            regime           = MarketRegime.UNKNOWN,
            confidence       = 0.0,
            composite_score  = 0.0,
            reasons          = ["BTC regime unavailable"],
            updated_at       = now,
        )

    scored: List[ScoredSetup] = []

    for candidate in candidates:
        # 2. Fetch snapshots (non-fatal)
        h1_snap:  Optional[MarketSnapshot] = None
        m15_snap: Optional[MarketSnapshot] = None

        try:
            h1_snap = await get_market_snapshot(candidate.symbol, Timeframe.H1)
        except Exception as exc:
            logger.warning(
                "1H snapshot failed",
                symbol=candidate.symbol,
                error=str(exc),
            )

        try:
            m15_snap = await get_market_snapshot(candidate.symbol, Timeframe.M15)
        except Exception as exc:
            logger.warning(
                "15M snapshot failed",
                symbol=candidate.symbol,
                error=str(exc),
            )

        # 3. Score
        setup = score_candidate(candidate, btc_resp.regime, h1_snap, m15_snap)
        scored.append(setup)

    total_candidates = len(scored)

    # 4. Filter
    passed = [s for s in scored if s.score >= min_score]

    # 5. Sort highest score first
    passed.sort(key=lambda s: s.score, reverse=True)

    logger.info(
        "Setup scoring complete",
        total_candidates=total_candidates,
        total_passed=len(passed),
        min_score=min_score,
        btc_regime=btc_resp.regime.value,
    )

    return SetupScoringResult(
        setups              = passed,
        btc_regime          = btc_resp.regime,
        btc_confidence      = btc_resp.confidence,
        btc_composite_score = btc_resp.composite_score,
        min_score_threshold = min_score,
        total_candidates    = total_candidates,
        total_passed        = len(passed),
        scored_at           = now,
    )
