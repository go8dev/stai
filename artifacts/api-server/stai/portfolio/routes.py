"""Read-only owner views of the virtual fund and its accounting trail."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from stai.core.errors import ErrorResponse
from stai.core.runtime import Runtime, get_runtime
from stai.core.time import utcnow
from stai.db.models import BotState, FundAllocation, LedgerEntry, MarketSnapshot, PaperPosition
from stai.marketdata.schemas import (
    AllocationBalance,
    LedgerEvent,
    LedgerList,
    LedgerVerification,
    PortfolioSummary,
)
from stai.trading.ledger import ensure_fund, verify_ledger

router = APIRouter(
    prefix="/api",
    tags=["portfolio"],
    responses={401: {"model": ErrorResponse, "description": "Owner session required."}},
)
ZERO = Decimal("0")


def _ledger_event(row: LedgerEntry) -> LedgerEvent:
    return LedgerEvent(
        seq=row.seq,
        occurred_at=row.occurred_at,
        event_type=row.event_type,
        market_type=row.market_type,
        amount=row.amount,
        idempotency_key=row.idempotency_key,
        reference=row.reference,
        details=row.details,
        hash=row.hash,
    )


@router.get(
    "/portfolio/summary",
    operation_id="getPortfolioSummary",
    summary="Virtual fund balances and ledger status",
    response_model=PortfolioSummary,
    response_description="Persisted virtual fund balances and engine state.",
)
def get_portfolio_summary(
    runtime: Runtime = Depends(get_runtime),
) -> PortfolioSummary:
    with runtime.database.session() as session:
        fund = ensure_fund(session)
        allocations = (
            session.execute(select(FundAllocation).where(FundAllocation.fund_id == fund.id))
            .scalars()
            .all()
        )
        events = session.execute(select(LedgerEntry)).scalars().all()
        open_positions = (
            session.execute(select(PaperPosition).where(PaperPosition.state == "open"))
            .scalars()
            .all()
        )
        bot_states = session.execute(select(BotState).order_by(BotState.bot_id)).scalars().all()
        snapshots = (
            session.execute(
                select(MarketSnapshot)
                .where(MarketSnapshot.observed_at >= utcnow() - timedelta(days=7))
                .order_by(MarketSnapshot.observed_at.desc())
            )
            .scalars()
            .all()
        )
        latest_by_market: dict[tuple[str, str], MarketSnapshot] = {}
        for snapshot in snapshots:
            latest_by_market.setdefault((snapshot.symbol, snapshot.market_type), snapshot)
        balances: dict[str, Decimal] = defaultdict(lambda: ZERO)
        for event in events:
            balances[event.market_type] += event.amount
        fee_total = -sum(
            (event.amount for event in events if event.event_type == "fee"), start=ZERO
        )
        funding_total = sum(
            (event.amount for event in events if event.event_type == "funding"), start=ZERO
        )
        realized = sum(
            (event.amount for event in events if event.event_type == "realized_pnl"), start=ZERO
        )
        checked = verify_ledger(session)
        allocation_balances = [
            AllocationBalance(
                market_type=allocation.market_type,
                initial_balance=allocation.initial_balance,
                balance=balances[allocation.market_type],
                collateral=ZERO,
                available_balance=balances[allocation.market_type],
                exposure=ZERO,
            )
            for allocation in allocations
        ]
        positions_payload: list[dict[str, object]] = []
        spot_value = ZERO
        spot_unrealized = ZERO
        futures_unrealized = ZERO
        exposure = defaultdict(lambda: ZERO)
        collateral = ZERO
        for position in open_positions:
            symbol = position.instrument.split(":", maxsplit=1)[0]
            quote = latest_by_market.get((symbol, position.market_type))
            mark = position.mark_price
            mark_status = "stale"
            if (
                quote is not None
                and quote.status == "fresh"
                and quote.last_price is not None
                and quote.exchange_at is not None
                and (utcnow() - quote.exchange_at).total_seconds() <= 60
            ):
                mark = quote.last_price
                mark_status = "fresh"
            movement = (
                (mark - position.entry_price) * position.quantity
                if position.side == "long"
                else (position.entry_price - mark) * position.quantity
            )
            if position.market_type == "spot":
                spot_value += position.quantity * mark
                spot_unrealized += movement
            else:
                futures_unrealized += movement
                collateral += position.quantity * position.entry_price / position.leverage
            exposure[position.market_type] += position.quantity * mark
            positions_payload.append(
                {
                    "tradeId": position.trade_id,
                    "instrument": position.instrument,
                    "marketType": position.market_type,
                    "side": position.side,
                    "quantity": position.quantity,
                    "entryPrice": position.entry_price,
                    "markPrice": mark,
                    "markStatus": mark_status,
                    "leverage": position.leverage,
                    "unrealizedPnl": movement,
                    "openedAt": position.opened_at,
                }
            )
        for allocation in allocation_balances:
            allocation.exposure = exposure[allocation.market_type]
            if allocation.market_type == "futures":
                allocation.collateral = collateral
                allocation.available_balance = allocation.balance - collateral
        realized = sum(
            (
                position.realized_pnl
                for position in session.execute(select(PaperPosition)).scalars()
            ),
            start=ZERO,
        )
        equity = (
            sum((balance.balance for balance in allocation_balances), start=ZERO)
            + spot_value
            + futures_unrealized
        )
        return PortfolioSummary(
            fund_id=fund.id,
            currency=fund.currency,
            initial_balance=fund.initial_balance,
            equity=equity,
            allocations=allocation_balances,
            positions=positions_payload,
            bots=[
                {
                    "botId": row.bot_id,
                    "status": (
                        row.state.get("status", "unknown")
                        if (utcnow() - row.saved_at).total_seconds() <= 30
                        else "stale"
                    ),
                    "dryRun": row.state.get("dryRun", True),
                    "entryGate": row.state.get("entryGate", "closed"),
                    "reconciliation": (
                        row.state.get("reconciliation", "pending")
                        if (utcnow() - row.saved_at).total_seconds() <= 30
                        else "pending"
                    ),
                    "savedAt": row.saved_at,
                }
                for row in bot_states
            ],
            fees=fee_total,
            funding=funding_total,
            realized_pnl=realized,
            unrealized_pnl=spot_unrealized + futures_unrealized,
            ledger_verified=checked.ok,
            ledger_events=checked.events_checked,
            updated_at=utcnow(),
        )


@router.get(
    "/portfolio/ledger",
    operation_id="listPortfolioLedger",
    summary="Most recent virtual-fund ledger entries",
    response_model=LedgerList,
    response_description="Recent immutable accounting events.",
    responses={422: {"model": ErrorResponse, "description": "The limit is out of range."}},
)
def list_portfolio_ledger(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    runtime: Runtime = Depends(get_runtime),
) -> LedgerList:
    with runtime.database.session() as session:
        ensure_fund(session)
        rows = (
            session.execute(select(LedgerEntry).order_by(LedgerEntry.seq.desc()).limit(limit))
            .scalars()
            .all()
        )
        total = session.execute(select(func.count()).select_from(LedgerEntry)).scalar_one()
        return LedgerList(events=[_ledger_event(row) for row in rows], total=int(total))


@router.get(
    "/portfolio/ledger/verify",
    operation_id="verifyPortfolioLedger",
    summary="Verify the complete virtual-fund ledger chain",
    response_model=LedgerVerification,
    response_description="Database-only hash-chain verification result.",
)
def verify_portfolio_ledger(runtime: Runtime = Depends(get_runtime)) -> LedgerVerification:
    with runtime.database.session() as session:
        ensure_fund(session)
        result = verify_ledger(session)
        return LedgerVerification(
            ok=result.ok,
            events_checked=result.events_checked,
            first_seq=result.first_seq,
            last_seq=result.last_seq,
            head_hash=result.head_hash,
            first_break_seq=result.first_break_seq,
            reason=result.reason,
            duration_ms=result.duration_ms,
            verified_at=utcnow(),
        )
