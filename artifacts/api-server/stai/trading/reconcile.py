"""Read completed dry-run orders from a consistent engine snapshot, never submit orders."""

from __future__ import annotations

import gzip
import sqlite3
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from stai.db.models import MarketSnapshot, PaperFill, TradingPermit
from stai.marketdata.schemas import BookLevel
from stai.trading.accounting import FillRejected, estimate_taker_fill, record_fill, record_funding


def snapshot_orders(snapshot: bytes) -> list[dict]:
    """Read-only view of the pinned Freqtrade order schema, in fill order."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        connection.deserialize(gzip.decompress(snapshot))
        if not connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='orders'"
        ).fetchone():
            return []
        return [
            dict(row)
            for row in connection.execute(
                "SELECT o.id, o.ft_trade_id, o.ft_order_side, o.side, o.average, o.price, "
                "o.filled, o.order_filled_date, o.funding_fee, t.pair, t.is_short, "
                "t.leverage, t.enter_tag FROM orders o JOIN trades t ON t.id=o.ft_trade_id "
                "WHERE o.filled > 0 AND o.ft_is_open=0 "
                "ORDER BY o.order_filled_date, o.id"
            )
        ]
    finally:
        connection.close()


def import_completed_orders(session: Session, market_type: str, snapshot: bytes) -> None:
    """Only import fills backed by an already-consumed owner permit and timely book evidence.

    No permits are created here. Unknown fills stop reconciliation instead of being
    silently accepted. Phase 2's strategy emits no entries, so normally this reads zero rows.
    """
    for order in snapshot_orders(snapshot):
        fill_id = f"{market_type}:order:{order['id']}"
        trade_id = f"{market_type}:{order['ft_trade_id']}"
        side = "short" if order["is_short"] else "long"
        entry_side = "sell" if side == "short" else "buy"
        fill_type = "entry" if order["ft_order_side"] == entry_side else "exit"
        quantity = Decimal(str(order["filled"])).quantize(Decimal("1e-12"))
        raw = Decimal(str(order["average"] or order["price"]))
        prior = session.get(PaperFill, fill_id)
        if prior is not None:
            if (
                prior.trade_id != trade_id
                or prior.quantity != quantity
                or prior.raw_price != raw
                or prior.instrument != order["pair"]
                or prior.side != side
                or prior.fill_type != fill_type
            ):
                raise FillRejected("previously imported engine fill changed")
            continue
        moment = datetime.fromisoformat(order["order_filled_date"]).replace(tzinfo=UTC)
        tag = str(order["enter_tag"] or "")
        permit = (
            session.get(TradingPermit, tag.removeprefix("stai:"))
            if tag.startswith("stai:")
            else None
        )
        if (
            permit is None
            or not permit.consumed
            or permit.consumed_at is None
            or permit.instrument != order["pair"]
            or permit.market_type != market_type
            or permit.side != side
            or permit.leverage != Decimal(str(order["leverage"]))
        ):
            raise FillRejected("engine fill has no matching consumed owner approval")
        if fill_type == "entry" and (
            not permit.approved_at <= moment <= permit.expires_at
            or quantity * raw > permit.max_notional
            or abs(raw - permit.approved_price) / permit.approved_price * 100
            > permit.max_price_drift_pct
        ):
            raise FillRejected("engine fill differs from the owner's approved terms")
        quote = session.execute(
            select(MarketSnapshot)
            .where(
                MarketSnapshot.symbol == order["pair"].split(":")[0],
                MarketSnapshot.market_type == market_type,
                MarketSnapshot.observed_at <= moment,
            )
            .order_by(MarketSnapshot.observed_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if (
            quote is None
            or quote.status != "fresh"
            or quote.exchange_at is None
            or not 0 <= (moment - quote.exchange_at).total_seconds() <= 60
        ):
            raise FillRejected("no timely order-book evidence for engine fill")
        # Buy exits of shorts walk asks; sell exits of longs walk bids.
        estimate = estimate_taker_fill(
            side="long" if order["side"] == "buy" else "short",
            quantity=quantity,
            bids=[BookLevel.model_validate(x) for x in quote.details.get("bids", [])],
            asks=[BookLevel.model_validate(x) for x in quote.details.get("asks", [])],
            observed_at=quote.exchange_at,
        )
        # Never improve on the engine's raw execution price.
        adjusted = (
            max(raw, estimate.fill_price)
            if order["side"] == "buy"
            else min(raw, estimate.fill_price)
        )
        slippage = abs(adjusted - raw) / raw * 100
        record_fill(
            session,
            fill_id=fill_id,
            trade_id=trade_id,
            market_type=market_type,
            instrument=order["pair"],
            side=side,
            fill_type=fill_type,
            quantity=quantity,
            raw_price=raw,
            fill_price=adjusted,
            spread_pct=estimate.spread_pct,
            slippage_pct=slippage,
            leverage=Decimal(str(order["leverage"])),
            occurred_at=moment,
        )
        if market_type == "futures" and order["funding_fee"]:
            record_funding(
                session,
                event_id=f"{fill_id}:funding",
                trade_id=trade_id,
                amount=Decimal(str(order["funding_fee"])).quantize(Decimal("1e-12")),
                occurred_at=moment,
            )
