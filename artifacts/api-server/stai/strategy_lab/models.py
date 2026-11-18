"""Durable, owner-scoped Strategy Laboratory run records."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from stai.db.base import Base, UtcDateTime


class StrategyBacktestRun(Base):
    __tablename__ = "strategy_backtest_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(12), nullable=False)
    requested_days: Mapped[int] = mapped_column(Integer, nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    data_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    source_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    __table_args__ = (Index("ix_strategy_backtest_runs_owner_created", "user_id", "created_at"),)


class StrategyBacktestReview(Base):
    """One owner-requested, bounded advisory review of an immutable saved run."""

    __tablename__ = "strategy_backtest_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    backtest_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("strategy_backtest_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        Text, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    data_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    reserved_usd: Mapped[Decimal] = mapped_column(
        Numeric(18, 10), nullable=False, default=Decimal("0")
    )
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 10))
    answer: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint("status IN ('running','completed','unknown')", name="status"),
        CheckConstraint("reserved_usd >= 0", name="reserved_nonnegative"),
        Index("ix_strategy_backtest_reviews_owner_created", "user_id", "created_at"),
        Index("ix_strategy_backtest_reviews_run_created", "backtest_id", "created_at"),
    )
