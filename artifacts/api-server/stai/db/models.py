"""Tables of Phase 1: the owner's user record, sign-in sessions and the audit trail.

Rules for every table in STAI:
* timestamps are `timestamp with time zone`, stored in UTC;
* money and quantities use NUMERIC (Python Decimal), never floating point;
* only the `public` schema, and no triggers, functions or grants, because the published
  database receives its structure from Replit's Publish step, which carries none of those.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

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
