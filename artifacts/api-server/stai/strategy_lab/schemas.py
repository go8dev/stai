"""API contracts for historical, hypothetical Strategy Laboratory runs."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from stai.core.schemas import ApiModel, DefaultedResponse

BacktestSymbol = Literal["BTCUSDT", "ETHUSDT", "SOLUSDT"]
MarketType = Literal["spot", "futures"]
TradeSide = Literal["long", "short"]
PeriodName = Literal["development", "out_of_sample"]


class BacktestInput(ApiModel):
    symbol: BacktestSymbol
    days: int = Field(ge=7, le=30)


class StrategyConfiguration(DefaultedResponse):
    strategy_version: str
    score_threshold: int
    trend_timeframe: str
    confirmation_timeframe: str
    spot_sides: list[TradeSide]
    futures_sides: list[TradeSide]
    take_profit_level: str
    stop_rule: str
    max_hold_minutes: int
    sample_split: str
    notional_usdt: Decimal
    leverage: Decimal
    spread_bps: Decimal = Decimal("0")
    slippage_bps: Decimal = Decimal("0")
    no_lookahead_rule: str
    execution_assumptions: list[str]
    entry_rules: list[str] = Field(default_factory=list)
    score_gate_enabled: bool = True
    entry_limit_rule: str = "Legacy next-15m-open entry."
    entry_expiry_bars: int = 0
    entry_fee_type: Literal["maker", "taker"] = "taker"
    target_fee_type: Literal["maker", "taker"] = "taker"
    stop_fee_type: Literal["maker", "taker"] = "taker"


class BacktestMetrics(DefaultedResponse):
    trade_count: int
    wins: int
    losses: int
    breakeven: int
    win_rate_pct: Decimal | None
    expectancy_usdt: Decimal | None
    expectancy_pct_of_notional: Decimal | None
    profit_factor: Decimal | None
    profit_factor_note: str | None
    max_drawdown_usdt: Decimal
    max_drawdown_pct: Decimal
    cumulative_pnl_usdt: Decimal
    cumulative_return_pct: Decimal
    ending_equity_usdt: Decimal
    total_fees_usdt: Decimal
    total_funding_usdt: Decimal
    total_spread_cost_usdt: Decimal
    total_slippage_cost_usdt: Decimal
    excluded_unclosed_trades: int
    unfilled_entry_orders: int = 0
    total_maker_fees_usdt: Decimal = Decimal("0")
    total_taker_fees_usdt: Decimal = Decimal("0")


class EquityPoint(ApiModel):
    at: datetime
    equity_usdt: Decimal
    cumulative_pnl_usdt: Decimal


class BacktestTrade(DefaultedResponse):
    signal_at: datetime
    entered_at: datetime
    exited_at: datetime
    side: TradeSide
    score: Decimal | None
    entry_price: Decimal
    stop_price: Decimal
    target_price: Decimal
    exit_price: Decimal
    exit_reason: Literal["stop_loss", "take_profit_1", "time_limit"]
    holding_minutes: int
    gross_pnl_usdt: Decimal
    fee_usdt: Decimal
    funding_usdt: Decimal
    spread_cost_usdt: Decimal
    slippage_cost_usdt: Decimal
    net_pnl_usdt: Decimal
    return_on_notional_pct: Decimal
    entry_order_price: Decimal | None = None
    entry_order_type: str = "legacy_next_open"
    entry_fee_type: Literal["maker", "taker"] = "taker"
    exit_order_type: str = "legacy_rule_exit"
    exit_fee_type: Literal["maker", "taker"] = "taker"
    maker_fee_usdt: Decimal = Decimal("0")
    taker_fee_usdt: Decimal = Decimal("0")


class BacktestEntryOrder(DefaultedResponse):
    signal_at: datetime
    side: TradeSide
    limit_price: Decimal
    expires_at: datetime
    status: Literal["filled", "unfilled", "cancelled"]
    filled_at: datetime | None = None
    fill_price: Decimal | None = None
    reason: str


class BacktestSegment(DefaultedResponse):
    market_type: MarketType
    side: TradeSide
    period: PeriodName
    period_start: datetime
    period_end: datetime
    metrics: BacktestMetrics
    equity_curve: list[EquityPoint]
    trades: list[BacktestTrade]
    entry_diagnostics: dict[str, int] = Field(default_factory=dict)
    entry_orders: list[BacktestEntryOrder] = Field(default_factory=list)


class CandleCoverage(ApiModel):
    symbol: BacktestSymbol
    market_type: MarketType
    requested_start: datetime
    requested_end: datetime
    first_candle_at: datetime | None
    last_candle_at: datetime | None
    actual_closed_candles: int
    expected_candles: int
    missing_candles: int
    coverage_pct: Decimal
    gap_ranges: list[str]


class FundingCoverage(ApiModel):
    status: Literal["not_applicable", "available", "partial", "unavailable"]
    records: int
    first_event_at: datetime | None
    last_event_at: datetime | None
    note: str


class StrategyLabStatus(DefaultedResponse):
    paid_committee_review_enabled: bool
    historical_ai_review_enabled: bool = False
    trading_enabled: bool
    proposal_creation_enabled: bool
    notice: str


class HistoricalReviewInput(ApiModel):
    question: str = Field(min_length=1, max_length=500)


class HistoricalReviewAnswer(DefaultedResponse):
    summary: str
    observations: list[str]
    risks: list[str]
    limitations: list[str]
    evidence_ids: list[str]


class HistoricalReviewResponse(DefaultedResponse):
    id: str
    backtest_id: str
    data_sha256: str
    created_at: datetime
    question: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    answer: HistoricalReviewAnswer
    advisory_only: bool = True


class BacktestResult(ApiModel):
    id: str
    created_at: datetime
    symbol: BacktestSymbol
    requested_days: int
    strategy: StrategyConfiguration
    engine_version: str
    requested_start: datetime
    requested_end: datetime
    development_end: datetime
    out_of_sample_start: datetime
    data_sha256: str
    candle_coverage: list[CandleCoverage]
    funding_coverage: FundingCoverage
    segments: list[BacktestSegment]
    notes: list[str]
    status: StrategyLabStatus


class BacktestListItem(ApiModel):
    id: str
    created_at: datetime
    symbol: BacktestSymbol
    requested_days: int
    strategy_version: str
    data_sha256: str
    trade_count: int
    development_end: datetime
    out_of_sample_start: datetime


class StrategyLabOverview(ApiModel):
    strategy: StrategyConfiguration
    status: StrategyLabStatus
    recent_runs: list[BacktestListItem]
