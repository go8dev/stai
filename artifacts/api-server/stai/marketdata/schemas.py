"""Owner-facing shapes for public OKX market data."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from stai.core.schemas import ApiModel, DefaultedResponse
from stai.strategies.schemas import EntryResearch

MarketType = Literal["spot", "futures"]
Freshness = Literal["fresh", "stale", "unavailable"]


class BookLevel(ApiModel):
    price: Decimal
    size: Decimal


class CandlePoint(ApiModel):
    opened_at: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_volume: Decimal
    complete: bool


class InstrumentRules(ApiModel):
    instrument_id: str
    min_size: Decimal | None
    lot_size: Decimal | None
    tick_size: Decimal | None
    contract_value: Decimal | None
    max_leverage: Decimal | None


class MarketIndicators(ApiModel):
    trend: str
    trend_15m: str
    rsi: float | None
    rsi_state: str
    macd_direction: str
    macd_direction_15m: str
    volume_strength: str
    volatility_pct: float | None
    candle_behavior: str
    screening_state: Literal["watch", "no_alignment", "unavailable"]


class MarketScannerRow(DefaultedResponse):
    symbol: str
    market_type: MarketType
    status: Freshness
    observed_at: datetime | None
    exchange_at: datetime | None
    age_seconds: int | None
    last_price: Decimal | None
    change_pct_24h: Decimal | None
    volume_24h: Decimal | None
    bid: Decimal | None
    ask: Decimal | None
    spread_pct: Decimal | None
    funding_rate: Decimal | None
    next_funding_at: datetime | None
    instrument: InstrumentRules | None
    indicators: MarketIndicators | None
    candles: list[CandlePoint]
    candles_15m: list[CandlePoint]
    bids: list[BookLevel]
    asks: list[BookLevel]
    detail: str | None
    setup_scores: dict[str, Any] | None
    candidate_id: str | None
    candidate_status: str | None
    entry_research: EntryResearch | None = None


class MarketScannerResponse(ApiModel):
    provider: str
    scanned_at: datetime
    rows: list[MarketScannerRow]


MtfTimeframe = Literal["1d", "4h", "1h", "15m"]
MtfDirection = Literal["bullish", "bearish", "neutral"]


class MtfQuote(ApiModel):
    last_price: Decimal | None
    change_pct_24h: Decimal | None
    volume_24h: Decimal | None
    exchange_at: datetime | None
    observed_at: datetime
    status: Freshness


class MtfIndicatorSnapshot(ApiModel):
    timeframe: MtfTimeframe
    status: Literal["fresh", "stale", "insufficient", "unavailable"]
    latest_completed_at: datetime | None
    close: Decimal | None
    rsi14: float | None
    sma20: float | None
    sma50: float | None
    atr14: float | None
    sma_direction: MtfDirection
    rsi_direction: MtfDirection
    candles: list[CandlePoint]
    expected_candles: int
    actual_candles: int
    gap_count: int
    detail: str | None


class MtfScoreComponent(ApiModel):
    timeframe: MtfTimeframe
    weight: int
    sma_direction: MtfDirection
    sma_points: Decimal | None
    rsi_direction: MtfDirection
    rsi_points: Decimal | None


class MtfDirectionalEvidence(ApiModel):
    strategy_version: str
    status: Literal["complete", "stale", "insufficient"]
    bullish_score: Decimal | None
    bearish_score: Decimal | None
    neutral_points: Decimal | None
    classification: Literal[
        "strong_bullish",
        "moderate_bullish",
        "strong_bearish",
        "moderate_bearish",
        "mixed",
        "insufficient",
    ]
    components: list[MtfScoreComponent]
    disagreement_reasons: list[str]
    note: str


class MtfZone(ApiModel):
    id: str
    source_timeframe: MtfTimeframe
    kind: Literal["support", "resistance"]
    lower: Decimal
    upper: Decimal
    pivot_at: datetime
    confirmed_at: datetime
    atr_at_calculation: Decimal | None
    independent_reactions: int
    state: Literal["active", "tested", "broken", "retested", "invalidated"]
    distance_from_price: Decimal | None
    confluence_timeframes: list[MtfTimeframe]
    is_prior_extreme: bool
    detail: str


class MtfIndicativePlan(ApiModel):
    direction: Literal["long", "short"]
    entry_zone_lower: Decimal
    entry_zone_upper: Decimal
    trigger: str
    entry_reference: Decimal
    stop_reference: Decimal
    target_reference: Decimal
    gross_reward_risk: Decimal
    estimated_net_reward_risk: Decimal | None
    supporting_zone_ids: list[str]
    opposing_evidence: list[str]
    signal_at: datetime
    expires_at: datetime
    price_basis: Literal["indicative_only"]
    cost_note: str


class MtfOpportunity(ApiModel):
    state: Literal[
        "bullish_watchlist",
        "bearish_watchlist",
        "waiting_for_pullback",
        "entry_zone_reached",
        "awaiting_confirmation",
        "indicative_setup_ready",
        "invalidated",
        "expired",
        "insufficient_data",
        "no_opportunity",
    ]
    direction: Literal["long", "short"] | None
    anchor_id: str | None
    anchor_at: datetime | None
    signal_at: datetime | None
    expires_at: datetime | None
    research_rule_version: str
    detail: str
    plan: MtfIndicativePlan | None


class MtfInstrumentAnalysis(ApiModel):
    symbol: str
    market_type: MarketType
    instrument_id: str
    quote: MtfQuote
    timeframes: list[MtfIndicatorSnapshot]
    evidence: MtfDirectionalEvidence
    btc_context: MtfDirectionalEvidence | None
    zones: list[MtfZone]
    nearest_support: MtfZone | None
    nearest_resistance: MtfZone | None
    opportunity: MtfOpportunity
    committee_status: str
    observed_at: datetime


class MtfMarketIntelligenceResponse(ApiModel):
    provider: Literal["OKX"]
    strategy_version: str
    observed_at: datetime
    instruments: list[MtfInstrumentAnalysis]
    limitations: list[str]


class LedgerEvent(ApiModel):
    seq: int
    occurred_at: datetime
    event_type: str
    market_type: MarketType
    amount: Decimal
    idempotency_key: str
    reference: str | None
    details: dict[str, object]
    hash: str


class AllocationBalance(ApiModel):
    market_type: MarketType
    initial_balance: Decimal
    balance: Decimal
    collateral: Decimal
    available_balance: Decimal
    exposure: Decimal


class PortfolioSummary(ApiModel):
    fund_id: int
    currency: str
    initial_balance: Decimal
    equity: Decimal
    allocations: list[AllocationBalance]
    positions: list[dict[str, object]]
    bots: list[dict[str, object]]
    fees: Decimal
    funding: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    ledger_verified: bool
    ledger_events: int
    updated_at: datetime


class LedgerList(ApiModel):
    events: list[LedgerEvent]
    total: int


class LedgerVerification(ApiModel):
    ok: bool
    events_checked: int
    first_seq: int | None
    last_seq: int | None
    head_hash: str | None
    first_break_seq: int | None
    reason: str | None
    duration_ms: float
    verified_at: datetime
