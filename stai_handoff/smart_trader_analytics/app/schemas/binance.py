"""
Pydantic schemas for Binance Futures API responses.
All Binance-specific shapes live here — never scatter them across services.
"""
from typing import Optional
from pydantic import BaseModel, Field

from app.core.constants import TradeSide


class ConnectivityStatus(BaseModel):
    connected: bool
    testnet: bool
    server_time_ms: Optional[int] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class SymbolInfo(BaseModel):
    symbol: str
    base_asset: str
    quote_asset: str
    contract_type: str
    status: str
    price_precision: int
    quantity_precision: int
    tick_size: float
    step_size: float


class Ticker24h(BaseModel):
    symbol: str
    price: float
    change_24h: float          # absolute price change
    change_pct_24h: float      # % change
    volume: float              # base-asset volume
    quote_volume: float        # USDT volume
    high: float
    low: float
    trades: int


class Kline(BaseModel):
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float
    trades: int


class FuturesBalance(BaseModel):
    asset: str
    wallet_balance: float
    available_balance: float
    unrealized_pnl: float


class FuturesPosition(BaseModel):
    symbol: str
    side: TradeSide
    size: float                 # absolute notional size
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    pnl_percent: float
    leverage: int
    liquidation_price: float


class FuturesOrder(BaseModel):
    order_id: int
    symbol: str
    side: TradeSide
    order_type: str
    price: float
    orig_qty: float
    executed_qty: float
    status: str
    placed_at: int              # unix ms
