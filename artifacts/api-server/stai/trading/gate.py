"""Fail-closed, single-use validation for owner-approved paper entries.

Phase 4 supplies permits through an owner-facing approval action. Phase 2 deliberately
does not expose a permit-creation API, so the running strategy cannot obtain approval.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from stai.core.time import as_utc, utcnow
from stai.db.models import BotState, MarketSnapshot, PaperPosition, TradingPermit
from stai.trading.accounting import accounting_reconciles
from stai.trading.ledger import verify_ledger


class PermitDenied(RuntimeError):
    """The exact requested entry does not match a current owner approval."""


@dataclass(frozen=True, slots=True)
class EntryRequest:
    permit_id: str
    instrument: str
    market_type: str
    side: str
    notional: Decimal
    price: Decimal
    leverage: Decimal
    stop_price: Decimal
    target_price: Decimal


def consume_permit(
    session: Session,
    request: EntryRequest,
    *,
    now: datetime | None = None,
) -> TradingPermit:
    """Atomically consume a permit only when every approved term still matches."""
    moment = as_utc(now) if now is not None else utcnow()
    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": 0x5354_4149_0005})
    if any(
        not isinstance(value, Decimal) or not value.is_finite()
        for value in (
            request.notional,
            request.price,
            request.leverage,
            request.stop_price,
            request.target_price,
        )
    ):
        raise PermitDenied("entry values are invalid")
    permit = session.execute(
        select(TradingPermit).where(TradingPermit.id == request.permit_id).with_for_update()
    ).scalar_one_or_none()
    if permit is None:
        raise PermitDenied("no owner approval matches this entry")
    if permit.consumed or permit.consumed_at is not None:
        raise PermitDenied("owner approval has already been used")
    if permit.approved_at > moment or permit.expires_at <= moment:
        raise PermitDenied("owner approval is not current")
    if (
        permit.instrument != request.instrument
        or permit.market_type != request.market_type
        or permit.side != request.side
    ):
        raise PermitDenied("entry differs from the approved instrument or side")
    if request.notional <= 0 or request.notional != permit.max_notional:
        raise PermitDenied("entry differs from the exact approved amount")
    if request.price <= 0:
        raise PermitDenied("entry price is invalid")
    drift_pct = abs(request.price - permit.approved_price) / permit.approved_price * 100
    if drift_pct > permit.max_price_drift_pct:
        raise PermitDenied("price moved outside the approved band")
    if (
        request.leverage != permit.leverage
        or request.stop_price != permit.stop_price
        or request.target_price != permit.target_price
    ):
        raise PermitDenied("entry differs from the approved risk parameters")
    if request.market_type == "spot" and (
        request.side != "long" or request.leverage != Decimal("1")
    ):
        raise PermitDenied("spot entries must be long-only and unleveraged")
    if request.market_type == "futures" and not Decimal("1") <= request.leverage <= Decimal("2"):
        raise PermitDenied("futures leverage must be between 1x and 2x")
    open_positions = session.execute(
        select(func.count()).select_from(PaperPosition).where(PaperPosition.state == "open")
    ).scalar_one()
    if open_positions >= 3:
        raise PermitDenied("the three-position portfolio limit has been reached")
    if request.side == "long" and not request.stop_price < request.price < request.target_price:
        raise PermitDenied("long stop and target must bracket the approved entry price")
    if request.side == "short" and not request.target_price < request.price < request.stop_price:
        raise PermitDenied("short stop and target must bracket the approved entry price")
    if not verify_ledger(session).ok or not accounting_reconciles(session):
        raise PermitDenied("ledger integrity is not clear")
    bot = session.get(BotState, request.market_type)
    if (
        bot is None
        or not 0 <= (moment - bot.saved_at).total_seconds() <= 960
        or bot.state.get("status") != "running"
        or bot.state.get("reconciliation") != "clear"
    ):
        raise PermitDenied("paper engine reconciliation is not current and clear")
    symbol = request.instrument.split(":", maxsplit=1)[0]
    quote = session.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.symbol == symbol, MarketSnapshot.market_type == request.market_type)
        .order_by(MarketSnapshot.observed_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if (
        quote is None
        or quote.status != "fresh"
        or quote.exchange_at is None
        or not 0 <= (moment - quote.exchange_at).total_seconds() <= 60
    ):
        raise PermitDenied("market data is not current")
    permit.consumed = True
    permit.consumed_at = moment
    session.flush()
    return permit
