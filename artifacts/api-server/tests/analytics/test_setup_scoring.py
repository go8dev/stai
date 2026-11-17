"""
Tests for the rule-based setup scoring engine — Phase 7.

All pure scoring functions are tested in isolation (no mocks, no async).
The async integration tests mock get_btc_regime and get_market_snapshot.

Coverage:
  - score_btc_regime_alignment
  - score_h1_ema
  - score_m15_ema
  - score_m15_rsi
  - score_m15_macd
  - score_m15_candle
  - score_volume
  - score_pullback_zone
  - derive_trade_levels
  - score_candidate (assembly)
  - score_all_candidates (integration via mocks)
  - Specific scenario tests: bullish aligned long, bearish aligned short,
    conflicting BTC regime, weak-trend rejection, score threshold behavior
"""
from __future__ import annotations

from typing import List, Optional
from unittest.mock import AsyncMock, patch

import pytest

from stai.analytics.core.constants import (
    CandleBehavior,
    EMAAlignment,
    MACDDirection,
    MarketRegime,
    RSIState,
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
    StrategyType,
    Timeframe,
    TradeSide,
    VolumeStrength,
)
from stai.analytics.schemas.btc_regime import BTCRegimeResponse
from stai.analytics.schemas.market_snapshot import MarketSnapshot
from stai.analytics.schemas.scanner import ScannerCandidate
from stai.analytics.schemas.setup_score import ScoredSetup, SetupScoringResult
from stai.analytics.services.setup_scoring_service import (
    derive_trade_levels,
    score_all_candidates,
    score_btc_regime_alignment,
    score_candidate,
    score_h1_ema,
    score_m15_candle,
    score_m15_ema,
    score_m15_macd,
    score_m15_rsi,
    score_pullback_zone,
    score_volume,
)


# ══════════════════════════════════════════════════════════════════════════════
# Factories
# ══════════════════════════════════════════════════════════════════════════════

def _snapshot(
    symbol:          str             = "ETHUSDT",
    timeframe:       Timeframe       = Timeframe.H1,
    price:           float           = 3_000.0,
    ema_7:           Optional[float] = 2_950.0,
    ema_25:          Optional[float] = 2_900.0,
    ema_99:          Optional[float] = 2_800.0,
    ema_alignment:   EMAAlignment    = EMAAlignment.BULLISH,
    rsi:             float           = 45.0,
    rsi_state:       RSIState        = RSIState.NEUTRAL,
    macd_direction:  MACDDirection   = MACDDirection.BULLISH,
    volume_strength: VolumeStrength  = VolumeStrength.NORMAL,
    candle_behavior: CandleBehavior  = CandleBehavior.NEUTRAL,
) -> MarketSnapshot:
    return MarketSnapshot(
        symbol          = symbol,
        timeframe       = timeframe,
        current_price   = price,
        ema_7           = ema_7,
        ema_25          = ema_25,
        ema_99          = ema_99,
        ema_alignment   = ema_alignment,
        rsi             = rsi,
        rsi_state       = rsi_state,
        macd            = 10.0,
        macd_signal     = 5.0,
        macd_hist       = 5.0,
        macd_direction  = macd_direction,
        volume          = 1_000.0,
        avg_volume      = 700.0,
        volume_ratio    = 1.43,
        volume_strength = volume_strength,
        body_pct        = 0.65,
        candle_behavior = candle_behavior,
        computed_at     = "2026-01-01T00:00:00+00:00",
    )


def _candidate(
    symbol: str         = "ETHUSDT",
    side:   TradeSide   = TradeSide.LONG,
    price:  float       = 3_000.0,
    change: float       = 5.0,
) -> ScannerCandidate:
    return ScannerCandidate(
        symbol             = symbol,
        last_price         = price,
        change_percent_24h = change,
        quote_volume       = 200_000_000.0,
        candidate_side     = side,
        scan_reasons       = ["volume ok", "move ok", "long bias"],
        scanned_at         = "2026-01-01T00:00:00+00:00",
    )


def _btc_regime_response(
    regime:          MarketRegime = MarketRegime.BULLISH,
    confidence:      float        = 0.8,
    composite_score: float        = 3.5,
) -> BTCRegimeResponse:
    return BTCRegimeResponse(
        regime          = regime,
        confidence      = confidence,
        composite_score = composite_score,
        reasons         = ["test regime"],
        updated_at      = "2026-01-01T00:00:00+00:00",
    )


