"""Decimal-safe virtual-fund initialization and immutable ledger operations."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from stai.core.time import as_utc, utcnow
from stai.db.models import FundAllocation, LedgerEntry, VirtualFund

_FUND_LOCK_KEY = 0x5354_4149_0002
_LEDGER_LOCK_KEY = 0x5354_4149_0003
GENESIS_HASH = "0" * 64


class LedgerInputError(ValueError):
    """A value cannot safely be written to the paper ledger."""


class IdempotencyConflict(RuntimeError):
    """An idempotency key was reused for a different accounting event."""


@dataclass(frozen=True, slots=True)
class LedgerVerification:
    ok: bool
    events_checked: int
    first_seq: int | None
    last_seq: int | None
    head_hash: str | None
    first_break_seq: int | None
    reason: str | None
    duration_ms: float


def _canonical_hash(
    *,
    seq: int,
    occurred_at: datetime,
    event_type: str,
    market_type: str,
    amount: Decimal,
    idempotency_key: str,
    reference: str | None,
    details: dict[str, Any],
    prev_hash: str,
) -> str:
    payload = {
        "seq": seq,
        "occurred_at": as_utc(occurred_at).isoformat(),
        "event_type": event_type,
        "market_type": market_type,
        "amount": format(amount, ".12f"),
        "idempotency_key": idempotency_key,
        "reference": reference,
        "details": details,
        "prev_hash": prev_hash,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_amount(amount: Decimal) -> None:
    if not isinstance(amount, Decimal) or not amount.is_finite():
        raise LedgerInputError("ledger amounts must be finite Decimal values")
    if abs(amount) >= Decimal("1e18") or amount != amount.quantize(Decimal("1e-12")):
        raise LedgerInputError("ledger amounts exceed the supported precision")


def append_entry(
    session: Session,
    *,
    event_type: str,
    market_type: str,
    amount: Decimal,
    idempotency_key: str,
    reference: str | None = None,
    details: dict[str, Any] | None = None,
    occurred_at: datetime | None = None,
) -> LedgerEntry:
    """Append one signed USDT movement. A repeated identical key is a no-op."""
    _validate_amount(amount)
    if market_type not in {"spot", "futures"}:
        raise LedgerInputError("market_type must be spot or futures")
    if not event_type or len(event_type) > 40:
        raise LedgerInputError("event_type is required and must be at most 40 characters")
    if not idempotency_key or len(idempotency_key) > 128:
        raise LedgerInputError("idempotency_key is required and must be at most 128 characters")
    body = dict(details or {})

    existing = session.execute(
        select(LedgerEntry).where(LedgerEntry.idempotency_key == idempotency_key)
    ).scalar_one_or_none()
    if existing is not None:
        if (
            existing.event_type != event_type
            or existing.market_type != market_type
            or existing.amount != amount
            or existing.reference != reference
            or existing.details != body
        ):
            raise IdempotencyConflict("the ledger idempotency key belongs to another event")
        return existing

    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _LEDGER_LOCK_KEY})
    existing = session.execute(
        select(LedgerEntry).where(LedgerEntry.idempotency_key == idempotency_key)
    ).scalar_one_or_none()
    if existing is not None:
        if (
            existing.event_type != event_type
            or existing.market_type != market_type
            or existing.amount != amount
            or existing.reference != reference
            or existing.details != body
        ):
            raise IdempotencyConflict("the ledger idempotency key belongs to another event")
        return existing

    last = session.execute(
        select(LedgerEntry.seq, LedgerEntry.hash).order_by(LedgerEntry.seq.desc()).limit(1)
    ).first()
    seq = 1 if last is None else last.seq + 1
    previous = GENESIS_HASH if last is None else last.hash
    moment = as_utc(occurred_at) if occurred_at else utcnow()
    entry = LedgerEntry(
        seq=seq,
        occurred_at=moment,
        event_type=event_type,
        market_type=market_type,
        amount=amount,
        idempotency_key=idempotency_key,
        reference=reference,
        details=body,
        prev_hash=previous,
        hash=_canonical_hash(
            seq=seq,
            occurred_at=moment,
            event_type=event_type,
            market_type=market_type,
            amount=amount,
            idempotency_key=idempotency_key,
            reference=reference,
            details=body,
            prev_hash=previous,
        ),
    )
    session.add(entry)
    session.flush()
    return entry


def ensure_fund(session: Session, *, now: datetime | None = None) -> VirtualFund:
    """Create the one virtual fund and its allocation entries exactly once."""
    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _FUND_LOCK_KEY})
    fund = session.execute(
        select(VirtualFund).where(VirtualFund.id == 1).with_for_update()
    ).scalar_one_or_none()
    if fund is not None:
        if fund.currency != "USDT" or fund.initial_balance != Decimal("1000"):
            raise RuntimeError("the virtual fund differs from its approved initial capital")
        allocations = (
            session.execute(select(FundAllocation).where(FundAllocation.fund_id == fund.id))
            .scalars()
            .all()
        )
        actual = {allocation.market_type: allocation.initial_balance for allocation in allocations}
        expected = {"spot": Decimal("600.000000000000"), "futures": Decimal("400.000000000000")}
        if actual != expected:
            raise RuntimeError(
                "the initial virtual-fund allocations do not match the approved plan"
            )
        return fund

    moment = as_utc(now) if now else utcnow()
    fund = VirtualFund(
        id=1,
        currency="USDT",
        initial_balance=Decimal("1000.000000000000"),
        created_at=moment,
    )
    session.add(fund)
    session.flush()
    allocations = (
        ("spot", Decimal("600.000000000000")),
        ("futures", Decimal("400.000000000000")),
    )
    for market_type, amount in allocations:
        session.add(
            FundAllocation(
                fund_id=fund.id,
                market_type=market_type,
                initial_balance=amount,
            )
        )
        append_entry(
            session,
            event_type="fund_allocation",
            market_type=market_type,
            amount=amount,
            idempotency_key=f"fund:1:initial:{market_type}",
            reference="fund:1",
            details={"currency": "USDT"},
            occurred_at=moment,
        )
    session.flush()
    return fund


def verify_ledger(session: Session) -> LedgerVerification:
    """Recompute the complete ledger chain and report the first inconsistency."""
    started = time.perf_counter()
    rows = session.execute(select(LedgerEntry).order_by(LedgerEntry.seq)).scalars().all()
    previous = GENESIS_HASH
    first_seq: int | None = rows[0].seq if rows else None
    last_seq: int | None = rows[-1].seq if rows else None
    for expected, row in enumerate(rows, start=1):
        if row.seq != expected:
            return LedgerVerification(
                False,
                expected - 1,
                first_seq,
                last_seq,
                previous,
                row.seq,
                "sequence_gap",
                round((time.perf_counter() - started) * 1000, 1),
            )
        if row.prev_hash != previous:
            return LedgerVerification(
                False,
                expected - 1,
                first_seq,
                last_seq,
                previous,
                row.seq,
                "prev_hash_mismatch",
                round((time.perf_counter() - started) * 1000, 1),
            )
        expected_hash = _canonical_hash(
            seq=row.seq,
            occurred_at=row.occurred_at,
            event_type=row.event_type,
            market_type=row.market_type,
            amount=row.amount,
            idempotency_key=row.idempotency_key,
            reference=row.reference,
            details=row.details,
            prev_hash=row.prev_hash,
        )
        if expected_hash != row.hash:
            return LedgerVerification(
                False,
                expected - 1,
                first_seq,
                last_seq,
                previous,
                row.seq,
                "hash_mismatch",
                round((time.perf_counter() - started) * 1000, 1),
            )
        previous = row.hash
    return LedgerVerification(
        True,
        len(rows),
        first_seq,
        last_seq,
        None if not rows else previous,
        None,
        None,
        round((time.perf_counter() - started) * 1000, 1),
    )
