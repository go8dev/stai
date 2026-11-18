"""Serializable research state; never an execution or AI authorization."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from stai.core.schemas import DefaultedResponse


class PullbackEvidence(DefaultedResponse):
    side: Literal["long", "short"]
    stage: Literal[
        "waiting", "pullback_detected", "confirmed", "invalidated", "expired", "insufficient_data"
    ] = "waiting"
    reason: str = "Waiting for a completed EMA25 touch."
    last_candle_at: datetime | None = None
    pullback_at: datetime | None = None
    confirmation_at: datetime | None = None
    pullback_high: float | None = None
    pullback_low: float | None = None
    bars_waited: int = 0
    setup_id: str | None = None
    checks: dict[str, bool] = Field(default_factory=dict)


class EntryResearch(DefaultedResponse):
    strategy_version: str = "ema25-pullback-v2"
    research_only: Literal[True] = True
    ai_eligible: Literal[False] = False
    note: str = (
        "Entry research only. Legacy scores are diagnostic, not eligibility. "
        "Revised score weights, AI review and trading are not authorized."
    )
    sides: dict[str, PullbackEvidence] = Field(default_factory=dict)