# ══════════════════════════════════════════════════════════════════════════════
# score_btc_regime_alignment
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreBtcRegimeAlignment:

    def test_bullish_regime_long_is_aligned(self):
        pts, reason = score_btc_regime_alignment(MarketRegime.BULLISH, TradeSide.LONG)
        assert pts == SETUP_SCORE_BTC_REGIME_ALIGNED
        assert "aligned" in reason.lower() or "bullish" in reason.lower()

    def test_bearish_regime_short_is_aligned(self):
        pts, reason = score_btc_regime_alignment(MarketRegime.BEARISH, TradeSide.SHORT)
        assert pts == SETUP_SCORE_BTC_REGIME_ALIGNED

    def test_bullish_regime_short_is_conflict(self):
        pts, reason = score_btc_regime_alignment(MarketRegime.BULLISH, TradeSide.SHORT)
        assert pts == SETUP_SCORE_BTC_REGIME_CONFLICT
        assert "oppose" in reason.lower() or "conflict" in reason.lower() or "opposes" in reason.lower()

    def test_bearish_regime_long_is_conflict(self):
        pts, _ = score_btc_regime_alignment(MarketRegime.BEARISH, TradeSide.LONG)
        assert pts == SETUP_SCORE_BTC_REGIME_CONFLICT

    def test_ranging_regime_is_neutral(self):
        pts, reason = score_btc_regime_alignment(MarketRegime.RANGING, TradeSide.LONG)
        assert pts == SETUP_SCORE_BTC_REGIME_NEUTRAL
        assert "neutral" in reason.lower() or "ranging" in reason.lower()

    def test_volatile_regime_is_neutral(self):
        pts, _ = score_btc_regime_alignment(MarketRegime.VOLATILE, TradeSide.LONG)
        assert pts == SETUP_SCORE_BTC_REGIME_NEUTRAL

    def test_unknown_regime_is_neutral(self):
        pts, _ = score_btc_regime_alignment(MarketRegime.UNKNOWN, TradeSide.SHORT)
        assert pts == SETUP_SCORE_BTC_REGIME_NEUTRAL

    def test_sideways_regime_is_neutral(self):
        pts, _ = score_btc_regime_alignment(MarketRegime.SIDEWAYS, TradeSide.LONG)
        assert pts == SETUP_SCORE_BTC_REGIME_NEUTRAL

    def test_returns_tuple_of_float_and_str(self):
        result = score_btc_regime_alignment(MarketRegime.BULLISH, TradeSide.LONG)
        assert isinstance(result[0], float)
        assert isinstance(result[1], str)
        assert len(result[1]) > 0


# ══════════════════════════════════════════════════════════════════════════════
# score_h1_ema
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreH1Ema:

    def test_bullish_ema_long_aligned(self):
        pts, _ = score_h1_ema(EMAAlignment.BULLISH, TradeSide.LONG)
        assert pts == SETUP_SCORE_H1_EMA_ALIGNED

    def test_bearish_ema_short_aligned(self):
        pts, _ = score_h1_ema(EMAAlignment.BEARISH, TradeSide.SHORT)
        assert pts == SETUP_SCORE_H1_EMA_ALIGNED

    def test_neutral_ema_partial_credit(self):
        pts, _ = score_h1_ema(EMAAlignment.NEUTRAL, TradeSide.LONG)
        assert pts == SETUP_SCORE_H1_EMA_NEUTRAL

    def test_bullish_ema_short_conflict(self):
        pts, _ = score_h1_ema(EMAAlignment.BULLISH, TradeSide.SHORT)
        assert pts == SETUP_SCORE_H1_EMA_CONFLICT

    def test_bearish_ema_long_conflict(self):
        pts, _ = score_h1_ema(EMAAlignment.BEARISH, TradeSide.LONG)
        assert pts == SETUP_SCORE_H1_EMA_CONFLICT

    def test_reason_mentions_1h(self):
        _, reason = score_h1_ema(EMAAlignment.BULLISH, TradeSide.LONG)
        assert "1H" in reason or "1h" in reason.lower()


# ══════════════════════════════════════════════════════════════════════════════
# score_m15_ema
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreM15Ema:

    def test_bullish_ema_long_aligned(self):
        pts, _ = score_m15_ema(EMAAlignment.BULLISH, TradeSide.LONG)
        assert pts == SETUP_SCORE_M15_EMA_ALIGNED

    def test_bearish_ema_short_aligned(self):
        pts, _ = score_m15_ema(EMAAlignment.BEARISH, TradeSide.SHORT)
        assert pts == SETUP_SCORE_M15_EMA_ALIGNED

    def test_neutral_partial_credit(self):
        pts, _ = score_m15_ema(EMAAlignment.NEUTRAL, TradeSide.LONG)
        assert pts == SETUP_SCORE_M15_EMA_NEUTRAL

    def test_conflict_gives_zero(self):
        pts, _ = score_m15_ema(EMAAlignment.BEARISH, TradeSide.LONG)
        assert pts == SETUP_SCORE_M15_EMA_CONFLICT

    def test_reason_mentions_15m(self):
        _, reason = score_m15_ema(EMAAlignment.BULLISH, TradeSide.LONG)
        assert "15M" in reason or "15m" in reason.lower()


