"""The market-data interface the analytics read through.

Smart Trader's analytics called a Binance client directly. In STAI they ask this
interface for candles and a 24-hour ticker instead. Its OKX implementation, built on
public endpoints, arrives with the market-data service in Phase 2. Until one is
registered, asking for the provider fails with a clear error instead of returning
made-up data.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from stai.analytics.schemas.market_data import Candle, Ticker


class MarketDataNotConfigured(RuntimeError):
    """No market-data provider has been registered yet."""


@runtime_checkable
class MarketDataProvider(Protocol):
    """Read-only public market data. There is no method that places or changes an order."""

    async def get_ticker(self, symbol: str) -> Ticker | None:
        """24-hour statistics for `symbol`, or None when they cannot be fetched."""
        ...

    async def get_candles(self, symbol: str, timeframe: str, limit: int = 200) -> list[Candle]:
        """The latest `limit` candles, oldest first. Empty when they cannot be fetched."""
        ...


_provider: MarketDataProvider | None = None


def set_market_data_provider(provider: MarketDataProvider | None) -> None:
    """Register the provider the analytics use. Pass None to clear it."""
    global _provider
    _provider = provider


def get_market_data_provider() -> MarketDataProvider:
    if _provider is None:
        raise MarketDataNotConfigured(
            "No market-data provider is registered. The OKX public-data provider is "
            "delivered in Phase 2; until then the analytics can only be given data directly."
        )
    return _provider
