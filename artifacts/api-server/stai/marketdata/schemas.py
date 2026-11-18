"""Owner-facing shapes for public OKX market data."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from stai.core.schemas import ApiModel

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


class MarketScannerRow(ApiModel):
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


class MarketScannerResponse(ApiModel):
    provider: str
    scanned_at: datetime
    rows: list[MarketScannerRow]


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
