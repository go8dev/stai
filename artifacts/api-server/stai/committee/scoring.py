"""Adapt captured OKX candles to unchanged indicator and setup scoring functions."""

from __future__ import annotations

from stai.analytics.core.constants import CandleBehavior, MarketRegime, Timeframe, TradeSide
from stai.analytics.schemas.market_snapshot import MarketSnapshot
from stai.analytics.schemas.scanner import ScannerCandidate
from stai.analytics.services.btc_regime_service import (
    REGIME_WEIGHT_H1,
    REGIME_WEIGHT_M15,
    _classify_composite,
    _score_snapshot,
)
from stai.analytics.services.setup_scoring_service import score_candidate
from stai.analytics.utils.indicators import (
    classify_macd,
    classify_rsi,
    classify_volume,
    detect_rejection_candle,
    detect_strong_momentum,
    detect_trend,
)
from stai.marketdata.indicators import indicator_snapshot, safe_number
from stai.marketdata.schemas import MarketScannerRow


def snapshot(row: MarketScannerRow, timeframe: Timeframe) -> MarketSnapshot | None:
    """Shape adapter only; classifications/calculations stay in ported analytics."""
    candles = row.candles if timeframe == Timeframe.H1 else row.candles_15m
    result = indicator_snapshot(candles)
    if result is None:
        return None
    last, _ = result
    return MarketSnapshot(
        symbol=row.symbol,
        timeframe=timeframe,
        current_price=float(last["close"]),
        volume=float(last["volume"]),
        **{
            key: safe_number(last.get(key))
            for key in [
                "ema_7",
                "ema_25",
                "ema_99",
                "rsi",
                "macd",
                "macd_signal",
                "macd_hist",
                "avg_volume",
                "volume_ratio",
                "body",
                "upper_wick",
                "lower_wick",
                "body_pct",
            ]
        },
        ema_alignment=detect_trend(last),
        rsi_state=classify_rsi(safe_number(last.get("rsi"))),
        macd_direction=classify_macd(safe_number(last.get("macd_hist"))),
        volume_strength=classify_volume(safe_number(last.get("volume_ratio"))),
        candle_behavior=(
            detect_rejection_candle(last) or detect_strong_momentum(last) or CandleBehavior.NEUTRAL
        ),
        computed_at=row.observed_at.isoformat(),
    )


def setup_scores(
    row: MarketScannerRow, btc_row: MarketScannerRow | None = None
) -> dict[str, object]:
    """Full reused score with captured BTC regime; unavailable BTC earns no points."""
    if row.status != "fresh" or row.last_price is None:
        return {"status": "unavailable", "reason": "Fresh market data required"}
    h1, m15 = snapshot(row, Timeframe.H1), snapshot(row, Timeframe.M15)
    if h1 is None or m15 is None:
        return {"status": "unavailable", "reason": "Indicator snapshots missing"}
    regime = MarketRegime.UNKNOWN
    btc_evidence: dict[str, object] = {"status": "unavailable", "regime": "unknown"}
    if btc_row is not None and btc_row.status == "fresh":
        btc_h1, btc_m15 = snapshot(btc_row, Timeframe.H1), snapshot(btc_row, Timeframe.M15)
        if btc_h1 is not None and btc_m15 is not None:
            h1_score, h1_reasons = _score_snapshot(btc_h1)
            m15_score, m15_reasons = _score_snapshot(btc_m15)
            composite = round(h1_score * REGIME_WEIGHT_H1 + m15_score * REGIME_WEIGHT_M15, 4)
            regime, confidence, reasons = _classify_composite(composite, h1_score, m15_score)
            btc_evidence = {
                "status": "fresh",
                "regime": regime.value,
                "confidence": confidence,
                "compositeScore": composite,
                "reasons": h1_reasons + m15_reasons + reasons,
                "observedAt": btc_row.observed_at.isoformat(),
                "marketType": btc_row.market_type,
                "h1Snapshot": btc_h1.model_dump(mode="json"),
                "m15Snapshot": btc_m15.model_dump(mode="json"),
            }
    results = {}
    for side in (TradeSide.LONG, TradeSide.SHORT):
        if row.market_type == "spot" and side == TradeSide.SHORT:
            continue
        candidate = ScannerCandidate(
            symbol=row.symbol,
            last_price=float(row.last_price),
            change_percent_24h=float(row.change_pct_24h or 0),
            quote_volume=float(row.volume_24h or 0),
            candidate_side=side,
            scan_reasons=["Observed, not an approved setup"],
            scanned_at=row.observed_at.isoformat(),
        )
        results[side.value] = score_candidate(candidate, regime, h1, m15).model_dump(mode="json")
    return {
        "status": "available",
        "scores": results,
        "h1Snapshot": h1.model_dump(mode="json"),
        "m15Snapshot": m15.model_dump(mode="json"),
        "btcRegime": btc_evidence,
        "note": "Deterministic screening only. The 70/100 threshold is selected, with independent "
        "freshness, BTC-regime, 1-hour trend, 15-minute confirmation, pullback, and market-quality "
        "gates. It does not initiate a paid committee run.",
    }
