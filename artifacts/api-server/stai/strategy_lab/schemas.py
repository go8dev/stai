"""API contracts for historical, hypothetical Strategy Laboratory runs."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from stai.core.schemas import ApiModel

BacktestSymbol = Literal["BTCUSDT", "ETHUSDT", "SOLUSDT"]
MarketType = Literal["spot", "futures"]
TradeSide = Literal["long", "short"]
PeriodName = Literal["development", "out_of_sample"]


class BacktestInput(ApiModel):
    symbol: BacktestSymbol = "BTCUSDT"
    days: int = Field(default=30, ge=7, le=30)
    spread_bps: Decimal = Field(default=Decimal("5"), ge=0, le=50)
    slippage_bps: Decimal = Field(default=Decimal("5"), ge=0, le=50)


class StrategyConfiguration(ApiModel):
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
    spread_bps: Decimal
    slippage_bps: Decimal
    no_lookahead_rule: str
    execution_assumptions: list[str]


class BacktestMetrics(ApiModel):
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


class EquityPoint(ApiModel):
    at: datetime
    equity_usdt: Decimal
    cumulative_pnl_usdt: Decimal


class BacktestTrade(ApiModel):
    signal_at: datetime
    entered_at: datetime
    exited_at: datetime
    side: TradeSide
    score: Decimal
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


class BacktestSegment(ApiModel):
    market_type: MarketType
    side: TradeSide
    period: PeriodName
    period_start: datetime
    period_end: datetime
    metrics: BacktestMetrics
    equity_curve: list[EquityPoint]
    trades: list[BacktestTrade]


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


class StrategyLabStatus(ApiModel):
    paid_committee_review_enabled: bool
    trading_enabled: bool
    proposal_creation_enabled: bool
    notice: str


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
