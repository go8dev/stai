"""
Tests for the BTC multi-timeframe regime classifier.

Strategy: build realistic MarketSnapshot objects, inject them via mocking,
and assert that the scoring, regime labelling, confidence, and reasons
all behave as documented.

No live Binance calls are made.
"""
from __future__ import annotations

from typing import Optional
from unittest.mock import AsyncMock, patch

import pytest

from app.core.constants import (
    REGIME_AGREE_BONUS,
    REGIME_BEARISH_THRESHOLD,
    REGIME_BULLISH_THRESHOLD,
    REGIME_MAX_RAW_SCORE,
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
    VolumeStrength,
)
from app.schemas.btc_regime import BTCRegimeResponse, SnapshotSummary
from app.schemas.market_snapshot import MarketSnapshot
from app.services.btc_regime_service import (
    _classify_composite,
    _score_snapshot,
    _to_summary,
    get_btc_regime_multi_tf,
)


# ── Factories ─────────────────────────────────────────────────────────────────

def _snap(
    timeframe:       Timeframe     = Timeframe.H1,
    price:           float         = 50_000.0,
    ema_alignment:   EMAAlignment  = EMAAlignment.NEUTRAL,
    rsi:             float         = 50.0,
    rsi_state:       RSIState      = RSIState.NEUTRAL,
    macd_hist:       float         = 0.0,
    macd_direction:  MACDDirection = MACDDirection.NEUTRAL,
    volume_strength: VolumeStrength= VolumeStrength.NORMAL,
    candle_behavior: CandleBehavior= CandleBehavior.NEUTRAL,
) -> MarketSnapshot:
    """Factory that returns a fully-formed MarketSnapshot with sensible defaults."""
    return MarketSnapshot(
        symbol          = "BTCUSDT",
        timeframe       = timeframe,
        current_price   = price,
        ema_7           = price * 1.001,
        ema_25          = price * 1.000,
        ema_99          = price * 0.999,
        ema_alignment   = ema_alignment,
        rsi             = rsi,
        rsi_state       = rsi_state,
        macd            = macd_hist,
        macd_signal     = 0.0,
        macd_hist       = macd_hist,
        macd_direction  = macd_direction,
        volume          = 1000.0,
        avg_volume      = 1000.0,
        volume_ratio    = 1.0,
        volume_strength = volume_strength,
        body            = price * 0.01,
        upper_wick      = price * 0.002,
        lower_wick      = price * 0.002,
        body_pct        = 75.0,
        candle_behavior = candle_behavior,
        computed_at     = "2026-01-01T00:00:00+00:00",
    )


# ── _score_snapshot ───────────────────────────────────────────────────────────

