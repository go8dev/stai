"""Tables of Phase 1: the owner's user record, sign-in sessions and the audit trail.

Rules for every table in STAI:
* timestamps are `timestamp with time zone`, stored in UTC;
* money and quantities use NUMERIC (Python Decimal), never floating point;
* only the `public` schema, and no triggers, functions or grants, because the published
  database receives its structure from Replit's Publish step, which carries none of those.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from stai.committee import models as committee_models  # noqa: F401
from stai.db.base import Base, UtcDateTime


class User(Base):
    """A Replit account that has signed in. Only the owner's account can."""

    __tablename__ = "users"

    # The account ID from the identity token (`sub`).
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    username: Mapped[str | None] = mapped_column(Text)
    first_name: Mapped[str | None] = mapped_column(Text)
    last_name: Mapped[str | None] = mapped_column(Text)
    profile_image_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(UtcDateTime)


class AuthSession(Base):
    """A browser session. Only the SHA-256 of the cookie value is stored."""

    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)

    __table_args__ = (
        Index("ix_auth_sessions_user_id", "user_id"),
        Index("ix_auth_sessions_expires_at", "expires_at"),
    )


class AuditEvent(Base):
    """One record of the append-only audit trail.

    `seq` is assigned by the application, one higher than the record before. `hash` covers
    the record's own content and `prev_hash`, so changing or removing any earlier record
    breaks every hash after it. Records are only ever inserted.
    """

    __tablename__ = "audit_events"

    seq: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    occurred_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(Text)
    correlation_id: Mapped[str | None] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        CheckConstraint("seq > 0", name="seq_positive"),
        # Two records can never follow the same predecessor.
        Index("uq_audit_events_prev_hash", "prev_hash", unique=True),
        Index("uq_audit_events_hash", "hash", unique=True),
        Index("ix_audit_events_event_type", "event_type"),
        Index("ix_audit_events_occurred_at", "occurred_at"),
    )


class VirtualFund(Base):
    """The single paper fund. Its initial capital is never rewritten."""

    __tablename__ = "virtual_funds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    currency: Mapped[str] = mapped_column(String(12), nullable=False)
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)

    __table_args__ = (CheckConstraint("id = 1", name="singleton"),)


class FundAllocation(Base):
    """The fixed initial split between spot and futures."""

    __tablename__ = "fund_allocations"

    fund_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("virtual_funds.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    market_type: Mapped[str] = mapped_column(String(12), primary_key=True)
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)

    __table_args__ = (
        CheckConstraint("market_type IN ('spot', 'futures')", name="market_type"),
        CheckConstraint("initial_balance >= 0", name="balance_nonnegative"),
    )


class LedgerEntry(Base):
    """An append-only, hash-chained USDT cash movement."""

    __tablename__ = "ledger_entries"

    seq: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    occurred_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    market_type: Mapped[str] = mapped_column(String(12), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    reference: Mapped[str | None] = mapped_column(String(128))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    __table_args__ = (
        CheckConstraint("seq > 0", name="seq_positive"),
        CheckConstraint("market_type IN ('spot', 'futures')", name="market_type"),
        Index("uq_ledger_entries_prev_hash", "prev_hash", unique=True),
        Index("ix_ledger_entries_occurred_at", "occurred_at"),
    )


class MarketSnapshot(Base):
    """A timestamped public-market observation used by the real-data screens."""

    __tablename__ = "market_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(24), nullable=False)
    market_type: Mapped[str] = mapped_column(String(12), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    exchange_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    last_price: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    change_pct_24h: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    volume_24h: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    bid: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    ask: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    funding_rate: Mapped[Decimal | None] = mapped_column(Numeric(24, 16))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        CheckConstraint("market_type IN ('spot', 'futures')", name="market_type"),
        CheckConstraint("status IN ('fresh', 'stale', 'unavailable')", name="status"),
        Index("ix_market_snapshots_symbol_market_time", "symbol", "market_type", "observed_at"),
    )


class BotState(Base):
    """The latest non-secret engine state, stored outside the ephemeral VM filesystem."""

    __tablename__ = "bot_states"

    bot_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    saved_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    sqlite_snapshot: Mapped[bytes | None] = mapped_column(LargeBinary)
    snapshot_sha256: Mapped[str | None] = mapped_column(String(64))


class PaperPosition(Base):
    """Current/reconciled state of one Freqtrade dry-run position."""

    __tablename__ = "paper_positions"

    trade_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    market_type: Mapped[str] = mapped_column(String(12), nullable=False)
    instrument: Mapped[str] = mapped_column(String(24), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    mark_price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    leverage: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    total_fees: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    total_funding: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    state: Mapped[str] = mapped_column(String(12), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(UtcDateTime)

    __table_args__ = (
        CheckConstraint("market_type IN ('spot', 'futures')", name="market_type"),
        CheckConstraint("side IN ('long', 'short')", name="side"),
        CheckConstraint("state IN ('open', 'closed')", name="state"),
        CheckConstraint("quantity >= 0", name="quantity_nonnegative"),
        CheckConstraint("entry_price > 0", name="entry_price_positive"),
        CheckConstraint("mark_price > 0", name="mark_price_positive"),
        CheckConstraint("leverage >= 1 AND leverage <= 2", name="leverage_range"),
        Index("ix_paper_positions_state_market", "state", "market_type"),
    )


class PaperFill(Base):
    """An idempotently imported Freqtrade dry-run fill with STAI fee accounting."""

    __tablename__ = "paper_fills"

    fill_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    trade_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("paper_positions.trade_id", ondelete="RESTRICT"), nullable=False
    )
    market_type: Mapped[str] = mapped_column(String(12), nullable=False)
    instrument: Mapped[str] = mapped_column(String(24), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    fill_type: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    raw_price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    fill_price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    fee_rate: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    spread_pct: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    slippage_pct: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        CheckConstraint("market_type IN ('spot', 'futures')", name="market_type"),
        CheckConstraint("side IN ('long', 'short')", name="side"),
        CheckConstraint("fill_type IN ('entry', 'exit')", name="fill_type"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("raw_price > 0", name="raw_price_positive"),
        CheckConstraint("fill_price > 0", name="fill_price_positive"),
        CheckConstraint("fee >= 0", name="fee_nonnegative"),
        CheckConstraint("fee_rate >= 0", name="fee_rate_nonnegative"),
        CheckConstraint("spread_pct >= 0", name="spread_nonnegative"),
        CheckConstraint("slippage_pct >= 0", name="slippage_nonnegative"),
        Index("ix_paper_fills_trade_time", "trade_id", "occurred_at"),
    )


class TradingPermit(Base):
    """One owner-approved paper entry permit; API creation arrives in Phase 4."""

    __tablename__ = "trading_permits"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    instrument: Mapped[str] = mapped_column(String(24), nullable=False)
    market_type: Mapped[str] = mapped_column(String(12), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    max_notional: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    approved_price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    max_price_drift_pct: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    leverage: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    stop_price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    target_price: Mapped[Decimal] = mapped_column(Numeric(30, 12), nullable=False)
    approved_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    consumed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint("market_type IN ('spot', 'futures')", name="market_type"),
        CheckConstraint("side IN ('long', 'short')", name="side"),
        CheckConstraint("max_notional > 0", name="notional_positive"),
        CheckConstraint("approved_price > 0", name="price_positive"),
        CheckConstraint("max_price_drift_pct >= 0", name="drift_nonnegative"),
        CheckConstraint("leverage >= 1 AND leverage <= 2", name="leverage_range"),
        Index("ix_trading_permits_expiry", "expires_at"),
    )