# ══════════════════════════════════════════════════════════════════════════════
# score_m15_rsi
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreM15Rsi:

    def test_oversold_long_is_ideal(self):
        pts, reason = score_m15_rsi(RSIState.OVERSOLD, TradeSide.LONG)
        assert pts == SETUP_SCORE_M15_RSI_IDEAL
        assert "oversold" in reason.lower()

    def test_overbought_short_is_ideal(self):
        pts, reason = score_m15_rsi(RSIState.OVERBOUGHT, TradeSide.SHORT)
        assert pts == SETUP_SCORE_M15_RSI_IDEAL
        assert "overbought" in reason.lower()

    def test_neutral_rsi_partial_credit(self):
        pts, _ = score_m15_rsi(RSIState.NEUTRAL, TradeSide.LONG)
        assert pts == SETUP_SCORE_M15_RSI_NEUTRAL

    def test_overbought_long_is_conflict(self):
        pts, reason = score_m15_rsi(RSIState.OVERBOUGHT, TradeSide.LONG)
        assert pts == SETUP_SCORE_M15_RSI_CONFLICT
        assert "conflict" in reason.lower() or "conflicts" in reason.lower()

    def test_oversold_short_is_conflict(self):
        pts, _ = score_m15_rsi(RSIState.OVERSOLD, TradeSide.SHORT)
        assert pts == SETUP_SCORE_M15_RSI_CONFLICT


# ══════════════════════════════════════════════════════════════════════════════
# score_m15_macd
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreM15Macd:

    def test_bullish_macd_long_aligned(self):
        pts, _ = score_m15_macd(MACDDirection.BULLISH, TradeSide.LONG)
        assert pts == SETUP_SCORE_M15_MACD_ALIGNED

    def test_bearish_macd_short_aligned(self):
        pts, _ = score_m15_macd(MACDDirection.BEARISH, TradeSide.SHORT)
        assert pts == SETUP_SCORE_M15_MACD_ALIGNED

    def test_neutral_macd_zero(self):
        pts, _ = score_m15_macd(MACDDirection.NEUTRAL, TradeSide.LONG)
        assert pts == 0.0

    def test_bearish_macd_long_conflict(self):
        pts, _ = score_m15_macd(MACDDirection.BEARISH, TradeSide.LONG)
        assert pts == SETUP_SCORE_M15_MACD_CONFLICT

    def test_bullish_macd_short_conflict(self):
        pts, _ = score_m15_macd(MACDDirection.BULLISH, TradeSide.SHORT)
        assert pts == SETUP_SCORE_M15_MACD_CONFLICT


# ══════════════════════════════════════════════════════════════════════════════
# score_m15_candle
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreM15Candle:

    def test_rejection_bull_on_long_is_reversal(self):
        pts, reason = score_m15_candle(CandleBehavior.REJECTION_BULL, TradeSide.LONG)
        assert pts == SETUP_SCORE_M15_CANDLE_REVERSAL
        assert "reversal" in reason.lower()

    def test_rejection_bear_on_short_is_reversal(self):
        pts, _ = score_m15_candle(CandleBehavior.REJECTION_BEAR, TradeSide.SHORT)
        assert pts == SETUP_SCORE_M15_CANDLE_REVERSAL

    def test_strong_bull_on_long_is_momentum(self):
        pts, reason = score_m15_candle(CandleBehavior.STRONG_BULL, TradeSide.LONG)
        assert pts == SETUP_SCORE_M15_CANDLE_MOMENTUM
        assert "momentum" in reason.lower()

    def test_strong_bear_on_short_is_momentum(self):
        pts, _ = score_m15_candle(CandleBehavior.STRONG_BEAR, TradeSide.SHORT)
        assert pts == SETUP_SCORE_M15_CANDLE_MOMENTUM

    def test_neutral_candle_minimal_credit(self):
        pts, _ = score_m15_candle(CandleBehavior.NEUTRAL, TradeSide.LONG)
        assert pts == SETUP_SCORE_M15_CANDLE_NEUTRAL

    def test_strong_bear_on_long_is_conflict(self):
        pts, _ = score_m15_candle(CandleBehavior.STRONG_BEAR, TradeSide.LONG)
        assert pts == SETUP_SCORE_M15_CANDLE_CONFLICT

    def test_rejection_bull_on_short_is_conflict(self):
        pts, _ = score_m15_candle(CandleBehavior.REJECTION_BULL, TradeSide.SHORT)
        assert pts == SETUP_SCORE_M15_CANDLE_CONFLICT


# ══════════════════════════════════════════════════════════════════════════════
# score_volume
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreVolume:

    def test_high_volume_max_points(self):
        pts, reason = score_volume(VolumeStrength.HIGH)
        assert pts == SETUP_SCORE_VOLUME_HIGH
        assert "high" in reason.lower()

    def test_normal_volume_partial(self):
        pts, _ = score_volume(VolumeStrength.NORMAL)
        assert pts == SETUP_SCORE_VOLUME_NORMAL

    def test_low_volume_zero(self):
        pts, reason = score_volume(VolumeStrength.LOW)
        assert pts == SETUP_SCORE_VOLUME_LOW
        assert "low" in reason.lower()


