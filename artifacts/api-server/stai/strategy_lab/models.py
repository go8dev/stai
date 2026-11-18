"""Durable, owner-scoped Strategy Laboratory run records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Index, Integer, String, Text
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

    __table_args__ = (
        Index("ix_strategy_backtest_runs_owner_created", "user_id", "created_at"),
    )
