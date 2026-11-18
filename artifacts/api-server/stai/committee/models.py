"""Research-only persistence, kept separate from portfolio/accounting models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from stai.db.base import Base, UtcDateTime


class CommitteeAgent(Base):
    __tablename__ = "committee_agents"
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)


class CommitteeRun(Base):
    __tablename__ = "committee_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # One benchmark slot, including failed/interrupted attempts. No automatic retry.
    purpose: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(24), nullable=False)
    market_type: Mapped[str] = mapped_column(String(12), nullable=False)
    snapshot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("market_snapshots.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(UtcDateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 10))
    cost_basis: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    recommendation: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    memory: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint("status IN ('running','completed','failed','interrupted')", name="status"),
        CheckConstraint("market_type IN ('spot','futures')", name="market_type"),
        Index("ix_committee_runs_started", "started_at"),
    )


class CommitteeFinding(Base):
    __tablename__ = "committee_findings"
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("committee_runs.id", ondelete="RESTRICT"), primary_key=True
    )
    role_id: Mapped[str] = mapped_column(
        String(24), ForeignKey("committee_agents.id", ondelete="RESTRICT"), primary_key=True
    )
    finding: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class CommitteeCallRecord(Base):
    __tablename__ = "committee_calls"
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("committee_runs.id", ondelete="RESTRICT"), primary_key=True
    )
    stage: Mapped[str] = mapped_column(String(32), primary_key=True)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 10))
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