# ══════════════════════════════════════════════════════════════════════════════
# score_pullback_zone
# ══════════════════════════════════════════════════════════════════════════════

class TestScorePullbackZone:

    # ── LONG scenarios ────────────────────────────────────────────────────────

    def test_long_price_in_ema7_25_zone_optimal(self):
        snap = _snapshot(price=2_920.0, ema_7=2_950.0, ema_25=2_900.0, ema_99=2_800.0)
        pts, reason = score_pullback_zone(snap, TradeSide.LONG)
        assert pts == SETUP_SCORE_PULLBACK_OPTIMAL
        assert "optimal" in reason.lower()

    def test_long_price_between_ema25_99_near(self):
        # price < ema_7 and price < ema_25 but >= ema_99
        snap = _snapshot(price=2_850.0, ema_7=2_960.0, ema_25=2_910.0, ema_99=2_800.0)
        pts, reason = score_pullback_zone(snap, TradeSide.LONG)
        assert pts == SETUP_SCORE_PULLBACK_NEAR
        assert "deeper" in reason.lower() or "near" in reason.lower() or "valid" in reason.lower()

    def test_long_price_above_ema7_shallow(self):
        snap = _snapshot(price=3_100.0, ema_7=2_950.0, ema_25=2_900.0, ema_99=2_800.0)
        pts, reason = score_pullback_zone(snap, TradeSide.LONG)
        assert pts == SETUP_SCORE_PULLBACK_SHALLOW
        assert "shallow" in reason.lower() or "wait" in reason.lower()

    def test_long_price_below_ema99_extended(self):
        snap = _snapshot(price=2_700.0, ema_7=2_950.0, ema_25=2_900.0, ema_99=2_800.0)
        pts, reason = score_pullback_zone(snap, TradeSide.LONG)
        assert pts == SETUP_SCORE_PULLBACK_EXTENDED
        assert "deep" in reason.lower() or "risk" in reason.lower()

    # ── SHORT scenarios ───────────────────────────────────────────────────────

    def test_short_price_in_ema7_25_zone_optimal(self):
        # Bearish EMA stack: ema_7 < ema_25 < ema_99
        snap = _snapshot(
            price=1_900.0,
            ema_7=1_850.0,
            ema_25=2_000.0,
            ema_99=2_200.0,
            ema_alignment=EMAAlignment.BEARISH,
        )
        pts, reason = score_pullback_zone(snap, TradeSide.SHORT)
        # price >= ema_7 (1900 >= 1850) and price <= ema_25 (1900 <= 2000)
        assert pts == SETUP_SCORE_PULLBACK_OPTIMAL
        assert "optimal" in reason.lower()

    def test_short_price_below_ema7_shallow(self):
        snap = _snapshot(
            price=1_700.0,
            ema_7=1_850.0,
            ema_25=2_000.0,
            ema_99=2_200.0,
            ema_alignment=EMAAlignment.BEARISH,
        )
        pts, reason = score_pullback_zone(snap, TradeSide.SHORT)
        assert pts == SETUP_SCORE_PULLBACK_SHALLOW
        assert "shallow" in reason.lower() or "reclaim" in reason.lower()

    def test_short_price_above_ema99_extended(self):
        snap = _snapshot(
            price=2_400.0,
            ema_7=1_850.0,
            ema_25=2_000.0,
            ema_99=2_200.0,
            ema_alignment=EMAAlignment.BEARISH,
        )
        pts, reason = score_pullback_zone(snap, TradeSide.SHORT)
        assert pts == SETUP_SCORE_PULLBACK_EXTENDED
        assert "deep" in reason.lower() or "risk" in reason.lower()

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_none_snap_returns_near_conservative(self):
        pts, reason = score_pullback_zone(None, TradeSide.LONG)
        assert pts == SETUP_SCORE_PULLBACK_NEAR
        assert "unavailable" in reason.lower() or "conservative" in reason.lower()

    def test_missing_ema_returns_near_conservative(self):
        snap = _snapshot(ema_7=None, ema_25=None, ema_99=None)
        pts, reason = score_pullback_zone(snap, TradeSide.LONG)
        assert pts == SETUP_SCORE_PULLBACK_NEAR
        assert "unavailable" in reason.lower() or "conservative" in reason.lower()


# ══════════════════════════════════════════════════════════════════════════════
# derive_trade_levels
# ══════════════════════════════════════════════════════════════════════════════

