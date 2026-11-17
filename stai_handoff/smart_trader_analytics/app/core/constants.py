"""
Shared enums and constants used across all modules.
Import from here — never redeclare the same enum in multiple files.
"""
from enum import Enum


class TradeSide(str, Enum):
    """Direction of a futures trade."""
    LONG = "long"
    SHORT = "short"


class SetupDecision(str, Enum):
    """AI or manual decision on a trade setup."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SetupStatus(str, Enum):
    """Status of a setup in the Phase 9 approval workflow."""
    PENDING_USER_APPROVAL = "pending_user_approval"
    USER_APPROVED         = "user_approved"
    REJECTED              = "rejected"
    MONITORING            = "monitoring"
    EXECUTED              = "executed"
    EXPIRED               = "expired"


class AIDecision(str, Enum):
    """AI confirmation layer verdict on a scored setup."""
    ENTER  = "enter"   # conditions met — proceed to execution
    WAIT   = "wait"    # setup valid but timing is not ideal
    REJECT = "reject"  # setup fundamentally flawed or too risky


class AIReviewStatus(str, Enum):
    """Whether the AI review completed successfully."""
    REVIEWED = "reviewed"   # AI returned a parseable, valid response
    FAILED   = "failed"     # AI returned malformed or invalid JSON
    SKIPPED  = "skipped"    # AI not configured or setup below threshold


class TradeStatus(str, Enum):
    """Lifecycle state of an executed trade."""
    PENDING = "pending"           # awaiting approval
    OPEN = "open"                 # live position on exchange
    PARTIAL_CLOSE = "partial_close"  # partially exited
    CLOSED = "closed"             # position fully exited (TP / SL / manual)
    CANCELLED = "cancelled"       # rejected before execution
    ERROR = "error"               # execution failed


class CloseReason(str, Enum):
    """Why a trade position was closed."""
    STOP_LOSS_HIT        = "stop_loss_hit"
    TAKE_PROFIT_HIT      = "take_profit_hit"
    MANUAL_CLOSE         = "manual_close"
    INVALIDATION_TRIGGER = "invalidation_trigger"
    TRADE_EXPIRY         = "trade_expiry"


class MarketRegime(str, Enum):
    """BTC macro market regime label."""
    BULLISH  = "bullish"
    BEARISH  = "bearish"
    RANGING  = "ranging"    # low-directional, contained price action
    SIDEWAYS = "sideways"   # legacy alias — prefer RANGING in new code
    VOLATILE = "volatile"
    UNKNOWN  = "unknown"


class StrategyType(str, Enum):
    """Registered trading strategy identifiers."""
    RSI_REVERSAL              = "rsi_reversal"
    EMA_CROSSOVER             = "ema_crossover"
    BREAKOUT                  = "breakout"
    TREND_FOLLOW              = "trend_follow"
    MEAN_REVERSION            = "mean_reversion"
    # Phase 7 rule-based strategies
    LONG_PULLBACK_BULLISH     = "long_pullback_in_bullish_trend"
    SHORT_BOUNCE_BEARISH      = "short_the_bounce_in_bearish_trend"


class LogLevel(str, Enum):
    """Activity log severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    DEBUG = "debug"


