"""
Market service — BTC regime detection and full indicator snapshots.

Responsibilities:
  - Classify the current BTC market regime using live market data.
  - Build a MarketSnapshot for any symbol/timeframe by fetching candles and
    running the full indicator engine.
  - Abstract all data access away from routes; routes never touch the
    market-data provider.
  - Falls back gracefully when market data is unavailable.

Ported from Smart Trader. Its two Binance client calls now go through STAI's
market-data provider interface (stai.marketdata.provider).
"""
from datetime import datetime, timezone
from typing import Optional

import numpy as np

from stai.analytics.core.constants import (
    DEFAULT_CANDLE_LIMIT,
    CandleBehavior,
    MarketRegime,
    Timeframe,
)
from stai.core.logging import StructuredLogger
from stai.analytics.schemas.market_data import Ticker
from stai.analytics.schemas.market import MarketRegimeResponse
from stai.analytics.schemas.market_snapshot import MarketSnapshot
from stai.analytics.utils.indicators import (
    classify_macd,
    classify_rsi,
    classify_volume,
    compute_indicators,
    detect_rejection_candle,
    detect_strong_momentum,
    detect_trend,
)
from stai.marketdata.provider import get_market_data_provider

logger = StructuredLogger(__name__)

BTC_SYMBOL = "BTCUSDT"

# Regime thresholds (tunable via constants or config later)
BULLISH_CHANGE_PCT    = 3.0
BEARISH_CHANGE_PCT    = -3.0
VOLATILE_HIGH_LOW_PCT = 5.0   # high-low range as % of price


# ── BTC regime ────────────────────────────────────────────────────────────────

def _classify_regime(ticker: Ticker) -> MarketRegime:
    """
    Derive a market regime label from 24h BTC ticker stats.

    Rules (deterministic — no AI):
      Volatile  : (high − low) / price >= VOLATILE_HIGH_LOW_PCT %
      Bullish   : 24h change  >= BULLISH_CHANGE_PCT %
      Bearish   : 24h change  <= BEARISH_CHANGE_PCT %
      Sideways  : everything else
    """
    high_low_range_pct = (
        (ticker.high - ticker.low) / ticker.price * 100
    ) if ticker.price else 0.0

    if high_low_range_pct >= VOLATILE_HIGH_LOW_PCT:
        return MarketRegime.VOLATILE
    if ticker.change_pct_24h >= BULLISH_CHANGE_PCT:
        return MarketRegime.BULLISH
    if ticker.change_pct_24h <= BEARISH_CHANGE_PCT:
        return MarketRegime.BEARISH
    return MarketRegime.SIDEWAYS


def _regime_trend_label(regime: MarketRegime, change_pct: float) -> str:
    labels = {
        MarketRegime.BULLISH:  f"Uptrend +{change_pct:.2f}%",
        MarketRegime.BEARISH:  f"Downtrend {change_pct:.2f}%",
        MarketRegime.SIDEWAYS: f"Range-bound {change_pct:+.2f}%",
        MarketRegime.VOLATILE: f"High volatility {change_pct:+.2f}%",
        MarketRegime.UNKNOWN:  "Awaiting data",
    }
    return labels.get(regime, "Unknown")


async def get_btc_regime() -> MarketRegimeResponse:
    """
    Fetch live BTC 24h ticker and classify the market regime.
    Falls back to UNKNOWN if the ticker is unavailable.
    """
    ticker: Optional[Ticker] = await get_market_data_provider().get_ticker(BTC_SYMBOL)

    if ticker is None:
        logger.warning("BTC ticker unavailable — returning UNKNOWN regime")
        return MarketRegimeResponse(
            regime=MarketRegime.UNKNOWN,
            btc_price=0.0,
            btc_change_24h=0.0,
            trend="Awaiting data",
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    regime = _classify_regime(ticker)
    trend  = _regime_trend_label(regime, ticker.change_pct_24h)

    logger.info(
        "BTC regime classified",
        regime=regime.value,
        price=ticker.price,
        change_pct=ticker.change_pct_24h,
    )

    return MarketRegimeResponse(
        regime=regime,
        btc_price=ticker.price,
        btc_change_24h=ticker.change_pct_24h,
        trend=trend,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


# ── Market snapshot ───────────────────────────────────────────────────────────

def _safe(val: object) -> Optional[float]:
    """Return None if val is NaN/None, else float(val)."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if np.isnan(f) else f
    except (TypeError, ValueError):
        return None


async def get_market_snapshot(
    symbol: str,
    timeframe: Timeframe = Timeframe.H1,
    limit: int = DEFAULT_CANDLE_LIMIT,
) -> Optional[MarketSnapshot]:
    """
    Fetch OHLCV candles from the market-data provider for *symbol* / *timeframe*,
    run the full indicator engine, and return a structured MarketSnapshot for the
    latest candle.

    Returns None if candles cannot be fetched (e.g. provider unreachable).

    Flow
    ----
    1. provider.get_candles()       → List[Candle]
    2. compute_indicators()         → pd.DataFrame with EMA / RSI / MACD / volume / candle cols
    3. Classify last row            → enum values
    4. Assemble and return          → MarketSnapshot
    """
    klines = await get_market_data_provider().get_candles(symbol, timeframe.value, limit=limit)

    if not klines:
        logger.warning(
            "No klines returned — cannot build snapshot",
            symbol=symbol,
            timeframe=timeframe.value,
        )
        return None

    df  = compute_indicators(klines)
    row = df.iloc[-1]

    # ── Classification ───────────────────────────────────────────────────────
    ema_alignment    = detect_trend(row)
    rsi_state        = classify_rsi(_safe(row.get("rsi")))
    macd_direction   = classify_macd(_safe(row.get("macd_hist")))
    volume_strength  = classify_volume(_safe(row.get("volume_ratio")))

    # Rejection takes priority; then momentum; then neutral
    candle_behavior: CandleBehavior = (
        detect_rejection_candle(row)
        or detect_strong_momentum(row)
        or CandleBehavior.NEUTRAL
    )

    snapshot = MarketSnapshot(
        symbol        = symbol,
        timeframe     = timeframe,
        current_price = float(row["close"]),
        ema_7         = _safe(row.get("ema_7")),
        ema_25        = _safe(row.get("ema_25")),
        ema_99        = _safe(row.get("ema_99")),
        ema_alignment = ema_alignment,
        rsi           = _safe(row.get("rsi")),
        rsi_state     = rsi_state,
        macd          = _safe(row.get("macd")),
        macd_signal   = _safe(row.get("macd_signal")),
        macd_hist     = _safe(row.get("macd_hist")),
        macd_direction= macd_direction,
        volume        = float(row["volume"]),
        avg_volume    = _safe(row.get("avg_volume")),
        volume_ratio  = _safe(row.get("volume_ratio")),
        volume_strength = volume_strength,
        body          = _safe(row.get("body")),
        upper_wick    = _safe(row.get("upper_wick")),
        lower_wick    = _safe(row.get("lower_wick")),
        body_pct      = _safe(row.get("body_pct")),
        candle_behavior = candle_behavior,
        computed_at   = datetime.now(timezone.utc).isoformat(),
    )

    logger.info(
        "Market snapshot computed",
        symbol        = symbol,
        timeframe     = timeframe.value,
        price         = snapshot.current_price,
        ema_alignment = ema_alignment.value,
        rsi           = snapshot.rsi,
        rsi_state     = rsi_state.value,
        macd_direction= macd_direction.value,
        candle        = candle_behavior.value,
    )

    return snapshot
