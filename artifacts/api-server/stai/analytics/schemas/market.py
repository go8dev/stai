"""
Market regime response of `market_service.get_btc_regime`.

Smart Trader's `app/schemas/market.py` was not part of the handoff. This shape was
rebuilt from the five fields `get_btc_regime` fills in, which is its only use.
"""
from pydantic import BaseModel

from stai.analytics.core.constants import MarketRegime


class MarketRegimeResponse(BaseModel):
    regime:         MarketRegime
    btc_price:      float
    btc_change_24h: float
    trend:          str
    updated_at:     str
