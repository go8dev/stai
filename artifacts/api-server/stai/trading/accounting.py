"""Decimal-safe paper fills, fees, funding and market-book execution estimates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_DOWN, Decimal
from typing import Literal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from stai.core.time import as_utc, utcnow
from stai.db.models import LedgerEntry, PaperFill, PaperPosition
from stai.marketdata.schemas import BookLevel
from stai.trading.ledger import append_entry

Liquidity = Literal["maker", "taker"]
Side = Literal["long", "short"]
MarketType = Literal["spot", "futures"]
FillType = Literal["entry", "exit"]


@dataclass(frozen=True, slots=True)
class FeeSchedule:
    """Defaults measured from the pinned exchange library, overrideable per service."""

    spot_maker: Decimal = Decimal("0.001")
    spot_taker: Decimal = Decimal("0.0015")
    futures_maker: Decimal = Decimal("0.0002")
    futures_taker: Decimal = Decimal("0.0005")

    def rate(self, market_type: MarketType, liquidity: Liquidity) -> Decimal:
        return getattr(self, f"{market_type}_{liquidity}")


@dataclass(frozen=True, slots=True)
class FillEstimate:
    side: Side
    quantity: Decimal
    fill_price: Decimal
    spread_pct: Decimal
    slippage_pct: Decimal
    visible_notional: Decimal
    observed_at: datetime


class FillRejected(ValueError):
    """A simulated fill would exceed the visible or configured book limits."""


class FillConflict(RuntimeError):
    """A fill ID was reused for different accounting data."""


def estimate_taker_fill(
    *,
    side: Side,
    quantity: Decimal,
    bids: list[BookLevel],
    asks: list[BookLevel],
    observed_at: datetime,
    max_book_share: Decimal = Decimal("0.10"),
) -> FillEstimate:
    """Estimate a conservative book-walk fill, refusing orders above visible depth."""
    if not quantity.is_finite() or quantity <= 0:
        raise FillRejected("quantity must be positive and finite")
    if not max_book_share.is_finite() or not Decimal("0") < max_book_share <= Decimal("1"):
        raise FillRejected("book share limit is invalid")
    if not bids or not asks:
        raise FillRejected("both sides of the public order book are required")
    if any(level.price <= 0 or level.size < 0 for level in [*bids, *asks]):
        raise FillRejected("order book contains an invalid level")
    best_bid, best_ask = bids[0].price, asks[0].price
    if best_bid >= best_ask:
        raise FillRejected("order book is crossed or locked")
    levels = asks if side == "long" else bids
    visible_notional = sum((level.price * level.size for level in levels), start=Decimal("0"))
    required_notional = quantity * (best_ask if side == "long" else best_bid)
    if required_notional > visible_notional * max_book_share:
        raise FillRejected("requested notional exceeds the approved share of visible depth")

    remaining = quantity
    total_quote = Decimal("0")
    for level in levels:
        available = min(remaining, level.size)
        total_quote += available * level.price
        remaining -= available
        if remaining == 0:
            break
    if remaining > 0:
        raise FillRejected("visible book depth cannot fully fill the requested quantity")
    price = (total_quote / quantity).quantize(Decimal("0.000000000001"), rounding=ROUND_DOWN)
    mid = (best_bid + best_ask) / 2
    spread_pct = (best_ask - best_bid) / mid * 100
    best_side = best_ask if side == "long" else best_bid
    slippage_pct = abs(price - best_side) / best_side * 100 if best_side != 0 else Decimal("0")
    return FillEstimate(
        side=side,
        quantity=quantity,
        fill_price=price,
        spread_pct=spread_pct,
        slippage_pct=slippage_pct,
        visible_notional=visible_notional,
        observed_at=as_utc(observed_at),
    )


def _require_decimal(value: Decimal, name: str, *, positive: bool = False) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{name} must be a finite Decimal")
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")


def record_fill(
    session: Session,
    *,
    fill_id: str,
    trade_id: str,
    market_type: MarketType,
    instrument: str,
    side: Side,
    fill_type: FillType,
    quantity: Decimal,
    raw_price: Decimal,
    fill_price: Decimal,
    spread_pct: Decimal,
    slippage_pct: Decimal,
    liquidity: Liquidity = "taker",
    leverage: Decimal = Decimal("1"),
    fee_schedule: FeeSchedule = FeeSchedule(),
    occurred_at: datetime | None = None,
) -> PaperFill:
    """Record one actual Freqtrade dry-run fill and idempotent ledger movements."""
    if not fill_id or len(fill_id) > 128 or not trade_id or len(trade_id) > 64:
        raise ValueError("fill and trade identifiers are required")
    if (
        market_type not in {"spot", "futures"}
        or side not in {"long", "short"}
        or fill_type not in {"entry", "exit"}
        or liquidity not in {"maker", "taker"}
    ):
        raise ValueError("invalid fill classification")
    # Serialize fill imports and their cash movements as one transaction.
    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": 0x5354_4149_0006})
    if market_type == "spot" and (side != "long" or leverage != Decimal("1")):
        raise ValueError("spot paper fills must be long-only and unleveraged")
    if market_type == "futures" and not Decimal("1") <= leverage <= Decimal("2"):
        raise ValueError("futures paper fills must use isolated leverage up to 2x")
    for name, value in (
        ("quantity", quantity),
        ("raw_price", raw_price),
        ("fill_price", fill_price),
        ("spread_pct", spread_pct),
        ("slippage_pct", slippage_pct),
        ("leverage", leverage),
    ):
        _require_decimal(value, name, positive=name in {"quantity", "raw_price", "fill_price"})
        if name in {"spread_pct", "slippage_pct"} and value < 0:
            raise ValueError(f"{name} cannot be negative")
    rate = fee_schedule.rate(market_type, liquidity)
    _require_decimal(rate, "fee rate")
    if rate < 0:
        raise ValueError("fee rate cannot be negative")
    moment = as_utc(occurred_at) if occurred_at else utcnow()
    fee = (quantity * fill_price * rate).quantize(Decimal("0.000000000001"))
    prior = session.execute(
        select(PaperFill).where(PaperFill.fill_id == fill_id)
    ).scalar_one_or_none()
    if prior is not None:
        expected = (
            prior.trade_id == trade_id
            and prior.market_type == market_type
            and prior.instrument == instrument
            and prior.side == side
            and prior.fill_type == fill_type
            and prior.quantity == quantity
            and prior.raw_price == raw_price
            and prior.fill_price == fill_price
            and prior.fee == fee
            and prior.fee_rate == rate
            and prior.spread_pct == spread_pct
            and prior.slippage_pct == slippage_pct
            and prior.details == {"liquidity": liquidity, "leverage": format(leverage, "f")}
        )
        if not expected:
            raise FillConflict("the fill ID was already recorded with different values")
        return prior

    position = session.execute(
        select(PaperPosition).where(PaperPosition.trade_id == trade_id).with_for_update()
    ).scalar_one_or_none()
    if fill_type == "entry":
        if position is None:
            position = PaperPosition(
                trade_id=trade_id,
                market_type=market_type,
                instrument=instrument,
                side=side,
                quantity=quantity,
                entry_price=fill_price,
                mark_price=fill_price,
                leverage=leverage,
                realized_pnl=Decimal("0"),
                total_fees=fee,
                total_funding=Decimal("0"),
                state="open",
                opened_at=moment,
                closed_at=None,
            )
            session.add(position)
        else:
            if (
                position.state != "open"
                or position.market_type != market_type
                or position.instrument != instrument
                or position.side != side
            ):
                raise FillConflict("entry does not match the existing paper position")
            total_quantity = position.quantity + quantity
            position.entry_price = (
                position.entry_price * position.quantity + fill_price * quantity
            ) / total_quantity
            position.quantity = total_quantity
            position.mark_price = fill_price
            position.total_fees += fee
    else:
        if position is None or position.state != "open":
            raise FillRejected("an open paper position is required for an exit fill")
        if (
            position.market_type != market_type
            or position.instrument != instrument
            or position.side != side
            or quantity > position.quantity
        ):
            raise FillRejected("exit fill does not match the open paper position")
        pnl = (
            (fill_price - position.entry_price) * quantity
            if side == "long"
            else (position.entry_price - fill_price) * quantity
        )
        position.quantity -= quantity
        position.realized_pnl += pnl
        position.mark_price = fill_price
        position.total_fees += fee
        if position.quantity == 0:
            position.state = "closed"
            position.closed_at = moment

    session.flush()  # Persist a new position before its fill's foreign key is inserted.
    fill = PaperFill(
        fill_id=fill_id,
        trade_id=trade_id,
        market_type=market_type,
        instrument=instrument,
        side=side,
        fill_type=fill_type,
        quantity=quantity,
        raw_price=raw_price,
        fill_price=fill_price,
        fee=fee,
        fee_rate=rate,
        spread_pct=spread_pct,
        slippage_pct=slippage_pct,
        occurred_at=moment,
        details={"liquidity": liquidity, "leverage": format(leverage, "f")},
    )
    session.add(fill)
    session.flush()

    append_entry(
        session,
        event_type="fill_record",
        market_type=market_type,
        amount=Decimal("0"),
        idempotency_key=f"fill:{fill_id}:record",
        reference=trade_id,
        details={
            "instrument": instrument,
            "side": side,
            "fillType": fill_type,
            "quantity": format(quantity, "f"),
            "rawPrice": format(raw_price, "f"),
            "fillPrice": format(fill_price, "f"),
            "fee": format(fee, "f"),
            "feeRate": format(rate, "f"),
            "liquidity": liquidity,
            "spreadPct": format(spread_pct, "f"),
            "slippagePct": format(slippage_pct, "f"),
            "leverage": format(leverage, "f"),
        },
        occurred_at=moment,
    )
    if market_type == "spot":
        gross_cash = quantity * fill_price
        cash_delta = -gross_cash if fill_type == "entry" else gross_cash
        append_entry(
            session,
            event_type="fill",
            market_type=market_type,
            amount=cash_delta.quantize(Decimal("1e-12")),
            idempotency_key=f"fill:{fill_id}:cash",
            reference=trade_id,
            details={"instrument": instrument, "fillType": fill_type},
            occurred_at=moment,
        )
    elif fill_type == "exit":
        append_entry(
            session,
            event_type="realized_pnl",
            market_type=market_type,
            amount=pnl.quantize(Decimal("1e-12")),
            idempotency_key=f"fill:{fill_id}:pnl",
            reference=trade_id,
            details={"instrument": instrument},
            occurred_at=moment,
        )
    append_entry(
        session,
        event_type="fee",
        market_type=market_type,
        amount=-fee,
        idempotency_key=f"fill:{fill_id}:fee",
        reference=trade_id,
        details={
            "currency": "USDT",
            "feeRate": format(rate, "f"),
            "liquidity": liquidity,
            "notional": format(quantity * fill_price, "f"),
        },
        occurred_at=moment,
    )
    return fill


def record_funding(
    session: Session,
    *,
    event_id: str,
    trade_id: str,
    amount: Decimal,
    occurred_at: datetime | None = None,
) -> LedgerEntry:
    """Record one signed funding payment using its exchange/bot event ID."""
    if not event_id or len(event_id) > 128:
        raise ValueError("funding event ID is required")
    _require_decimal(amount, "funding amount")
    position = session.execute(
        select(PaperPosition).where(PaperPosition.trade_id == trade_id).with_for_update()
    ).scalar_one_or_none()
    if position is None or position.market_type != "futures":
        raise FillRejected("funding requires a known futures position")
    moment = as_utc(occurred_at) if occurred_at else utcnow()
    existing = session.execute(
        select(LedgerEntry).where(LedgerEntry.idempotency_key == f"funding:{event_id}")
    ).scalar_one_or_none()
    if existing is not None:
        if existing.amount != amount or existing.reference != trade_id:
            raise FillConflict("funding event ID was already recorded with different values")
        return existing
    position.total_funding += amount
    return append_entry(
        session,
        event_type="funding",
        market_type="futures",
        amount=amount,
        idempotency_key=f"funding:{event_id}",
        reference=trade_id,
        details={"currency": "USDT"},
        occurred_at=moment,
    )


def accounting_reconciles(session: Session) -> bool:
    """Cross-check the cash ledger against immutable fills and position totals."""
    entries = session.execute(select(LedgerEntry)).scalars().all()
    fills = session.execute(select(PaperFill)).scalars().all()
    positions = session.execute(select(PaperPosition)).scalars().all()
    quantum = Decimal("1e-12")
    for market, initial in (("spot", Decimal("600")), ("futures", Decimal("400"))):
        actual = sum((row.amount for row in entries if row.market_type == market), Decimal("0"))
        market_fills = [row for row in fills if row.market_type == market]
        market_positions = [row for row in positions if row.market_type == market]
        expected = initial - sum((row.fee for row in market_fills), Decimal("0"))
        expected += sum((row.total_funding for row in market_positions), Decimal("0"))
        if market == "spot":
            expected += sum(
                (
                    (Decimal("-1") if row.fill_type == "entry" else Decimal("1"))
                    * (row.quantity * row.fill_price).quantize(quantum)
                    for row in market_fills
                ),
                Decimal("0"),
            )
        else:
            expected += sum((row.realized_pnl for row in market_positions), Decimal("0"))
        if actual.quantize(quantum) != expected.quantize(quantum):
            return False
    for position in positions:
        trade_fills = [row for row in fills if row.trade_id == position.trade_id]
        entered = [row for row in trade_fills if row.fill_type == "entry"]
        entry_qty = sum((row.quantity for row in entered), Decimal("0"))
        exit_qty = sum(
            (row.quantity for row in trade_fills if row.fill_type == "exit"), Decimal("0")
        )
        if entry_qty <= 0 or position.quantity != entry_qty - exit_qty:
            return False
        average = sum((row.quantity * row.fill_price for row in entered), Decimal("0")) / entry_qty
        if position.entry_price.quantize(quantum) != average.quantize(quantum):
            return False
        if position.total_fees != sum((row.fee for row in trade_fills), Decimal("0")):
            return False
    return True
