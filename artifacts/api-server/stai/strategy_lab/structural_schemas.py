"""Owner-facing contracts for the isolated structural pullback challenger."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from stai.core.schemas import ApiModel
from stai.strategy_lab.schemas import (
    BacktestMetrics,
    BacktestSymbol,
    FundingCoverage,
    MarketType,
    TradeSide,
)

EntryMethod = Literal["next_candle_market", "anchor_limit"]
ResearchWindowName = Literal["development", "future_validation"]


class StructuralBacktestInput(ApiModel):
    symbol: BacktestSymbol
    sample_period: ResearchWindowName


class StructuralWindow(ApiModel):
    sample_period: ResearchWindowName
    starts_at: datetime
    ends_at: datetime
    status: Literal["ready", "pending"]
    note: str


class StructuralStrategyConfiguration(ApiModel):
    strategy_version: str
    trend_timeframe: str
    entry_timeframe: str
    swing_left_bars: int
    swing_right_bars: int
    zone_cluster_atr: Decimal
    support_resistance_proximity_atr: Decimal
    confirmation_expiry_bars: int
    max_chase_atr: Decimal
    structural_stop_buffer_atr: Decimal
    target_offset_before_zone_atr: Decimal
    minimum_net_reward_risk: Decimal
    holding_periods_minutes: list[int]
    entry_methods: list[EntryMethod]
    market_cost_sensitivity_bps: list[int]
    notional_usdt: Decimal
    leverage: Decimal
    no_lookahead_rule: str
    execution_assumptions: list[str]


class StructuralCandleCoverage(ApiModel):
    symbol: BacktestSymbol
    market_type: MarketType
    timeframe: Literal["1m", "15m", "1h"]
    requested_start: datetime
    requested_end: datetime
    first_candle_at: datetime | None
    last_candle_at: datetime | None
    actual_closed_candles: int
    expected_candles: int
    missing_candles: int
    coverage_pct: Decimal
    gap_ranges: list[str]


class StructuralEntryOrder(ApiModel):
    candidate_id: str
    signal_at: datetime
    side: TradeSide
    entry_method: EntryMethod
    proposed_price: Decimal
    planned_net_reward_risk: Decimal | None
    expires_at: datetime
    status: Literal["filled", "unfilled", "cancelled", "rejected", "untestable"]
    filled_at: datetime | None
    fill_price: Decimal | None
    reason: str


class StructuralTrade(ApiModel):
    candidate_id: str
    signal_at: datetime
    entered_at: datetime
    exited_at: datetime
    side: TradeSide
    entry_method: EntryMethod
    proposed_entry_price: Decimal
    entry_price: Decimal
    stop_price: Decimal
    target_price: Decimal
    planned_net_reward_risk: Decimal
    exit_price: Decimal
    exit_reason: Literal["stop_loss", "take_profit", "time_limit"]
    holding_minutes: int
    gross_pnl_usdt: Decimal
    fees_usdt: Decimal
    maker_fees_usdt: Decimal
    taker_fees_usdt: Decimal
    funding_usdt: Decimal
    modeled_market_cost_usdt: Decimal
    net_pnl_usdt: Decimal
    stop_zone_lower: Decimal
    stop_zone_upper: Decimal
    target_zone_lower: Decimal
    target_zone_upper: Decimal


class StructuralCostResult(ApiModel):
    market_cost_bps: int
    metrics: BacktestMetrics
    trades: list[StructuralTrade]


class StructuralSegment(ApiModel):
    market_type: MarketType
    side: TradeSide
    entry_method: EntryMethod
    max_hold_minutes: int
    candidate_count: int
    reward_risk_rejected: int
    orders_placed: int
    orders_filled: int
    unfilled_limits: int
    cancelled_orders: int
    untestable_candidates: int
    overlapping_signals_skipped: int
    orders: list[StructuralEntryOrder]
    cost_results: list[StructuralCostResult]


class StructuralCandidateEvidence(ApiModel):
    """Research-only evidence snapshot compatible with proposal price/risk terms."""

    candidate_id: str
    symbol: BacktestSymbol
    market_type: MarketType
    side: TradeSide
    entry_method: EntryMethod
    strategy_version: str
    signal_at: datetime
    confirmation_at: datetime
    anchor_price: Decimal
    proposed_entry_price: Decimal
    stop_price: Decimal
    target_price: Decimal
    planned_net_reward_risk: Decimal
    notional_usdt: Decimal
    leverage: Decimal
    planned_loss_usdt: Decimal
    estimated_cost_usdt: Decimal
    evidence: dict[str, object]
    committee_status: Literal["not_run"]


class StructuralRunListItem(ApiModel):
    id: str
    created_at: datetime
    symbol: BacktestSymbol
    strategy_version: str
    sample_period: ResearchWindowName
    requested_start: datetime
    requested_end: datetime
    data_sha256: str
    completed_trades: int


class StructuralLabOverview(ApiModel):
    strategy: StructuralStrategyConfiguration
    development_window: StructuralWindow
    future_validation_window: StructuralWindow
    committee_review_status: Literal["not_run"]
    committee_notice: str
    recent_runs: list[StructuralRunListItem]


class StructuralBacktestResult(ApiModel):
    id: str
    created_at: datetime
    symbol: BacktestSymbol
    strategy: StructuralStrategyConfiguration
    sample_period: ResearchWindowName
    requested_start: datetime
    requested_end: datetime
    data_sha256: str
    candle_coverage: list[StructuralCandleCoverage]
    funding_coverage: FundingCoverage
    future_validation_window: StructuralWindow
    segments: list[StructuralSegment]
    candidate_evidence: list[StructuralCandidateEvidence]
    committee_review_status: Literal["not_run"]
    committee_notice: str
    notes: list[str]
