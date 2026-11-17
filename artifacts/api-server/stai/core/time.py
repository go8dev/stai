"""Time rules: store and compute in UTC, display in Asia/Manila."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

DISPLAY_TIMEZONE = "Asia/Manila"
MANILA = ZoneInfo(DISPLAY_TIMEZONE)


def utcnow() -> datetime:
    """Current time as a timezone-aware UTC value."""
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """Convert an aware datetime to UTC. Naive values are rejected, never guessed."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("naive datetime: every timestamp must carry a timezone")
    return value.astimezone(UTC)
