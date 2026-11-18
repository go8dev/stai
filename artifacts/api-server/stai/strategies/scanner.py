"""Resume research state from existing immutable market observations, under the scan lock."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from stai.db.models import MarketSnapshot
from stai.marketdata.schemas import MarketScannerRow
from stai.strategies.pullback import BAR, HOUR, STRATEGY_VERSION, indicator_series, replay, utc
from stai.strategies.schemas import EntryResearch


def enrich_research(session: Session, rows: list[MarketScannerRow], *, now: datetime) -> None:
    context = {}
    for row in rows:
        # Never let a provider-marked complete future candle enter an EMA calculation.
        h1 = [b for b in row.candles if utc(b.opened_at) + HOUR <= utc(now)]
        m15 = [b for b in row.candles_15m if utc(b.opened_at) + BAR <= utc(now)]
        context[(row.symbol, row.market_type)] = (
            indicator_series(h1, HOUR),
            indicator_series(m15, BAR),
        )
    for row in rows:
        latest = session.execute(
            select(MarketSnapshot)
            .where(
                MarketSnapshot.symbol == row.symbol,
                MarketSnapshot.market_type == row.market_type,
            )
            .order_by(MarketSnapshot.observed_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        prior = None
        if latest is not None and latest.details.get("entryResearch") is not None:
            saved = EntryResearch.model_validate(latest.details["entryResearch"])
            if saved.strategy_version == STRATEGY_VERSION:
                prior = saved.sides
        h1, m15 = context[(row.symbol, row.market_type)]
        btc_h1, _ = context.get(("BTC/USDT", row.market_type), ({}, {}))
        states, _ = replay(
            symbol=row.symbol,
            market_type=row.market_type,
            m15=m15,
            h1=h1,
            btc_h1=btc_h1,
            as_of=now,
            previous=prior,
        )
        expected = (
            utc(now).replace(minute=utc(now).minute // 15 * 15, second=0, microsecond=0) - BAR
        )
        if row.status != "fresh" or not m15 or max(m15) != expected:
            states = {
                side: state.model_copy(
                    update={
                        "stage": "insufficient_data",
                        "reason": "Fresh, current completed 15m history is required.",
                    }
                )
                for side, state in states.items()
            }
        # Stale/future exchange observations do not turn historical confirmation into an alert.
        if row.exchange_at is None or not timedelta(0) <= utc(now) - utc(
            row.exchange_at
        ) <= timedelta(seconds=60):
            states = {
                side: state.model_copy(
                    update={
                        "stage": "insufficient_data",
                        "reason": "Fresh exchange quote required.",
                    }
                )
                for side, state in states.items()
            }
        row.entry_research = EntryResearch(sides=states)
        row.candidate_id = None
        row.candidate_status = "research_only"
