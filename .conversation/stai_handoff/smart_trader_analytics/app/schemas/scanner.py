"""
Scanner output schemas.

ScannerCandidate   — a single symbol that has passed all filters, tagged with
                     a direction (LONG or SHORT) and the reasons it was selected.
ScannerResult      — the full output of one scanner run, split into long and
                     short buckets with metadata about the run itself.

Design notes
------------
- candidate_side uses TradeSide (LONG/SHORT) rather than a new enum so that
  downstream modules (setup scoring, AI review, trade execution) can consume
  it directly without mapping.
- scan_reasons is a list so multiple qualifying signals can be recorded and
  later surfaced in a UI or passed to the AI reviewer.
- ScannerResult carries filter_params so callers can see exactly what thresholds
  were in effect when the scan ran — useful for audit trails and UI display.
"""
from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field

from app.core.constants import TradeSide


class ScannerCandidate(BaseModel):
    """
    A single futures symbol that has passed all scanner filters.

    Attributes
    ----------
    symbol              : Binance symbol (e.g. "ETHUSDT").
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


class ScannerResult(BaseModel):
    """
    Full output of one scanner run.

    Attributes
    ----------
    long_candidates     : Symbols with a significant positive 24-hour move.
    short_candidates    : Symbols with a significant negative 24-hour move.
    total_scanned       : Number of USDT perpetual symbols evaluated.
    total_passed        : Number that survived all filters before splitting
                          into LONG/SHORT.
    filter_params       : The threshold values that were applied in this run,
                          so the caller can display or audit them.
    scanned_at          : ISO-8601 UTC timestamp of this scan run.
    """

    long_candidates:  List[ScannerCandidate] = Field(default_factory=list)
    short_candidates: List[ScannerCandidate] = Field(default_factory=list)
    total_scanned:    int                    = Field(
        ..., description="Total USDT perpetual symbols evaluated"
    )
    total_passed:     int                    = Field(
        ..., description="Symbols that passed all filters"
    )
    filter_params:    Dict[str, float]       = Field(
        default_factory=dict,
        description="Filter thresholds active during this scan",
    )
    scanned_at:       str                    = Field(
        ..., description="ISO-8601 UTC timestamp"
    )
