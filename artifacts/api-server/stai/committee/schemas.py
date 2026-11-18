"""Strict research outputs and the owner-facing committee contract."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from stai.core.schemas import ApiModel

RoleId = Literal[
    "cio",
    "technical",
    "quantitative",
    "intelligence",
    "derivatives",
    "bull",
    "bear",
    "portfolio",
    "risk",
    "execution",
]

ROLE_NAMES = {
    "cio": "Chief Investment Officer",
    "technical": "Technical Analyst",
    "quantitative": "Quantitative Researcher",
    "intelligence": "Market Intelligence Analyst",
    "derivatives": "Derivatives Analyst",
    "bull": "Bull Researcher",
    "bear": "Bear Researcher",
    "portfolio": "Portfolio Manager",
    "risk": "Risk Officer",
    "execution": "Execution Specialist",
}


class StrictOutput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_serialization_defaults_required=True,
    )


class Finding(StrictOutput):
    role: RoleId
    summary: str = Field(min_length=1, max_length=3000)
    supporting: list[str] = Field(max_length=8)
    opposing: list[str] = Field(max_length=8)
    uncertainties: list[str] = Field(min_length=1, max_length=8)
    evidence_ids: list[str] = Field(min_length=1, max_length=12)
    confidence: int = Field(ge=0, le=100)


class FindingsPacket(StrictOutput):
    findings: list[Finding] = Field(min_length=1, max_length=3)


class ResearchTerms(StrictOutput):
    entry: Decimal = Field(gt=0)
    stop: Decimal = Field(gt=0)
    target: Decimal = Field(gt=0)
    notional_usdt: Decimal = Field(gt=0, le=200)
    leverage: int = Field(ge=1, le=2)


class Recommendation(StrictOutput):
    action: Literal["research_long", "research_short", "abstain"]
    thesis: str = Field(min_length=1, max_length=4000)
    confidence: int = Field(ge=0, le=100)
    supporting: list[str] = Field(max_length=8)
    opposing: list[str] = Field(max_length=8)
    uncertainties: list[str] = Field(min_length=1, max_length=8)
    evidence_ids: list[str] = Field(min_length=1, max_length=12)
    terms: ResearchTerms | None

    @model_validator(mode="after")
    def coherent_terms(self) -> Recommendation:
        if self.action == "abstain":
            if self.terms is not None:
                raise ValueError("An abstention cannot propose terms")
        elif self.terms is None:
            raise ValueError("Directional research needs explicit terms")
        elif self.action == "research_long":
            if not self.terms.stop < self.terms.entry < self.terms.target:
                raise ValueError("Long research needs stop < entry < target")
        elif not self.terms.target < self.terms.entry < self.terms.stop:
            raise ValueError("Short research needs target < entry < stop")
        return self


class Evidence(ApiModel):
    id: str
    kind: str
    source: str
    observed_at: datetime
    status: Literal["fresh", "stale", "unavailable"]
    summary: str
    data: dict[str, object]


class RoleDefinition(ApiModel):
    id: RoleId
    name: str
    mode: Literal["model", "deterministic"]


class CommitteeCall(ApiModel):
    stage: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: Decimal | None
    duration_ms: int
    status: str


class CommitteeRunSummary(ApiModel):
    id: str
    symbol: str
    market_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal | None
    cost_basis: str
    action: str | None
    error: str | None
    finding_count: int


class CommitteeRunDetail(CommitteeRunSummary):
    snapshot_id: str
    evidence: list[Evidence]
    findings: list[Finding]
    calls: list[CommitteeCall]
    recommendation: Recommendation | None
    memory: list[str]
    advisory_only: Literal[True]
    evidence_stale: bool


class CommitteeOverview(ApiModel):
    roles: list[RoleDefinition]
    runs: list[CommitteeRunSummary]
    paid_automation_enabled: Literal[False]
    manual_paid_runs_enabled: Literal[False]
    entry_gate: Literal["closed"]
    benchmark_state: str
    limits_status: str
    next_step: str
