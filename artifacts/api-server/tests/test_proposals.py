"""Phase 4 scanner qualification and owner-controlled paper proposals."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from stai.committee.models import CommitteeAgent, CommitteeFinding, CommitteeRun
from stai.committee.schemas import ROLE_NAMES, Recommendation
from stai.core.time import utcnow
from stai.db.models import (
    AuditEvent,
    BotState,
    MarketSnapshot,
    SetupCandidate,
    TradeProposal,
    TradingPermit,
)
from stai.marketdata.schemas import BookLevel, CandlePoint, InstrumentRules, MarketScannerRow
from stai.proposals.service import (
    PROPOSAL_TTL,
    _candidate_gates,
    create_proposal_from_committee_run,
    decide_proposal,
    list_proposal_center,
    persist_market_scan,
)
from stai.trading.ledger import ensure_fund

from .conftest import Harness
from .support import csrf_headers, sign_in

D = Decimal


def _scan_row(now, *, market_type: str = "spot") -> MarketScannerRow:
    candles_h1 = [
        CandlePoint(
            opened_at=now - timedelta(hours=40 - index),
            open=D("100"),
            high=D("101"),
            low=D("99"),
            close=D("100"),
            volume=D("10"),
            quote_volume=D("1000"),
            complete=True,
        )
        for index in range(40)
    ]
    candles_15m = [
        CandlePoint(
            opened_at=now - timedelta(minutes=15 * (40 - index)),
            open=D("100"),
            high=D("101"),
            low=D("99"),
            close=D("100"),
            volume=D("10"),
            quote_volume=D("1000"),
            complete=True,
        )
        for index in range(40)
    ]
    return MarketScannerRow(
        symbol="BTC/USDT",
        market_type=market_type,
        status="fresh",
        observed_at=now,
        exchange_at=now,
        age_seconds=0,
        last_price=D("100"),
        change_pct_24h=D("0.5"),
        volume_24h=D("1000000"),
        bid=D("99.99"),
        ask=D("100.01"),
        spread_pct=D("0.02"),
        funding_rate=D("0.0001") if market_type == "futures" else None,
        next_funding_at=now + timedelta(hours=4) if market_type == "futures" else None,
        instrument=InstrumentRules(
            instrument_id="BTC-USDT" if market_type == "spot" else "BTC-USDT-SWAP",
            min_size=D("0.01"),
            lot_size=D("0.01"),
            tick_size=D("0.01"),
            contract_value=None,
            max_leverage=D("2") if market_type == "futures" else None,
        ),
        indicators=None,
        candles=candles_h1,
        candles_15m=candles_15m,
        bids=[BookLevel(price=D("99.99"), size=D("1000"))],
        asks=[BookLevel(price=D("100.01"), size=D("1000"))],
        detail=None,
        candidate_id=None,
        candidate_status=None,
        setup_scores={
            "status": "available",
            "scores": {
                "long": {
                    "score": 78,
                    "strategy_type": "long_pullback_in_bullish_trend",
                    "entry_zone_low": 99,
                    "entry_zone_high": 101,
                    "stop_loss": 98,
                    "tp1": 102,
                    "tp2": 104,
                    "tp3": 106,
                    "reasons": ["BTC regime aligned", "15-minute candle confirmation"],
                }
            },
            "h1Snapshot": {
                "ema_alignment": "bullish",
                "current_price": 100,
                "ema_7": 101,
                "ema_25": 99.5,
                "ema_99": 90,
            },
            "m15Snapshot": {
                "ema_alignment": "bullish",
                "macd_direction": "bullish",
                "candle_behavior": "rejection_bull",
            },
            "btcRegime": {"status": "fresh", "regime": "bullish"},
        },
    )


def _seed_synthetic_review(harness: Harness) -> tuple:
    now = harness.clock()
    row = _scan_row(now)
    with harness.runtime.database.session() as session:
        ensure_fund(session, now=now)
        snapshot_id = persist_market_scan(session, [row], now=now)[0]
        assert row.candidate_id is not None
        session.add(
            BotState(
                bot_id="spot",
                saved_at=now,
                state={
                    "status": "running",
                    "dryRun": True,
                    "reconciliation": "clear",
                    "ledgerVerified": True,
                },
            )
        )
        for role, name in ROLE_NAMES.items():
            session.add(CommitteeAgent(id=role, name=name, mode="deterministic"))
        run_id = str(uuid4())
        evidence = [
            {
                "id": evidence_id,
                "kind": "synthetic_test",
                "source": "test",
                "observedAt": now.isoformat(),
                "status": "fresh",
                "summary": (
                    f"Synthetic evidence used by a test only. Snapshot {snapshot_id}"
                    if evidence_id == "market"
                    else "Synthetic evidence used by a test only."
                ),
                "data": ({"setupScores": row.setup_scores} if evidence_id == "market" else {}),
            }
            for evidence_id in ("market", "news", "portfolio")
        ]
        recommendation = Recommendation(
            action="research_long",
            thesis="Synthetic test recommendation.",
            confidence=75,
            supporting=["Synthetic evidence"],
            opposing=[],
            uncertainties=["Test data only"],
            evidence_ids=["market", "portfolio"],
            terms={
                "entry": "100",
                "stop": "99",
                "target": "102",
                "notional_usdt": "50",
                "leverage": 1,
            },
        )
        session.add(
            CommitteeRun(
                id=run_id,
                purpose=f"test-{run_id[:8]}",
                symbol=row.symbol,
                market_type=row.market_type,
                snapshot_id=snapshot_id,
                status="completed",
                started_at=now,
                finished_at=now,
                duration_ms=1,
                model="synthetic-test-only",
                input_tokens=0,
                output_tokens=0,
                cost_usd=None,
                cost_basis="synthetic test",
                evidence=evidence,
                recommendation=recommendation.model_dump(mode="json", by_alias=True),
                memory=[],
            )
        )
        session.flush()
        for role in ROLE_NAMES:
            session.add(
                CommitteeFinding(
                    run_id=run_id,
                    role_id=role,
                    finding={
                        "role": role,
                        "summary": "Synthetic test finding",
                        "evidenceIds": ["market"],
                    },
                )
            )
        session.flush()
    return now, row.candidate_id, run_id, snapshot_id


def test_candidate_gates_use_completed_confirmation_and_70_threshold() -> None:
    now = utcnow()
    row = _scan_row(now)
    assert _candidate_gates(row, row.setup_scores, "long", now) == []

    exact_threshold = {
        **row.setup_scores,
        "scores": {"long": {**row.setup_scores["scores"]["long"], "score": 70}},
    }
    assert _candidate_gates(row, exact_threshold, "long", now) == []
    assert any(
        "does not support" in reason
        for reason in _candidate_gates(row, row.setup_scores, "short", now)
    )

    low_score = {
        **row.setup_scores,
        "scores": {"long": {**row.setup_scores["scores"]["long"], "score": 69}},
    }
    assert any("below 70" in reason for reason in _candidate_gates(row, low_score, "long", now))

    no_candle_confirmation = {
        **row.setup_scores,
        "m15Snapshot": {**row.setup_scores["m15Snapshot"], "candle_behavior": "neutral"},
    }
    assert any(
        "15-minute candle" in reason
        for reason in _candidate_gates(row, no_candle_confirmation, "long", now)
    )

    stale_row = row.model_copy(update={"exchange_at": now - timedelta(seconds=61)})
    assert any(
        "older than 60 seconds" in reason
        for reason in _candidate_gates(stale_row, stale_row.setup_scores, "long", now)
    )
    incomplete_row = row.model_copy(
        update={
            "candles": [candle.model_copy(update={"complete": False}) for candle in row.candles]
        }
    )
    assert any(
        "completed 1-hour and 15-minute candles" in reason
        for reason in _candidate_gates(incomplete_row, incomplete_row.setup_scores, "long", now)
    )

    futures = _scan_row(now, market_type="futures")
    futures_without_funding = futures.model_copy(
        update={"funding_rate": None, "next_funding_at": None}
    )
    assert any(
        "funding data is required" in reason
        for reason in _candidate_gates(
            futures_without_funding, futures_without_funding.setup_scores, "long", now
        )
    )


def test_scan_candidates_are_persisted_once_per_unchanged_setup(harness: Harness) -> None:
    now = harness.clock()
    row = _scan_row(now)
    with harness.runtime.database.session() as session:
        first_snapshot = persist_market_scan(session, [row], now=now)[0]
        candidate_id = row.candidate_id
    assert candidate_id is not None

    row.candidate_id = None
    with harness.runtime.database.session() as session:
        second_snapshot = persist_market_scan(session, [row], now=now)[0]
        assert second_snapshot != first_snapshot
        assert row.candidate_id == candidate_id

    with harness.runtime.database.session() as session:
        assert session.scalar(select(func.count()).select_from(SetupCandidate)) == 1
        candidate = session.get(SetupCandidate, candidate_id)
        assert candidate is not None
        assert candidate.status == "awaiting_ai_authorization"
        assert candidate.score == D("78")


def test_complete_synthetic_review_creates_only_an_exact_owner_paper_permit(
    harness: Harness,
) -> None:
    now, candidate_id, run_id, snapshot_id = _seed_synthetic_review(harness)
    with harness.runtime.database.session() as session:
        proposal = create_proposal_from_committee_run(
            session,
            candidate_id=candidate_id,
            run_id=run_id,
            now=now,
        )
        assert proposal is not None
        proposal_id = proposal.id
        assert proposal.status == "pending"
        assert proposal.planned_loss_usdt < D("5")

    with harness.runtime.database.session() as session:
        approved = decide_proposal(
            session,
            proposal_id=proposal_id,
            owner_id="test-owner",
            approve=True,
            reason="Approved in a test only.",
            now=now,
            current_snapshot=session.get(MarketSnapshot, snapshot_id),
        )
        assert approved.status == "approved"
        assert approved.permit_id is not None
        permit = session.get(TradingPermit, approved.permit_id)
        assert permit is not None
        assert permit.consumed is False
        assert permit.market_type == "spot"
        assert permit.side == "long"
        assert permit.max_notional == D("50")
        assert (
            session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(AuditEvent.event_type == "trading_permit.issued")
            )
            == 1
        )


def test_risk_check_veto_is_persisted_and_audited(
    harness: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    now, candidate_id, run_id, _ = _seed_synthetic_review(harness)

    def reject_risk(*args, **kwargs):
        raise ValueError("Synthetic risk veto.")

    monkeypatch.setattr("stai.proposals.service._evaluate_terms", reject_risk)
    with harness.runtime.database.session() as session:
        proposal = create_proposal_from_committee_run(
            session,
            candidate_id=candidate_id,
            run_id=run_id,
            now=now,
        )
        assert proposal is None
        candidate = session.get(SetupCandidate, candidate_id)
        assert candidate is not None
        assert candidate.status == "vetoed"
        assert session.scalar(select(func.count()).select_from(TradeProposal)) == 0
        event = session.scalar(
            select(AuditEvent).where(AuditEvent.event_type == "setup_candidate.vetoed")
        )
        assert event is not None
        assert event.payload["candidateId"] == candidate_id
        assert event.payload["committeeRunId"] == run_id


def test_changed_market_vetoes_owner_approval_without_issuing_a_permit(
    harness: Harness,
) -> None:
    now, candidate_id, run_id, _ = _seed_synthetic_review(harness)
    with harness.runtime.database.session() as session:
        proposal = create_proposal_from_committee_run(
            session,
            candidate_id=candidate_id,
            run_id=run_id,
            now=now,
        )
        assert proposal is not None
        proposal_id = proposal.id

    changed_row = _scan_row(now)
    changed_row.last_price = D("103")
    changed_row.bid = D("102.99")
    changed_row.ask = D("103.01")
    with harness.runtime.database.session() as session:
        current_snapshot_id = persist_market_scan(session, [changed_row], now=now)[0]
        vetoed = decide_proposal(
            session,
            proposal_id=proposal_id,
            owner_id="test-owner",
            approve=True,
            reason="Approved in a test only.",
            now=now,
            current_snapshot=session.get(MarketSnapshot, current_snapshot_id),
        )
        assert vetoed.status == "vetoed"
        assert vetoed.permit_id is None
        assert vetoed.decision_reason is not None
        assert "Risk revalidation veto" in vetoed.decision_reason
        assert session.scalar(select(func.count()).select_from(TradingPermit)) == 0
        event = session.scalar(
            select(AuditEvent).where(AuditEvent.event_type == "trade_proposal.vetoed")
        )
        assert event is not None
        assert event.payload["proposalId"] == proposal_id


def test_owner_rejection_is_audited(harness: Harness) -> None:
    now, candidate_id, run_id, _ = _seed_synthetic_review(harness)
    with harness.runtime.database.session() as session:
        proposal = create_proposal_from_committee_run(
            session,
            candidate_id=candidate_id,
            run_id=run_id,
            now=now,
        )
        assert proposal is not None
        rejected = decide_proposal(
            session,
            proposal_id=proposal.id,
            owner_id="test-owner",
            approve=False,
            reason="Rejected in a test only.",
            now=now,
        )
        assert rejected.status == "rejected"
        assert rejected.decision_reason == "Rejected in a test only."
        event = session.scalar(
            select(AuditEvent).where(AuditEvent.event_type == "trade_proposal.rejected")
        )
        assert event is not None


def test_proposal_expiry_is_audited(harness: Harness) -> None:
    now, candidate_id, run_id, _ = _seed_synthetic_review(harness)
    with harness.runtime.database.session() as session:
        proposal = create_proposal_from_committee_run(
            session,
            candidate_id=candidate_id,
            run_id=run_id,
            now=now,
        )
        assert proposal is not None
        proposal_id = proposal.id
    with harness.runtime.database.session() as session:
        _, proposals = list_proposal_center(session, now=now + PROPOSAL_TTL)
        expired = next(item for item in proposals if item.id == proposal_id)
        assert expired.status == "expired"
        event = session.scalar(
            select(AuditEvent).where(AuditEvent.event_type == "trade_proposal.expired")
        )
        assert event is not None


@pytest.mark.parametrize("failure_mode", ["failed", "unavailable_evidence"])
def test_failed_or_unavailable_committee_review_cannot_create_proposal(
    harness: Harness, failure_mode: str
) -> None:
    now, candidate_id, run_id, _ = _seed_synthetic_review(harness)
    with harness.runtime.database.session() as session:
        run = session.get(CommitteeRun, run_id)
        assert run is not None
        if failure_mode == "failed":
            run.status = "failed"
            expected_error = "completed committee review"
        else:
            run.evidence = [{**item, "status": "unavailable"} for item in run.evidence]
            expected_error = "complete and fresh"
        with pytest.raises(ValueError, match=expected_error):
            create_proposal_from_committee_run(
                session,
                candidate_id=candidate_id,
                run_id=run_id,
                now=now,
            )
        assert session.scalar(select(func.count()).select_from(TradeProposal)) == 0


def test_committee_abstention_cannot_create_proposal(harness: Harness) -> None:
    now, candidate_id, run_id, _ = _seed_synthetic_review(harness)
    with harness.runtime.database.session() as session:
        run = session.get(CommitteeRun, run_id)
        assert run is not None
        run.recommendation = Recommendation(
            action="abstain",
            thesis="Synthetic abstention.",
            confidence=0,
            supporting=[],
            opposing=["Evidence is inconclusive."],
            uncertainties=["Insufficient confirmation"],
            evidence_ids=["market"],
            terms=None,
        ).model_dump(mode="json", by_alias=True)
        with pytest.raises(ValueError, match="Abstentions"):
            create_proposal_from_committee_run(
                session,
                candidate_id=candidate_id,
                run_id=run_id,
                now=now,
            )
        assert session.scalar(select(func.count()).select_from(TradeProposal)) == 0


def test_proposal_center_is_read_only_until_csrf_protected_owner_decision(harness: Harness) -> None:
    assert harness.client.get("/api/proposal-center").status_code == 401
    assert sign_in(harness.client, harness.provider).status_code == 302

    overview = harness.client.get("/api/proposal-center")
    assert overview.status_code == 200, overview.text
    body = overview.json()
    assert body["paidCommitteeEnabled"] is False
    assert body["ownerApprovalRequired"] is True
    assert body["strategyThreshold"] == 70
    assert "model" in body["gateMessage"].lower()
    assert "spend limits" in body["gateMessage"].lower()

    rejected = harness.client.post(
        "/api/proposals/unknown/reject",
        json={"reason": "test"},
        headers=csrf_headers(harness.client),
    )
    assert rejected.status_code == 404
    assert (
        harness.client.post(
            "/api/proposals/unknown/reject",
            json={"reason": "test"},
        ).status_code
        == 403
    )
