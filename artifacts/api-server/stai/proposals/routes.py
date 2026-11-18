"""Read-only scanner candidates and explicit owner decisions for paper proposals."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from stai.auth.deps import current_auth
from stai.auth.gate import AuthContext
from stai.committee.scoring import setup_scores
from stai.core.errors import ErrorResponse
from stai.core.runtime import Runtime, get_runtime
from stai.marketdata.routes import _enrich
from stai.marketdata.schemas import MarketScannerRow
from stai.proposals.schemas import (
    CandidateView,
    ProposalCenterOverview,
    ProposalDecision,
    ProposalView,
)
from stai.proposals.service import (
    CANDIDATE_TTL,
    STRATEGY_THRESHOLD,
    decide_proposal,
    list_proposal_center,
    persist_market_scan,
)

router = APIRouter(
    prefix="/api",
    tags=["proposals"],
    responses={401: {"model": ErrorResponse, "description": "Owner session required."}},
)

_GATE_MESSAGE = (
    "Paid committee reviews are disabled. Candidates can be collected, but no AI call or "
    "proposal is created until a supported model and daily run/spend limits are authorized."
)


def _candidate_view(row) -> CandidateView:
    return CandidateView(
        id=row.id,
        symbol=row.symbol,
        market_type=row.market_type,
        side=row.side,
        score=row.score,
        status=row.status,
        strategy_version=row.strategy_version,
        created_at=row.created_at,
        expires_at=row.created_at + CANDIDATE_TTL,
        details=row.details,
    )


def _proposal_view(row) -> ProposalView:
    return ProposalView(
        id=row.id,
        candidate_id=row.candidate_id,
        committee_run_id=row.committee_run_id,
        instrument=row.instrument,
        market_type=row.market_type,
        side=row.side,
        status=row.status,
        entry_price=row.entry_price,
        stop_price=row.stop_price,
        target_price=row.target_price,
        notional_usdt=row.notional_usdt,
        leverage=row.leverage,
        planned_loss_usdt=row.planned_loss_usdt,
        estimated_cost_usdt=row.estimated_cost_usdt,
        reward_risk=row.reward_risk,
        expires_at=row.expires_at,
        created_at=row.created_at,
        decided_at=row.decided_at,
        decision_reason=row.decision_reason,
        permit_id=row.permit_id,
        details=row.details,
    )


@router.get(
    "/proposal-center",
    operation_id="getProposalCenter",
    response_model=ProposalCenterOverview,
    summary="Get qualified candidates and owner-facing paper proposals",
)
def get_proposal_center(
    runtime: Runtime = Depends(get_runtime),
) -> ProposalCenterOverview:
    with runtime.database.session() as session:
        candidates, proposals = list_proposal_center(session, now=runtime.now())
        return ProposalCenterOverview(
            candidates=[_candidate_view(row) for row in candidates],
            proposals=[_proposal_view(row) for row in proposals],
            paid_committee_enabled=False,
            owner_approval_required=True,
            strategy_threshold=STRATEGY_THRESHOLD,
            gate_status="paid_review_disabled",
            gate_message=_GATE_MESSAGE,
        )


async def _fresh_scan(runtime: Runtime) -> tuple[list[MarketScannerRow], list[str]]:
    rows = [_enrich(row) for row in await runtime.okx_market_data.scanner()]
    btc = next(
        (row for row in rows if row.symbol == "BTC/USDT" and row.market_type == "spot"),
        None,
    )
    for row in rows:
        row.setup_scores = setup_scores(row, btc)
    with runtime.database.session() as session:
        ids = persist_market_scan(session, rows, now=runtime.now())
    return rows, ids


@router.post(
    "/proposals/{proposal_id}/approve",
    operation_id="approveTradeProposal",
    response_model=ProposalView,
    responses={
        403: {"model": ErrorResponse, "description": "Same-origin CSRF check failed."},
        404: {"model": ErrorResponse, "description": "Proposal was not found."},
        409: {"model": ErrorResponse, "description": "Proposal failed a final safety check."},
        503: {"model": ErrorResponse, "description": "Fresh market data is unavailable."},
        422: {"model": ErrorResponse, "description": "Request could not be validated."},
    },
    summary="Approve exact proposal terms for paper mode",
)
async def approve_trade_proposal(
    proposal_id: str,
    body: ProposalDecision,
    runtime: Runtime = Depends(get_runtime),
    auth: AuthContext = Depends(current_auth),
) -> ProposalView:
    try:
        rows, snapshot_ids = await _fresh_scan(runtime)
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail="Fresh OKX market evidence is unavailable."
        ) from exc
    with runtime.database.session() as session:
        from stai.db.models import MarketSnapshot, TradeProposal

        proposal = session.get(TradeProposal, proposal_id)
        if proposal is None:
            raise HTTPException(status_code=404, detail="Proposal was not found.")
        matching = next(
            (
                (row, snapshot_id)
                for row, snapshot_id in zip(rows, snapshot_ids, strict=True)
                if row.symbol == proposal.instrument.split(":")[0]
                and row.market_type == proposal.market_type
            ),
            None,
        )
        if matching is None:
            raise HTTPException(status_code=503, detail="Fresh market evidence is unavailable.")
        _, snapshot_id = matching
        snapshot = session.get(MarketSnapshot, snapshot_id)
        try:
            decided = decide_proposal(
                session,
                proposal_id=proposal_id,
                owner_id=auth.user.user_id,
                approve=True,
                reason=body.reason,
                now=runtime.now(),
                current_snapshot=snapshot,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="Proposal was not found.") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _proposal_view(decided)


@router.post(
    "/proposals/{proposal_id}/reject",
    operation_id="rejectTradeProposal",
    response_model=ProposalView,
    responses={
        403: {"model": ErrorResponse, "description": "Same-origin CSRF check failed."},
        404: {"model": ErrorResponse, "description": "Proposal was not found."},
        409: {"model": ErrorResponse, "description": "Proposal is no longer pending."},
        422: {"model": ErrorResponse, "description": "Request could not be validated."},
    },
    summary="Reject a paper trade proposal",
)
def reject_trade_proposal(
    proposal_id: str,
    body: ProposalDecision,
    runtime: Runtime = Depends(get_runtime),
    auth: AuthContext = Depends(current_auth),
) -> ProposalView:
    with runtime.database.session() as session:
        try:
            proposal = decide_proposal(
                session,
                proposal_id=proposal_id,
                owner_id=auth.user.user_id,
                approve=False,
                reason=body.reason,
                now=runtime.now(),
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="Proposal was not found.") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _proposal_view(proposal)