class TestScoreSnapshot:

    def test_all_neutral_gives_zero(self) -> None:
        snap = _snap()
        score, reasons = _score_snapshot(snap)
        assert score == 0.0

    def test_bullish_ema_adds_positive(self) -> None:
        snap = _snap(ema_alignment=EMAAlignment.BULLISH)
        score, _ = _score_snapshot(snap)
        assert score == REGIME_SCORE_EMA_STRONG

    def test_bearish_ema_subtracts(self) -> None:
        snap = _snap(ema_alignment=EMAAlignment.BEARISH)
        score, _ = _score_snapshot(snap)
        assert score == -REGIME_SCORE_EMA_STRONG

    def test_bullish_macd_adds(self) -> None:
        snap = _snap(macd_direction=MACDDirection.BULLISH)
        score, _ = _score_snapshot(snap)
        assert score == REGIME_SCORE_MACD

    def test_bearish_macd_subtracts(self) -> None:
        snap = _snap(macd_direction=MACDDirection.BEARISH)
        score, _ = _score_snapshot(snap)
        assert score == -REGIME_SCORE_MACD

    def test_overbought_rsi_adds(self) -> None:
        snap = _snap(rsi=75.0, rsi_state=RSIState.OVERBOUGHT)
        score, _ = _score_snapshot(snap)
        assert score == REGIME_SCORE_RSI

    def test_oversold_rsi_subtracts(self) -> None:
        snap = _snap(rsi=25.0, rsi_state=RSIState.OVERSOLD)
        score, _ = _score_snapshot(snap)
        assert score == -REGIME_SCORE_RSI

    def test_neutral_rsi_zero(self) -> None:
        snap = _snap(rsi=50.0, rsi_state=RSIState.NEUTRAL)
        score, _ = _score_snapshot(snap)
        assert score == 0.0

    def test_strong_bull_candle_adds(self) -> None:
        snap = _snap(candle_behavior=CandleBehavior.STRONG_BULL)
        score, _ = _score_snapshot(snap)
        assert score == REGIME_SCORE_CANDLE_STRONG

    def test_strong_bear_candle_subtracts(self) -> None:
        snap = _snap(candle_behavior=CandleBehavior.STRONG_BEAR)
        score, _ = _score_snapshot(snap)
        assert score == -REGIME_SCORE_CANDLE_STRONG

    def test_full_bullish_snapshot_max_score(self) -> None:
        """All bullish signals together should yield the theoretical max score."""
        snap = _snap(
            ema_alignment   = EMAAlignment.BULLISH,
            rsi_state       = RSIState.OVERBOUGHT,
            macd_direction  = MACDDirection.BULLISH,
            candle_behavior = CandleBehavior.STRONG_BULL,
        )
        score, reasons = _score_snapshot(snap)
        expected = (
            REGIME_SCORE_EMA_STRONG
            + REGIME_SCORE_RSI
            + REGIME_SCORE_MACD
            + REGIME_SCORE_CANDLE_STRONG
        )
        assert score == pytest.approx(expected)
        assert len(reasons) >= 4  # at least one reason per contributing signal

    def test_full_bearish_snapshot_min_score(self) -> None:
        snap = _snap(
            ema_alignment   = EMAAlignment.BEARISH,
            rsi_state       = RSIState.OVERSOLD,
            macd_direction  = MACDDirection.BEARISH,
            candle_behavior = CandleBehavior.STRONG_BEAR,
        )
        score, _ = _score_snapshot(snap)
        assert score < 0
        assert score == pytest.approx(
            -(REGIME_SCORE_EMA_STRONG + REGIME_SCORE_RSI + REGIME_SCORE_MACD + REGIME_SCORE_CANDLE_STRONG)
        )

    def test_reasons_contain_timeframe_label(self) -> None:
        snap = _snap(timeframe=Timeframe.M15, ema_alignment=EMAAlignment.BULLISH)
        _, reasons = _score_snapshot(snap)
        assert any("15M" in r for r in reasons)

    def test_rejection_bull_adds_half(self) -> None:
        from app.core.constants import REGIME_SCORE_CANDLE_REJECT
        snap = _snap(candle_behavior=CandleBehavior.REJECTION_BULL)
        score, _ = _score_snapshot(snap)
        assert score == pytest.approx(REGIME_SCORE_CANDLE_REJECT)

    def test_rejection_bear_subtracts_half(self) -> None:
        from app.core.constants import REGIME_SCORE_CANDLE_REJECT
        snap = _snap(candle_behavior=CandleBehavior.REJECTION_BEAR)
        score, _ = _score_snapshot(snap)
        assert score == pytest.approx(-REGIME_SCORE_CANDLE_REJECT)


# ── _classify_composite ───────────────────────────────────────────────────────

