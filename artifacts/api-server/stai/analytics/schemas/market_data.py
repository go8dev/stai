"""
Exchange-neutral market-data shapes used by the analytics.

Ported from Smart Trader's `app/schemas/binance.py`: `Kline` became `Candle` and
`Ticker24h` became `Ticker`, with the fields unchanged. The other shapes in that file
(connectivity, symbol info, balances, positions, orders) were left behind.
"""
from pydantic import BaseModel


class Ticker(BaseModel):
    symbol: str
    price: float
    change_24h: float          # absolute price change
    change_pct_24h: float      # % change
    volume: float              # base-asset volume
    quote_volume: float        # USDT volume
    high: float
    low: float
    trades: int


class Candle(BaseModel):
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float
    trades: int