class TestDeriveTraceLevels:

    def test_long_levels_logical_ordering(self):
        snap = _snapshot(price=2_950.0, ema_7=2_950.0, ema_25=2_900.0, ema_99=2_800.0)
        lvls = derive_trade_levels(snap, TradeSide.LONG, 2_950.0)
        # stop_loss < entry_zone_low < entry_zone_high < tp1 < tp2 < tp3
        assert lvls["stop_loss"]          < lvls["entry_zone_low"]
        assert lvls["entry_zone_low"]     < lvls["entry_zone_high"]
        assert lvls["entry_zone_high"]    < lvls["tp1"]
        assert lvls["tp1"]                < lvls["tp2"]
        assert lvls["tp2"]                < lvls["tp3"]
        assert lvls["invalidation_level"] < lvls["stop_loss"]

    def test_short_levels_logical_ordering(self):
        snap = _snapshot(
            price=1_900.0,
            ema_7=1_850.0,
            ema_25=2_000.0,
            ema_99=2_200.0,
            ema_alignment=EMAAlignment.BEARISH,
        )
        lvls = derive_trade_levels(snap, TradeSide.SHORT, 1_900.0)
        # stop_loss > entry_zone_high > entry_zone_low > tp1 > tp2 > tp3
        assert lvls["stop_loss"]          > lvls["entry_zone_high"]
        assert lvls["entry_zone_high"]    > lvls["entry_zone_low"]
        assert lvls["entry_zone_low"]     > lvls["tp1"]
        assert lvls["tp1"]                > lvls["tp2"]
        assert lvls["tp2"]                > lvls["tp3"]
        assert lvls["invalidation_level"] > lvls["stop_loss"]

    def test_all_keys_present(self):
        snap = _snapshot()
        lvls = derive_trade_levels(snap, TradeSide.LONG, 3_000.0)
        for key in ("entry_zone_low", "entry_zone_high", "stop_loss",
                    "tp1", "tp2", "tp3", "invalidation_level"):
            assert key in lvls, f"Missing key: {key}"

    def test_none_snap_falls_back_to_price(self):
        lvls = derive_trade_levels(None, TradeSide.LONG, 3_000.0)
        # With all EMAs == price, the levels should still be logically ordered
        assert all(isinstance(v, float) for v in lvls.values())


