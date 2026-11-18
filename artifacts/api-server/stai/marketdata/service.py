"""Persist the compact, time-stamped portion of each public market scan."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from stai.db.models import MarketSnapshot
from stai.marketdata.schemas import MarketScannerRow


def persist_market_rows(session: Session, rows: list[MarketScannerRow]) -> None:
    """Append immutable-in-time market observations; prices are never overwritten."""
    for row in rows:
        instrument = (
            None
            if row.instrument is None
            else row.instrument.model_dump(mode="json", by_alias=True)
        )
        indicators = (
            None
            if row.indicators is None
            else row.indicators.model_dump(mode="json", by_alias=True)
        )
        session.add(
            MarketSnapshot(
                id=str(uuid4()),
                symbol=row.symbol,
                market_type=row.market_type,
                observed_at=row.observed_at,
                exchange_at=row.exchange_at,
                status=row.status,
                last_price=row.last_price,
                change_pct_24h=row.change_pct_24h,
                volume_24h=row.volume_24h,
                bid=row.bid,
                ask=row.ask,
                funding_rate=row.funding_rate,
                details={
                    "spreadPct": None if row.spread_pct is None else format(row.spread_pct, "f"),
                    "fundingRate": (
                        None if row.funding_rate is None else format(row.funding_rate, "f")
                    ),
                    "instrument": instrument,
                    "indicators": indicators,
                    "bids": [level.model_dump(mode="json") for level in row.bids],
                    "asks": [level.model_dump(mode="json") for level in row.asks],
                    "detail": row.detail,
                },
            )
        )