class TestClassifyComposite:

    def test_high_positive_score_bullish(self) -> None:
        regime, confidence, _ = _classify_composite(3.5, 3.5, 3.5)
        assert regime == MarketRegime.BULLISH

    def test_high_negative_score_bearish(self) -> None:
        regime, confidence, _ = _classify_composite(-3.5, -3.5, -3.5)
        assert regime == MarketRegime.BEARISH

    def test_threshold_edge_bullish(self) -> None:
        regime, _, _ = _classify_composite(REGIME_BULLISH_THRESHOLD, 3.0, 3.0)
        assert regime == MarketRegime.BULLISH

    def test_threshold_edge_bearish(self) -> None:
        regime, _, _ = _classify_composite(REGIME_BEARISH_THRESHOLD, -3.0, -3.0)
        assert regime == MarketRegime.BEARISH

    def test_zero_score_ranging(self) -> None:
        regime, _, _ = _classify_composite(0.0, 0.0, 0.0)
        assert regime == MarketRegime.RANGING

    def test_mixed_tf_signals_volatile(self) -> None:
        """When one TF is strongly directional but composite is indecisive → VOLATILE."""
        regime, _, _ = _classify_composite(0.5, REGIME_BULLISH_THRESHOLD, -3.0)
        assert regime == MarketRegime.VOLATILE

    def test_confidence_zero_for_zero_score(self) -> None:
        _, confidence, _ = _classify_composite(0.0, 0.0, 0.0)
        assert confidence == 0.0

    def test_confidence_max_for_max_score(self) -> None:
        _, confidence, _ = _classify_composite(REGIME_MAX_RAW_SCORE, 5.0, 5.0)
        assert confidence == pytest.approx(min(1.0, 1.0 + REGIME_AGREE_BONUS))

    def test_confidence_bonus_when_both_tfs_agree(self) -> None:
        """Both TFs bullish → confidence is base + AGREE_BONUS."""
        _, base_conf,   _ = _classify_composite(3.0, 0.0,  0.0)   # disagree (h1=0, m15=0)
        _, bonus_conf,  _ = _classify_composite(3.0, 3.0,  3.0)   # agree
        assert bonus_conf > base_conf

    def test_confidence_capped_at_one(self) -> None:
        _, confidence, _ = _classify_composite(5.0, 5.0, 5.0)
        assert confidence <= 1.0

    def test_reasons_non_empty(self) -> None:
        _, _, reasons = _classify_composite(3.0, 3.0, 3.0)
        assert len(reasons) >= 1

    def test_agreement_reason_present_when_aligned(self) -> None:
        _, _, reasons = _classify_composite(3.0, 3.0, 2.0)
        assert any("aligned" in r.lower() or "both" in r.lower() for r in reasons)

    def test_disagreement_reason_when_mixed(self) -> None:
        _, _, reasons = _classify_composite(0.5, 3.0, -3.0)
        assert any("mixed" in r.lower() or "caution" in r.lower() for r in reasons)


# ── _to_summary ───────────────────────────────────────────────────────────────

class TestToSummary:

    def test_summary_fields_match_snapshot(self) -> None:
        snap = _snap(timeframe=Timeframe.H1, price=48_000.0)
        summary = _to_summary(snap, tf_score=2.5)
        assert summary.timeframe     == Timeframe.H1
        assert summary.current_price == 48_000.0
        assert summary.tf_score      == pytest.approx(2.5)

    def test_summary_classification_fields_pass_through(self) -> None:
        snap = _snap(ema_alignment=EMAAlignment.BULLISH, rsi_state=RSIState.OVERBOUGHT)
        summary = _to_summary(snap, tf_score=3.0)
        assert summary.ema_alignment == EMAAlignment.BULLISH
        assert summary.rsi_state     == RSIState.OVERBOUGHT

    def test_tf_score_rounded(self) -> None:
        summary = _to_summary(_snap(), tf_score=1.23456789)
        assert summary.tf_score == round(1.23456789, 4)


# ── get_btc_regime_multi_tf (integration via mocks) ───────────────────────────