class Timeframe(str, Enum):
    """Supported OHLCV candle timeframes."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


# ── Indicator classification enums ───────────────────────────────────────────

class EMAAlignment(str, Enum):
    """EMA stack alignment relative to price."""
    BULLISH = "bullish"   # EMA7 > EMA25 > EMA99, price above EMA7
    BEARISH = "bearish"   # EMA7 < EMA25 < EMA99, price below EMA7
    NEUTRAL = "neutral"   # mixed / insufficient data


class RSIState(str, Enum):
    """Relative Strength Index zone classification."""
    OVERBOUGHT = "overbought"   # RSI >= 70
    OVERSOLD   = "oversold"     # RSI <= 30
    NEUTRAL    = "neutral"      # 30 < RSI < 70


class MACDDirection(str, Enum):
    """MACD histogram direction."""
    BULLISH = "bullish"   # histogram > 0
    BEARISH = "bearish"   # histogram < 0
    NEUTRAL = "neutral"   # histogram == 0 or unavailable


class VolumeStrength(str, Enum):
    """Volume relative to rolling average."""
    HIGH   = "high"    # ratio >= 1.5
    NORMAL = "normal"  # 0.7 <= ratio < 1.5
    LOW    = "low"     # ratio < 0.7


class CandleBehavior(str, Enum):
    """Last candle pattern classification."""
    STRONG_BULL      = "strong_bull"      # large bullish body + high volume
    STRONG_BEAR      = "strong_bear"      # large bearish body + high volume
    REJECTION_BULL   = "rejection_bull"   # long lower wick (buyers rejected lows)
    REJECTION_BEAR   = "rejection_bear"   # long upper wick (sellers rejected highs)
    NEUTRAL          = "neutral"          # no dominant pattern


# ── Scalar constants ──────────────────────────────────────────────────────────

USDT_PAIR_SUFFIX = "USDT"
DEFAULT_CANDLE_LIMIT = 200
MIN_RSI_PERIOD = 5
MAX_RSI_PERIOD = 50

# Indicator parameters
EMA_PERIODS            = (7, 25, 99)   # EMA stack periods
RSI_PERIOD             = 14
MACD_FAST              = 12
MACD_SLOW              = 26
MACD_SIGNAL            = 9
VOLUME_AVG_WINDOW      = 20            # rolling window for average volume

# Classification thresholds
RSI_OVERBOUGHT         = 70.0
RSI_OVERSOLD           = 30.0
VOLUME_HIGH_RATIO      = 1.5           # volume / avg_volume >= this → HIGH
VOLUME_LOW_RATIO       = 0.7           # volume / avg_volume <= this → LOW
BODY_TO_RANGE_STRONG   = 0.60          # body / range >= this → momentum candle
WICK_TO_BODY_REJECTION = 2.0           # wick / body >= this → rejection candle

# ── Scanner filters ───────────────────────────────────────────────────────────
SCANNER_MIN_QUOTE_VOLUME_USDT = 50_000_000.0   # $50 M daily volume minimum
SCANNER_MIN_CHANGE_PCT        = 2.0            # |24h change| ≥ 2 % to pass
SCANNER_MAX_CANDIDATES        = 20             # max returned per side (LONG/SHORT)

# Substrings that identify leveraged, volatility, or stablecoin tokens.
# Any symbol whose name contains one of these is excluded.
SCANNER_SYMBOL_BLACKLIST_FRAGMENTS: tuple = (
    "UP",
    "DOWN",
    "BULL",
    "BEAR",
    "BUSD",
    "USDC",
    "TUSD",
    "FDUSD",
    "DAI",
)

# ── Multi-timeframe regime scoring ────────────────────────────────────────────
# Weights for individual signals (applied per timeframe, then timeframe-weighted)
REGIME_SCORE_EMA_STRONG    =  2.0   # full bullish/bearish EMA stack
REGIME_SCORE_MACD          =  1.0   # MACD histogram direction
REGIME_SCORE_RSI           =  1.0   # RSI state (overbought→+, oversold→-)
REGIME_SCORE_CANDLE_STRONG =  1.0   # strong bull/bear momentum candle
REGIME_SCORE_CANDLE_REJECT =  0.5   # rejection candle (softer signal)

# Per-timeframe weights (must sum to 1.0)
REGIME_WEIGHT_H1   = 0.60           # 1-hour timeframe has more structural weight
REGIME_WEIGHT_M15  = 0.40           # 15-minute timeframe is more tactical

# Composite score thresholds for regime labelling (scale: −5 to +5)
REGIME_BULLISH_THRESHOLD   =  2.5
REGIME_BEARISH_THRESHOLD   = -2.5

# Confidence bonuses
REGIME_AGREE_BONUS         =  0.10  # both timeframes agree on direction
REGIME_MAX_RAW_SCORE       =  5.0   # theoretical max absolute score (per TF)

# ── Setup scoring weights (Phase 7) ──────────────────────────────────────────
# Points awarded per component — all values are maximums; penalties give 0.
# Components must sum to SETUP_SCORE_MAX = 100.

SETUP_SCORE_MAX                    = 100.0

# BTC macro regime alignment (25 pts)
SETUP_SCORE_BTC_REGIME_ALIGNED     = 25.0   # regime matches trade direction
SETUP_SCORE_BTC_REGIME_NEUTRAL     = 10.0   # ranging / volatile / unknown
SETUP_SCORE_BTC_REGIME_CONFLICT    =  0.0   # regime opposes trade direction

# Higher timeframe (1H) EMA stack (20 pts)
SETUP_SCORE_H1_EMA_ALIGNED         = 20.0
SETUP_SCORE_H1_EMA_NEUTRAL         =  5.0
SETUP_SCORE_H1_EMA_CONFLICT        =  0.0

# Execution timeframe (15M) sub-components
SETUP_SCORE_M15_EMA_ALIGNED        = 10.0   # 15M EMA stack matches direction
SETUP_SCORE_M15_EMA_NEUTRAL        =  3.0
SETUP_SCORE_M15_EMA_CONFLICT       =  0.0

SETUP_SCORE_M15_RSI_IDEAL          =  5.0   # OVERSOLD for LONG, OVERBOUGHT for SHORT
SETUP_SCORE_M15_RSI_NEUTRAL        =  2.0   # neutral RSI (partial credit)
SETUP_SCORE_M15_RSI_CONFLICT       =  0.0   # RSI opposing direction

SETUP_SCORE_M15_MACD_ALIGNED       =  5.0
SETUP_SCORE_M15_MACD_NEUTRAL       =  0.0
SETUP_SCORE_M15_MACD_CONFLICT      =  0.0

SETUP_SCORE_M15_CANDLE_REVERSAL    =  5.0   # rejection candle in trade direction
SETUP_SCORE_M15_CANDLE_MOMENTUM    =  3.0   # strong candle in trade direction
SETUP_SCORE_M15_CANDLE_NEUTRAL     =  1.0
SETUP_SCORE_M15_CANDLE_CONFLICT    =  0.0

# Volume quality (10 pts)
SETUP_SCORE_VOLUME_HIGH            = 10.0
SETUP_SCORE_VOLUME_NORMAL          =  5.0
SETUP_SCORE_VOLUME_LOW             =  0.0

# Pullback / bounce zone quality based on price vs EMA stack (20 pts)
SETUP_SCORE_PULLBACK_OPTIMAL       = 20.0   # price in ideal retracement zone
SETUP_SCORE_PULLBACK_NEAR          = 12.0   # approaching the zone
SETUP_SCORE_PULLBACK_SHALLOW       =  5.0   # trend still intact but no pullback yet
SETUP_SCORE_PULLBACK_EXTENDED      =  0.0   # overextended — too far from structure

# Minimum score to include a setup in scored results
SETUP_MIN_SCORE_THRESHOLD          = 40.0

# Trade level derivation multipliers (applied to EMA or current price)
# Long pullback strategy
LONG_STOP_LOSS_BUFFER_PCT          = 0.015  # stop_loss = ema_99 × (1 − this)
LONG_TP1_MULT                      = 1.015  # +1.5 %
LONG_TP2_MULT                      = 1.035  # +3.5 %
LONG_TP3_MULT                      = 1.070  # +7.0 %

# Short bounce strategy
SHORT_STOP_LOSS_BUFFER_PCT         = 0.015  # stop_loss = ema_99 × (1 + this)
SHORT_TP1_MULT                     = 0.985  # −1.5 %
SHORT_TP2_MULT                     = 0.965  # −3.5 %
SHORT_TP3_MULT                     = 0.930  # −7.0 %

# ── AI review (Phase 8) ───────────────────────────────────────────────────────

# Minimum rule-based score required before calling AI (saves tokens for strong setups)
AI_MIN_SCORE_FOR_REVIEW            = 40.0

# AI call parameters
AI_TEMPERATURE                     = 0.2    # low temp → deterministic, conservative
AI_MAX_TOKENS                      = 512    # response is a small JSON blob

# Confidence bounds returned by the AI (0–1 scale)
AI_CONFIDENCE_MIN                  = 0.0
AI_CONFIDENCE_MAX                  = 1.0

# Hard guard: AI may never widen stop-loss by more than this fraction
AI_MAX_SL_WIDENING_FRACTION        = 0.0    # Phase 8: AI cannot widen SL at all