# ══════════════════════════════════════════════════════════════════════════════
# score_candidate (assembly integration)
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreCandidate:

    def test_fully_bullish_aligned_long_scores_high(self):
        """All signals aligned for a long setup → near-maximum score."""
        candidate = _candidate(side=TradeSide.LONG)
        h1 = _snapshot(
            price=2_920.0, ema_7=2_950.0, ema_25=2_900.0, ema_99=2_800.0,
            ema_alignment=EMAAlignment.BULLISH,
            rsi_state=RSIState.OVERSOLD,
            macd_direction=MACDDirection.BULLISH,
            volume_strength=VolumeStrength.HIGH,
            candle_behavior=CandleBehavior.REJECTION_BULL,
        )
        m15 = _snapshot(
            timeframe=Timeframe.M15,
            price=2_920.0, ema_7=2_950.0, ema_25=2_900.0, ema_99=2_800.0,
            ema_alignment=EMAAlignment.BULLISH,
            rsi_state=RSIState.OVERSOLD,
            macd_direction=MACDDirection.BULLISH,
            volume_strength=VolumeStrength.HIGH,
            candle_behavior=CandleBehavior.REJECTION_BULL,
        )
        setup = score_candidate(candidate, MarketRegime.BULLISH, h1, m15)
        # BTC(25) + H1EMA(20) + M15EMA(10) + RSI(5) + MACD(5) + candle(5) + vol(10) + pullback(20)
        assert setup.score == 100.0
        assert setup.side == TradeSide.LONG
        assert setup.strategy_type == StrategyType.LONG_PULLBACK_BULLISH

    def test_fully_bearish_aligned_short_scores_high(self):
        """All signals aligned for a short setup → near-maximum score."""
        candidate = _candidate(side=TradeSide.SHORT, change=-6.0)
        h1 = _snapshot(
            price=1_900.0,
            ema_7=1_850.0, ema_25=2_000.0, ema_99=2_200.0,
            ema_alignment=EMAAlignment.BEARISH,
            rsi_state=RSIState.OVERBOUGHT,
            macd_direction=MACDDirection.BEARISH,
            volume_strength=VolumeStrength.HIGH,
            candle_behavior=CandleBehavior.REJECTION_BEAR,
        )
        m15 = _snapshot(
            timeframe=Timeframe.M15,
            price=1_900.0,
            ema_7=1_850.0, ema_25=2_000.0, ema_99=2_200.0,
            ema_alignment=EMAAlignment.BEARISH,
            rsi_state=RSIState.OVERBOUGHT,
            macd_direction=MACDDirection.BEARISH,
            volume_strength=VolumeStrength.HIGH,
            candle_behavior=CandleBehavior.REJECTION_BEAR,
        )
        setup = score_candidate(candidate, MarketRegime.BEARISH, h1, m15)
        assert setup.score == 100.0
        assert setup.side == TradeSide.SHORT
        assert setup.strategy_type == StrategyType.SHORT_BOUNCE_BEARISH

    def test_conflicting_btc_regime_penalises_long(self):
        """BEARISH BTC + LONG setup → BTC component scores 0 → reduced total."""
        candidate = _candidate(side=TradeSide.LONG)
        h1  = _snapshot(ema_alignment=EMAAlignment.BULLISH)
        m15 = _snapshot(timeframe=Timeframe.M15, ema_alignment=EMAAlignment.BULLISH)
        aligned_setup   = score_candidate(candidate, MarketRegime.BULLISH, h1, m15)
        conflicted_setup = score_candidate(candidate, MarketRegime.BEARISH, h1, m15)
        assert conflicted_setup.score < aligned_setup.score
        assert conflicted_setup.score == aligned_setup.score - SETUP_SCORE_BTC_REGIME_ALIGNED

    def test_conflicting_btc_regime_penalises_short(self):
        """BULLISH BTC + SHORT setup → BTC component scores 0."""
        candidate = _candidate(side=TradeSide.SHORT)
        h1  = _snapshot(ema_alignment=EMAAlignment.BEARISH)
        m15 = _snapshot(timeframe=Timeframe.M15, ema_alignment=EMAAlignment.BEARISH)
        aligned_setup    = score_candidate(candidate, MarketRegime.BEARISH, h1, m15)
        conflicted_setup = score_candidate(candidate, MarketRegime.BULLISH, h1, m15)
        assert conflicted_setup.score < aligned_setup.score

    def test_weak_trend_scores_low(self):
        """Neutral EMAs, neutral RSI, neutral MACD → weak score even with good BTC regime."""
        candidate = _candidate(side=TradeSide.LONG)
        h1 = _snapshot(
            price=3_100.0,   # above ema_7 → shallow pullback
            ema_alignment=EMAAlignment.NEUTRAL,
            rsi_state=RSIState.NEUTRAL,
            macd_direction=MACDDirection.NEUTRAL,
            volume_strength=VolumeStrength.LOW,
            candle_behavior=CandleBehavior.NEUTRAL,
        )
        m15 = _snapshot(
            timeframe=Timeframe.M15,
            ema_alignment=EMAAlignment.NEUTRAL,
            rsi_state=RSIState.NEUTRAL,
            macd_direction=MACDDirection.NEUTRAL,
            volume_strength=VolumeStrength.LOW,
            candle_behavior=CandleBehavior.NEUTRAL,
        )
        setup = score_candidate(candidate, MarketRegime.BULLISH, h1, m15)
        # BTC(25) + H1EMA neutral(5) + M15EMA neutral(3) + RSI neutral(2) +
        # MACD neutral(0) + candle neutral(1) + vol low(0) + pullback shallow(5)
        assert setup.score == 41.0

    def test_score_bounded_0_to_100(self):
        candidate = _candidate()
        h1  = _snapshot()
        m15 = _snapshot(timeframe=Timeframe.M15)
        setup = score_candidate(candidate, MarketRegime.BULLISH, h1, m15)
        assert 0.0 <= setup.score <= 100.0

    def test_reasons_list_has_eight_entries(self):
        """One reason per scoring component."""
        candidate = _candidate()
        h1  = _snapshot()
        m15 = _snapshot(timeframe=Timeframe.M15)
        setup = score_candidate(candidate, MarketRegime.BULLISH, h1, m15)
        assert len(setup.reasons) == 8

    def test_no_snap_still_returns_scored_setup(self):
        """Graceful degradation with no market data."""
        candidate = _candidate()
        setup = score_candidate(candidate, MarketRegime.UNKNOWN, None, None)
        assert isinstance(setup, ScoredSetup)
        assert 0.0 <= setup.score <= 100.0

    def test_all_trade_levels_present(self):
        candidate = _candidate()
        h1  = _snapshot()
        m15 = _snapshot(timeframe=Timeframe.M15)
        setup = score_candidate(candidate, MarketRegime.BULLISH, h1, m15)
        assert setup.entry_zone_low  > 0.0
        assert setup.entry_zone_high > 0.0
        assert setup.stop_loss       > 0.0
        assert setup.tp1             > 0.0
        assert setup.tp2             > 0.0
        assert setup.tp3             > 0.0
        assert setup.invalidation_level > 0.0