class TestGetBtcRegimeMultiTf:
    """
    Patches market_service.get_market_snapshot so no real Binance call is made.
    The mock returns pre-built MarketSnapshots.
    """

    def _bullish_snap(self, tf: Timeframe) -> MarketSnapshot:
        return _snap(
            timeframe       = tf,
            ema_alignment   = EMAAlignment.BULLISH,
            rsi_state       = RSIState.OVERBOUGHT,
            macd_direction  = MACDDirection.BULLISH,
            candle_behavior = CandleBehavior.STRONG_BULL,
        )

    def _bearish_snap(self, tf: Timeframe) -> MarketSnapshot:
        return _snap(
            timeframe       = tf,
            ema_alignment   = EMAAlignment.BEARISH,
            rsi_state       = RSIState.OVERSOLD,
            macd_direction  = MACDDirection.BEARISH,
            candle_behavior = CandleBehavior.STRONG_BEAR,
        )

    def _neutral_snap(self, tf: Timeframe) -> MarketSnapshot:
        return _snap(timeframe=tf)

    async def _run(
        self,
        h1: Optional[MarketSnapshot],
        m15: Optional[MarketSnapshot],
    ) -> BTCRegimeResponse:
        with patch(
            "app.services.btc_regime_service.get_market_snapshot",
            new_callable=AsyncMock,
            side_effect=[h1, m15],
        ):
            return await get_btc_regime_multi_tf()

    @pytest.mark.asyncio
    async def test_both_bullish_returns_bullish_regime(self) -> None:
        result = await self._run(
            self._bullish_snap(Timeframe.H1),
            self._bullish_snap(Timeframe.M15),
        )
        assert result.regime == MarketRegime.BULLISH

    @pytest.mark.asyncio
    async def test_both_bearish_returns_bearish_regime(self) -> None:
        result = await self._run(
            self._bearish_snap(Timeframe.H1),
            self._bearish_snap(Timeframe.M15),
        )
        assert result.regime == MarketRegime.BEARISH

    @pytest.mark.asyncio
    async def test_both_neutral_returns_ranging(self) -> None:
        result = await self._run(
            self._neutral_snap(Timeframe.H1),
            self._neutral_snap(Timeframe.M15),
        )
        assert result.regime == MarketRegime.RANGING

    @pytest.mark.asyncio
    async def test_composite_score_computed_correctly(self) -> None:
        h1  = self._bullish_snap(Timeframe.H1)
        m15 = self._neutral_snap(Timeframe.M15)
        result = await self._run(h1, m15)
        h1_score  = REGIME_SCORE_EMA_STRONG + REGIME_SCORE_RSI + REGIME_SCORE_MACD + REGIME_SCORE_CANDLE_STRONG
        m15_score = 0.0
        expected  = round(h1_score * REGIME_WEIGHT_H1 + m15_score * REGIME_WEIGHT_M15, 4)
        assert result.composite_score == pytest.approx(expected)

    @pytest.mark.asyncio
    async def test_both_agree_increases_confidence(self) -> None:
        """Aligned timeframes should produce higher confidence than a single TF."""
        both_agree = await self._run(
            self._bullish_snap(Timeframe.H1),
            self._bullish_snap(Timeframe.M15),
        )
        only_h1 = await self._run(
            self._bullish_snap(Timeframe.H1),
            self._neutral_snap(Timeframe.M15),
        )
        assert both_agree.confidence > only_h1.confidence

    @pytest.mark.asyncio
    async def test_confidence_in_valid_range(self) -> None:
        result = await self._run(
            self._bullish_snap(Timeframe.H1),
            self._bullish_snap(Timeframe.M15),
        )
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_summaries_populated(self) -> None:
        result = await self._run(
            self._bullish_snap(Timeframe.H1),
            self._bullish_snap(Timeframe.M15),
        )
        assert result.h1_summary  is not None
        assert result.m15_summary is not None
        assert result.h1_summary.timeframe  == Timeframe.H1
        assert result.m15_summary.timeframe == Timeframe.M15

    @pytest.mark.asyncio
    async def test_reasons_non_empty(self) -> None:
        result = await self._run(
            self._bullish_snap(Timeframe.H1),
            self._neutral_snap(Timeframe.M15),
        )
        assert len(result.reasons) >= 2

    @pytest.mark.asyncio
    async def test_updated_at_is_iso_string(self) -> None:
        result = await self._run(
            self._neutral_snap(Timeframe.H1),
            self._neutral_snap(Timeframe.M15),
        )
        assert "T" in result.updated_at and "+" in result.updated_at or "Z" in result.updated_at

    @pytest.mark.asyncio
    async def test_one_tf_none_returns_partial_result(self) -> None:
        """Service degrades gracefully when one TF is unavailable."""
        result = await self._run(
            self._bullish_snap(Timeframe.H1),
            None,  # 15M unavailable
        )
        assert result.regime != MarketRegime.UNKNOWN
        assert result.h1_summary  is not None
        assert result.m15_summary is None

    @pytest.mark.asyncio
    async def test_both_none_returns_unknown_regime(self) -> None:
        result = await self._run(None, None)
        assert result.regime     == MarketRegime.UNKNOWN
        assert result.confidence == 0.0
        assert result.h1_summary  is None
        assert result.m15_summary is None


# ── BTCRegimeResponse schema validation ───────────────────────────────────────

class TestBTCRegimeResponseSchema:

    def test_confidence_rejects_out_of_range(self) -> None:
        import pytest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            BTCRegimeResponse(
                regime          = MarketRegime.BULLISH,
                confidence      = 1.5,          # invalid
                composite_score = 3.0,
                reasons         = [],
                updated_at      = "2026-01-01T00:00:00+00:00",
            )

    def test_valid_response_roundtrips_json(self) -> None:
        resp = BTCRegimeResponse(
            regime          = MarketRegime.RANGING,
            confidence      = 0.42,
            composite_score = 0.8,
            reasons         = ["test reason"],
            updated_at      = "2026-01-01T00:00:00+00:00",
        )
        data = resp.model_dump()
        assert data["regime"]          == "ranging"
        assert data["confidence"]      == pytest.approx(0.42)
        assert data["composite_score"] == pytest.approx(0.8)
        assert data["reasons"]         == ["test reason"]
