"""
Candidate schema — the input of the setup scoring service.

ScannerCandidate   — a single symbol tagged with a direction (LONG or SHORT)
                     and the reasons it was selected.

Ported from Smart Trader's scanner schemas. Only ScannerCandidate was kept: the
scanner itself and its ScannerResult were left behind, because STAI watches three
fixed instruments instead of scanning a market.

Design notes
------------
- candidate_side uses TradeSide (LONG/SHORT) rather than a new enum so that
  downstream modules can consume it directly without mapping.
- scan_reasons is a list so multiple qualifying signals can be recorded and
  later surfaced in a UI.
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from stai.analytics.core.constants import TradeSide


class ScannerCandidate(BaseModel):
    """
    A single symbol put forward for setup scoring.

    Attributes
    ----------
    symbol              : Instrument symbol (e.g. "ETHUSDT").
    last_price          : Last traded price in USDT.
    change_percent_24h  : 24-hour percentage price change.
    quote_volume        : 24-hour volume in USDT (quote asset).
    candidate_side      : LONG if move is positive, SHORT if negative.
    scan_reasons        : Ordered list of human-readable strings that justify
                          why this symbol was selected and which side it is on.
    scanned_at          : ISO-8601 UTC timestamp of the scan that produced it.
    """

    symbol:             str
    last_price:         float      = Field(..., description="Last price in USDT")
    change_percent_24h: float      = Field(..., description="24-hour % change")
    quote_volume:       float      = Field(..., description="24-hour USDT volume")
    candidate_side:     TradeSide  = Field(..., description="LONG or SHORT")
    scan_reasons:       List[str]  = Field(
        default_factory=list,
        description="Reasons this symbol passed the filter and its direction",
    )
    scanned_at:         str        = Field(..., description="ISO-8601 UTC timestamp")
