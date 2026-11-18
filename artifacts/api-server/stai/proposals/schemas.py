"""Owner-facing candidate and proposal payloads."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import Field

from stai.core.schemas import ApiModel


class CandidateView(ApiModel):
    id: str
    symbol: str
    market_type: Literal["spot", "futures"]
    side: Literal["long", "short"]
    score: Decimal
    status: str
    strategy_version: str
    created_at: datetime
    expires_at: datetime
    details: dict[str, Any]


class ProposalView(ApiModel):
    id: str
    candidate_id: str
    committee_run_id: str
    instrument: str
    market_type: Literal["spot", "futures"]
    side: Literal["long", "short"]
    status: Literal["pending", "approved", "rejected", "expired", "vetoed"]
    entry_price: Decimal
    stop_price: Decimal
    target_price: Decimal
    notional_usdt: Decimal
    leverage: Decimal
    planned_loss_usdt: Decimal
    estimated_cost_usdt: Decimal
    reward_risk: Decimal
    expires_at: datetime
    created_at: datetime
    decided_at: datetime | None
    decision_reason: str | None
    permit_id: str | None
    details: dict[str, Any]


class ProposalCenterOverview(ApiModel):
    candidates: list[CandidateView]
    proposals: list[ProposalView]
    paid_committee_enabled: Literal[False]
    owner_approval_required: Literal[True]
    strategy_threshold: int
    gate_status: str
    gate_message: str


class ProposalDecision(ApiModel):
    reason: str = Field(max_length=500)