# ══════════════════════════════════════════════════════════════════════════════
# score_all_candidates (integration — mocked async)
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreAllCandidates:

    def _patch_services(
        self,
        btc_resp:  BTCRegimeResponse,
        h1_snap:   Optional[MarketSnapshot],
        m15_snap:  Optional[MarketSnapshot],
    ):
        """Patch both async service calls."""
        return (
            patch(
                "stai.analytics.services.setup_scoring_service.get_btc_regime",
                new_callable=AsyncMock,
                return_value=btc_resp,
            ),
            patch(
                "stai.analytics.services.setup_scoring_service.get_market_snapshot",
                new_callable=AsyncMock,
                side_effect=[h1_snap, m15_snap] * 20,  # enough for all candidates
            ),
        )

    @pytest.mark.asyncio
    async def test_returns_setup_scoring_result(self):
        btc  = _btc_regime_response(MarketRegime.BULLISH)
        h1   = _snapshot(price=2_920.0, ema_7=2_950.0, ema_25=2_900.0, ema_99=2_800.0,
                         ema_alignment=EMAAlignment.BULLISH)
        m15  = _snapshot(timeframe=Timeframe.M15)
        cands = [_candidate()]
        p1, p2 = self._patch_services(btc, h1, m15)
        with p1, p2:
            result = await score_all_candidates(cands, min_score=0.0)
        assert isinstance(result, SetupScoringResult)

    @pytest.mark.asyncio
    async def test_score_threshold_filters_low_scorers(self):
        btc   = _btc_regime_response(MarketRegime.UNKNOWN)
        cands = [_candidate("ETHUSDT"), _candidate("SOLUSDT")]
        p1, p2 = self._patch_services(btc, None, None)
        with p1, p2:
            result_strict = await score_all_candidates(cands, min_score=99.0)
            result_lax    = await score_all_candidates(cands, min_score=0.0)
        assert len(result_strict.setups) == 0
        assert len(result_lax.setups)    == 2

    @pytest.mark.asyncio
    async def test_total_candidates_counts_all(self):
        btc   = _btc_regime_response()
        cands = [_candidate(f"T{i}USDT") for i in range(5)]
        p1, p2 = self._patch_services(btc, None, None)
        with p1, p2:
            result = await score_all_candidates(cands, min_score=0.0)
        assert result.total_candidates == 5

    @pytest.mark.asyncio
    async def test_total_passed_matches_setups_list(self):
        btc   = _btc_regime_response(MarketRegime.BULLISH)
        h1    = _snapshot(price=2_920.0, ema_7=2_950.0, ema_25=2_900.0, ema_99=2_800.0,
                          ema_alignment=EMAAlignment.BULLISH,
                          rsi_state=RSIState.OVERSOLD,
                          macd_direction=MACDDirection.BULLISH,
                          volume_strength=VolumeStrength.HIGH,
                          candle_behavior=CandleBehavior.REJECTION_BULL)
        m15   = _snapshot(timeframe=Timeframe.M15,
                          price=2_920.0, ema_7=2_950.0, ema_25=2_900.0, ema_99=2_800.0,
                          ema_alignment=EMAAlignment.BULLISH,
                          rsi_state=RSIState.OVERSOLD,
                          macd_direction=MACDDirection.BULLISH,
                          volume_strength=VolumeStrength.HIGH,
                          candle_behavior=CandleBehavior.REJECTION_BULL)
        cands = [_candidate()]
        p1, p2 = self._patch_services(btc, h1, m15)
        with p1, p2:
            result = await score_all_candidates(cands, min_score=40.0)
        assert result.total_passed == len(result.setups)

    @pytest.mark.asyncio
    async def test_setups_sorted_highest_score_first(self):
        btc   = _btc_regime_response(MarketRegime.BULLISH)
        # First candidate gets great snaps, second gets None
        h1_good  = _snapshot(price=2_920.0, ema_7=2_950.0, ema_25=2_900.0, ema_99=2_800.0,
                              ema_alignment=EMAAlignment.BULLISH,
                              rsi_state=RSIState.OVERSOLD,
                              macd_direction=MACDDirection.BULLISH,
                              volume_strength=VolumeStrength.HIGH,
                              candle_behavior=CandleBehavior.REJECTION_BULL)
        m15_good = _snapshot(timeframe=Timeframe.M15,
                              price=2_920.0, ema_7=2_950.0, ema_25=2_900.0, ema_99=2_800.0,
                              ema_alignment=EMAAlignment.BULLISH,
                              rsi_state=RSIState.OVERSOLD,
                              macd_direction=MACDDirection.BULLISH,
                              volume_strength=VolumeStrength.HIGH,
                              candle_behavior=CandleBehavior.REJECTION_BULL)
        cands = [_candidate("ETHUSDT"), _candidate("SOLUSDT")]
        with (
            patch(
                "stai.analytics.services.setup_scoring_service.get_btc_regime",
                new_callable=AsyncMock, return_value=btc,
            ),
            patch(
                "stai.analytics.services.setup_scoring_service.get_market_snapshot",
                new_callable=AsyncMock,
                # ETH: h1_good, m15_good; SOL: None, None
                side_effect=[h1_good, m15_good, None, None],
            ),
        ):
            result = await score_all_candidates(cands, min_score=0.0)

        assert result.setups[0].score >= result.setups[1].score

    @pytest.mark.asyncio
    async def test_btc_regime_in_result(self):
        btc = _btc_regime_response(MarketRegime.BEARISH, confidence=0.7)
        p1, p2 = self._patch_services(btc, None, None)
        with p1, p2:
            result = await score_all_candidates([], min_score=0.0)
        assert result.btc_regime     == MarketRegime.BEARISH
        assert result.btc_confidence == 0.7

    @pytest.mark.asyncio
    async def test_empty_candidates_returns_safe_result(self):
        btc = _btc_regime_response()
        p1, p2 = self._patch_services(btc, None, None)
        with p1, p2:
            result = await score_all_candidates([], min_score=40.0)
        assert result.total_candidates == 0
        assert result.total_passed     == 0
        assert result.setups           == []

    @pytest.mark.asyncio
    async def test_btc_regime_failure_uses_unknown(self):
        """If BTC regime fetch fails, scoring continues with UNKNOWN regime."""
        h1  = _snapshot()
        m15 = _snapshot(timeframe=Timeframe.M15)
        cands = [_candidate()]
        with (
            patch(
                "stai.analytics.services.setup_scoring_service.get_btc_regime",
                new_callable=AsyncMock,
                side_effect=RuntimeError("Binance down"),
            ),
            patch(
                "stai.analytics.services.setup_scoring_service.get_market_snapshot",
                new_callable=AsyncMock,
                side_effect=[h1, m15],
            ),
        ):
            result = await score_all_candidates(cands, min_score=0.0)
        assert result.btc_regime == MarketRegime.UNKNOWN
        assert len(result.setups) == 1


# ══════════════════════════════════════════════════════════════════════════════
# Score threshold behaviour — explicit boundary tests
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreThresholdBehavior:

    def _score_with_regime(self, regime: MarketRegime, side: TradeSide) -> float:
        """Quick score using all-neutral 15M signals for comparability."""
        candidate = _candidate(side=side)
        h1 = _snapshot(
            price=2_920.0,
            ema_alignment=EMAAlignment.NEUTRAL,
            rsi_state=RSIState.NEUTRAL,
            macd_direction=MACDDirection.NEUTRAL,
            volume_strength=VolumeStrength.NORMAL,
            candle_behavior=CandleBehavior.NEUTRAL,
        )
        m15 = _snapshot(
            timeframe=Timeframe.M15,
            ema_alignment=EMAAlignment.NEUTRAL,
            rsi_state=RSIState.NEUTRAL,
            macd_direction=MACDDirection.NEUTRAL,
            volume_strength=VolumeStrength.NORMAL,
            candle_behavior=CandleBehavior.NEUTRAL,
        )
        setup = score_candidate(candidate, regime, h1, m15)
        return setup.score

    def test_fully_aligned_scores_above_default_threshold(self):
        candidate = _candidate(side=TradeSide.LONG)
        h1 = _snapshot(
            price=2_920.0, ema_7=2_950.0, ema_25=2_900.0, ema_99=2_800.0,
            ema_alignment=EMAAlignment.BULLISH,
            rsi_state=RSIState.OVERSOLD,
            macd_direction=MACDDirection.BULLISH,
            volume_strength=VolumeStrength.HIGH,
            candle_behavior=CandleBehavior.REJECTION_BULL,
        )
        m15 = _snapshot(
            timeframe=Timeframe.M15,
            ema_alignment=EMAAlignment.BULLISH,
            rsi_state=RSIState.OVERSOLD,
            macd_direction=MACDDirection.BULLISH,
            volume_strength=VolumeStrength.HIGH,
            candle_behavior=CandleBehavior.REJECTION_BULL,
        )
        setup = score_candidate(candidate, MarketRegime.BULLISH, h1, m15)
        assert setup.score >= 40.0

    def test_conflicted_btc_neutral_signals_may_fail_threshold(self):
        score = self._score_with_regime(MarketRegime.BEARISH, TradeSide.LONG)
        # BTC conflict (0) + H1 neutral (5) + M15 neutral (3) + RSI neutral (2) +
        # MACD neutral (0) + candle neutral (1) + vol normal (5) + pullback near (12)
        # = 28 → below default threshold of 40
        assert score < 40.0

    def test_score_increases_monotonically_with_alignment(self):
        """Adding positive signals must never decrease the score."""
        candidate = _candidate(side=TradeSide.LONG)
        h1_base = _snapshot(
            price=2_920.0,
            ema_alignment=EMAAlignment.BULLISH,
            rsi_state=RSIState.NEUTRAL,
            macd_direction=MACDDirection.NEUTRAL,
            volume_strength=VolumeStrength.NORMAL,
            candle_behavior=CandleBehavior.NEUTRAL,
        )
        m15_base = _snapshot(
            timeframe=Timeframe.M15,
            ema_alignment=EMAAlignment.NEUTRAL,
            rsi_state=RSIState.NEUTRAL,
            macd_direction=MACDDirection.NEUTRAL,
        )
        h1_better = _snapshot(
            price=2_920.0,
            ema_alignment=EMAAlignment.BULLISH,
            rsi_state=RSIState.OVERSOLD,    # improved
            macd_direction=MACDDirection.BULLISH,  # improved
            volume_strength=VolumeStrength.HIGH,   # improved
            candle_behavior=CandleBehavior.REJECTION_BULL,  # improved
        )
        base_score   = score_candidate(candidate, MarketRegime.BULLISH, h1_base,   m15_base).score
        better_score = score_candidate(candidate, MarketRegime.BULLISH, h1_better, m15_base).score
        assert better_score >= base_score
