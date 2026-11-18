"""Deterministic candidate qualification and owner-gated paper proposals."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from stai.audit.service import append_event
from stai.committee.models import CommitteeFinding, CommitteeRun
from stai.committee.schemas import Recommendation
from stai.core.time import as_utc
from stai.db.models import (
    BotState,
    FundAllocation,
    LedgerEntry,
    MarketSnapshot,
    PaperPosition,
    SetupCandidate,
    TradeProposal,
    TradingPermit,
)
from stai.marketdata.schemas import BookLevel, MarketScannerRow
from stai.marketdata.service import persist_market_rows
from stai.strategies.scanner import enrich_research
from stai.trading.accounting import (
    FeeSchedule,
    FillRejected,
    accounting_reconciles,
    estimate_taker_fill,
)
from stai.trading.ledger import verify_ledger

STRATEGY_VERSION = "btc-regime-pullback-v1"
STRATEGY_THRESHOLD = 70
CANDIDATE_TTL = timedelta(minutes=60)
PROPOSAL_TTL = timedelta(minutes=60)
MAX_PLANNED_LOSS = Decimal("5")
MAX_NOTIONAL = Decimal("200")
MAX_OPEN_POSITIONS = 3
_SCAN_LOCK = 0x5354_4149_0013
_APPROVAL_LOCK = 0x5354_4149_0014


def _candle_recency_ok(row: MarketScannerRow, now: datetime) -> bool:
    for candles, interval, limit in (
        (row.candles, timedelta(hours=1), timedelta(minutes=65)),
        (row.candles_15m, timedelta(minutes=15), timedelta(minutes=30)),
    ):
        complete = [candle for candle in candles if candle.complete]
        if not complete:
            return False
        latest = max(complete, key=lambda candle: candle.opened_at)
        closed_at = latest.opened_at + interval
        age = now - closed_at
        if age < timedelta(0) or age > limit:
            return False
    return True


def _setup_for_side(scores: dict[str, Any], side: str) -> dict[str, Any] | None:
    available = scores.get("scores")
    if not isinstance(available, dict):
        return None
    setup = available.get(side)
    return setup if isinstance(setup, dict) else None


def _candidate_gates(
    row: MarketScannerRow, scores: dict[str, Any], side: str, now: datetime
) -> list[str]:
    failures: list[str] = []
    if row.entry_research is not None:
        return [
            "Revised entries are research-only; score mapping and AI authorization are pending."
        ]
    if row.status != "fresh" or row.exchange_at is None:
        failures.append("Live exchange quote is not fresh.")
    elif not timedelta(0) <= now - as_utc(row.exchange_at) <= timedelta(seconds=60):
        failures.append("Live exchange quote is older than 60 seconds.")
    if row.last_price is None or row.bid is None or row.ask is None:
        failures.append("A current price and two-sided order book are required.")
    elif row.bid <= 0 or row.ask <= row.bid:
        failures.append("The current order book is invalid or crossed.")
    if row.spread_pct is None or row.spread_pct < 0:
        failures.append("A valid spread measurement is required.")
    if row.market_type == "futures" and (row.funding_rate is None or row.next_funding_at is None):
        failures.append("Current futures funding data is required.")
    if not _candle_recency_ok(row, now):
        failures.append("Recent completed 1-hour and 15-minute candles are required.")
    if scores.get("status") != "available":
        failures.append("Deterministic setup scoring is unavailable.")

    setup = _setup_for_side(scores, side)
    if setup is None:
        failures.append("This market type does not support the proposed side.")
        return failures
    try:
        score = Decimal(str(setup.get("score")))
    except Exception:
        score = Decimal("-1")
    if score < STRATEGY_THRESHOLD:
        failures.append(f"Strategy score is below {STRATEGY_THRESHOLD}/100.")

    btc = scores.get("btcRegime")
    expected = "bullish" if side == "long" else "bearish"
    if not isinstance(btc, dict) or btc.get("status") != "fresh" or btc.get("regime") != expected:
        failures.append(f"BTC regime must be fresh and {expected} for this setup.")

    h1 = scores.get("h1Snapshot")
    m15 = scores.get("m15Snapshot")
    if not isinstance(h1, dict) or not isinstance(m15, dict):
        failures.append("Completed-candle indicator snapshots are missing.")
        return failures
    if h1.get("ema_alignment") != expected:
        failures.append(f"The 1-hour EMA trend must be {expected}.")
    if m15.get("ema_alignment") != expected or m15.get("macd_direction") != expected:
        failures.append(f"The 15-minute EMA and MACD must confirm {expected}.")
    candle = m15.get("candle_behavior")
    confirms = (
        {"strong_bull", "rejection_bull"} if side == "long" else {"strong_bear", "rejection_bear"}
    )
    if candle not in confirms:
        failures.append("The completed 15-minute candle has no directional confirmation.")

    try:
        price, ema7, ema99 = (Decimal(str(h1[key])) for key in ("current_price", "ema_7", "ema_99"))
        in_pullback = ema99 <= price <= ema7 if side == "long" else ema7 <= price <= ema99
        if row.last_price is not None:
            live_price = Decimal(str(row.last_price))
            in_pullback = in_pullback and (
                ema99 <= live_price <= ema7 if side == "long" else ema7 <= live_price <= ema99
            )
        if not in_pullback:
            failures.append(
                "The live and completed-candle prices are outside the pullback/bounce zone."
            )
    except Exception:
        failures.append("The 1-hour pullback zone is incomplete.")
    return failures


def _last_completed_open(row: MarketScannerRow, timeframe: str) -> str | None:
    candles = row.candles if timeframe == "1h" else row.candles_15m
    complete = [candle for candle in candles if candle.complete]
    if not complete:
        return None
    return max(complete, key=lambda candle: candle.opened_at).opened_at.isoformat()


def _fingerprint(row: MarketScannerRow, side: str) -> str:
    parts = (
        STRATEGY_VERSION,
        row.symbol,
        row.market_type,
        side,
        _last_completed_open(row, "1h"),
        _last_completed_open(row, "15m"),
    )
    return hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest()


def _candidate_details(
    row: MarketScannerRow, setup: dict[str, Any], scores: dict[str, Any]
) -> dict[str, Any]:
    return {
        "scoreEvidence": scores,
        "entryZoneLow": str(setup.get("entry_zone_low")),
        "entryZoneHigh": str(setup.get("entry_zone_high")),
        "suggestedStop": str(setup.get("stop_loss")),
        "targetLevels": [str(setup.get(key)) for key in ("tp1", "tp2", "tp3")],
        "lastPrice": None if row.last_price is None else str(row.last_price),
        "spreadPct": None if row.spread_pct is None else str(row.spread_pct),
        "fundingRate": None if row.funding_rate is None else str(row.funding_rate),
        "nextFundingAt": (None if row.next_funding_at is None else row.next_funding_at.isoformat()),
        "instrumentId": None if row.instrument is None else row.instrument.instrument_id,
        "riskPolicy": {
            "maxPlannedLossUsdt": str(MAX_PLANNED_LOSS),
            "maxNotionalUsdt": str(MAX_NOTIONAL),
            "maxFuturesLeverage": "2",
            "maxOpenPositions": MAX_OPEN_POSITIONS,
        },
        "screeningNotice": "A qualified rule-based setup is not an AI recommendation or an order.",
    }


def persist_market_scan(
    session: Session, rows: list[MarketScannerRow], *, now: datetime
) -> list[str]:
    """Persist observations and resumable research; revised entries create no trade candidates."""
    moment = as_utc(now)
    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _SCAN_LOCK})
    enrich_research(session, rows, now=moment)
    snapshot_ids = persist_market_rows(session, rows)
    session.flush()
    for row, snapshot_id in zip(rows, snapshot_ids, strict=True):
        scores = row.setup_scores if isinstance(row.setup_scores, dict) else {}
        snapshot = session.get(MarketSnapshot, snapshot_id)
        if snapshot is not None:
            snapshot.details = {
                **snapshot.details,
                "setupScores": scores,
                "entryResearch": row.entry_research.model_dump(mode="json"),
            }
        if row.entry_research is not None:
            continue
        for side in ("long", "short"):
            setup = _setup_for_side(scores, side)
            if setup is None or _candidate_gates(row, scores, side, moment):
                continue
            try:
                score = Decimal(str(setup["score"]))
            except (TypeError, ValueError, ArithmeticError):
                continue
            if not Decimal(STRATEGY_THRESHOLD) <= score <= Decimal("100"):
                continue
            fingerprint = _fingerprint(row, side)
            existing = session.execute(
                select(SetupCandidate).where(SetupCandidate.fingerprint == fingerprint)
            ).scalar_one_or_none()
            if existing is None:
                existing = session.execute(
                    select(SetupCandidate)
                    .where(
                        SetupCandidate.symbol == row.symbol,
                        SetupCandidate.market_type == row.market_type,
                        SetupCandidate.side == side,
                        SetupCandidate.status.in_(["awaiting_ai_authorization", "proposed"]),
                        SetupCandidate.created_at >= moment - CANDIDATE_TTL,
                    )
                    .order_by(SetupCandidate.created_at.desc())
                    .limit(1)
                ).scalar_one_or_none()
            if existing is None:
                candidate = SetupCandidate(
                    id=str(uuid4()),
                    fingerprint=fingerprint,
                    snapshot_id=snapshot_id,
                    symbol=row.symbol,
                    market_type=row.market_type,
                    side=side,
                    score=score,
                    strategy_version=STRATEGY_VERSION,
                    status="awaiting_ai_authorization",
                    created_at=moment,
                    updated_at=moment,
                    details=_candidate_details(row, setup, scores),
                )
                session.add(candidate)
                session.flush()
                append_event(
                    session,
                    event_type="setup_candidate.qualified",
                    actor_type="system",
                    payload={
                        "candidateId": candidate.id,
                        "snapshotId": snapshot_id,
                        "symbol": row.symbol,
                        "marketType": row.market_type,
                        "side": side,
                        "score": str(score),
                        "strategyVersion": STRATEGY_VERSION,
                    },
                    occurred_at=moment,
                )
                existing = candidate
            row.candidate_id = existing.id
            row.candidate_status = existing.status
    return snapshot_ids


def _snapshot_books(snapshot: MarketSnapshot) -> tuple[list[BookLevel], list[BookLevel]]:
    return (
        [BookLevel.model_validate(level) for level in snapshot.details.get("bids", [])],
        [BookLevel.model_validate(level) for level in snapshot.details.get("asks", [])],
    )


def _capacity_checks(
    session: Session,
    *,
    candidate: SetupCandidate,
    notional: Decimal,
    leverage: Decimal,
    now: datetime,
) -> list[str]:
    failures: list[str] = []
    ledger = verify_ledger(session)
    if not ledger.ok or not accounting_reconciles(session):
        failures.append("Paper ledger or accounting reconciliation is not clear.")
    allocations = {
        allocation.market_type: allocation
        for allocation in session.execute(select(FundAllocation)).scalars().all()
    }
    allocation = allocations.get(candidate.market_type)
    if allocation is None:
        failures.append("The paper fund allocation is unavailable.")
    else:
        cash = sum(
            (
                entry.amount
                for entry in session.execute(
                    select(LedgerEntry).where(LedgerEntry.market_type == candidate.market_type)
                ).scalars()
            ),
            Decimal("0"),
        )
        reserved = Decimal("0")
        permits = session.execute(
            select(TradingPermit).where(
                TradingPermit.market_type == candidate.market_type,
                TradingPermit.consumed.is_(False),
                TradingPermit.expires_at > now,
            )
        ).scalars()
        for permit in permits:
            reserved += (
                permit.max_notional
                if candidate.market_type == "spot"
                else permit.max_notional / permit.leverage
            )
        positions = (
            session.execute(select(PaperPosition).where(PaperPosition.state == "open"))
            .scalars()
            .all()
        )
        collateral = sum(
            (
                position.entry_price * position.quantity / position.leverage
                for position in positions
                if position.market_type == candidate.market_type == "futures"
            ),
            Decimal("0"),
        )
        required = notional if candidate.market_type == "spot" else notional / leverage
        if required + reserved + collateral > cash:
            failures.append(
                "The market allocation cannot cover this proposal and existing reservations."
            )

    open_positions = (
        session.execute(select(PaperPosition).where(PaperPosition.state == "open")).scalars().all()
    )
    permits = (
        session.execute(
            select(TradingPermit).where(
                TradingPermit.consumed.is_(False),
                TradingPermit.expires_at > now,
            )
        )
        .scalars()
        .all()
    )
    if len(open_positions) + len(permits) >= MAX_OPEN_POSITIONS:
        failures.append("The maximum of three open or reserved positions would be exceeded.")
    instrument = candidate.symbol if candidate.market_type == "spot" else f"{candidate.symbol}:USDT"
    if any(position.instrument == instrument for position in open_positions) or any(
        permit.instrument == instrument for permit in permits
    ):
        failures.append("This instrument already has an open position or unused approval.")

    bot = session.get(BotState, candidate.market_type)
    if (
        bot is None
        or bot.state.get("status") != "running"
        or bot.state.get("dryRun") is not True
        or bot.state.get("reconciliation") != "clear"
        or bot.state.get("ledgerVerified") is not True
        or not timedelta(0) <= now - as_utc(bot.saved_at) <= timedelta(seconds=60)
    ):
        failures.append("The paper bot is stopped, stale, or not reconciled.")
    return failures


def _evaluate_terms(
    session: Session,
    *,
    candidate: SetupCandidate,
    snapshot: MarketSnapshot,
    side: str,
    entry: Decimal,
    stop: Decimal,
    target: Decimal,
    notional: Decimal,
    leverage: Decimal,
    now: datetime,
) -> dict[str, Any]:
    failures: list[str] = []
    if candidate.status not in {"awaiting_ai_authorization", "proposed"}:
        failures.append("Candidate is no longer eligible for a proposal.")
    if (
        snapshot.status != "fresh"
        or snapshot.exchange_at is None
        or not (timedelta(0) <= now - as_utc(snapshot.exchange_at) <= timedelta(seconds=60))
    ):
        failures.append("Current OKX evidence is not fresh.")
    if snapshot.last_price is None or snapshot.bid is None or snapshot.ask is None:
        failures.append("Current price and two-sided quote are required.")
    if side != candidate.side:
        failures.append("Committee direction does not match the qualified setup.")
    if candidate.market_type == "spot" and (side != "long" or leverage != Decimal("1")):
        failures.append("Spot proposals must be unleveraged longs.")
    if candidate.market_type == "futures" and not Decimal("1") <= leverage <= Decimal("2"):
        failures.append("Futures leverage must be between 1x and 2x.")
    if not Decimal("0") < notional <= MAX_NOTIONAL:
        failures.append("Notional exceeds the approved USDT cap.")
    if not (
        (side == "long" and stop < entry < target) or (side == "short" and target < entry < stop)
    ):
        failures.append("Entry, stop, and target are not directionally coherent.")
    low = Decimal(str(candidate.details.get("entryZoneLow", "0")))
    high = Decimal(str(candidate.details.get("entryZoneHigh", "0")))
    if not low <= entry <= high:
        failures.append("Committee entry is outside the recorded strategy entry zone.")
    if snapshot.last_price is not None and not low <= snapshot.last_price <= high:
        failures.append("Current market price has left the recorded strategy entry zone.")

    try:
        bids, asks = _snapshot_books(snapshot)
        fill = estimate_taker_fill(
            side=side,
            quantity=notional / entry,
            bids=bids,
            asks=asks,
            observed_at=snapshot.exchange_at or now,
        )
    except (FillRejected, ValueError, ArithmeticError) as exc:
        failures.append(f"Order-book depth check failed: {exc}.")
        fill = None

    price_risk = notional * abs(entry - stop) / entry if entry > 0 else Decimal("0")
    fee_rate = FeeSchedule().rate(candidate.market_type, "taker")
    fees = notional * fee_rate * 2
    spread_cost = Decimal(str(snapshot.details.get("spreadPct") or "0")) * notional / 100
    slippage_cost = fill.slippage_pct * notional * 2 / 100 if fill is not None else Decimal("0")
    funding_cost = Decimal("0")
    funding_raw = snapshot.details.get("fundingRate")
    funding_at_raw = snapshot.details.get("nextFundingAt")
    if candidate.market_type == "futures":
        if funding_raw is None or funding_at_raw is None:
            failures.append("Current funding rate and settlement time are required.")
        else:
            funding = Decimal(str(funding_raw))
            funding_at = datetime.fromisoformat(str(funding_at_raw))
            if funding_at.tzinfo is None:
                funding_at = funding_at.replace(tzinfo=UTC)
            adverse = funding > 0 if side == "long" else funding < 0
            if adverse and now < as_utc(funding_at) <= now + PROPOSAL_TTL:
                funding_cost = abs(funding) * notional
    estimated_cost = fees + spread_cost + slippage_cost + funding_cost
    planned_loss = price_risk + estimated_cost
    gross_reward = notional * abs(target - entry) / entry if entry > 0 else Decimal("0")
    net_reward = gross_reward - estimated_cost
    if planned_loss > MAX_PLANNED_LOSS:
        failures.append("Planned stop loss plus estimated trading costs exceeds 5 USDT.")
    if net_reward <= 0:
        failures.append("Estimated fees, spread, slippage, and funding consume the target reward.")
    if failures:
        raise ValueError(" ".join(failures))
    capacity_failures = _capacity_checks(
        session, candidate=candidate, notional=notional, leverage=leverage, now=now
    )
    if capacity_failures:
        raise ValueError(" ".join(capacity_failures))
    return {
        "priceRiskUsdt": str(price_risk),
        "feesUsdt": str(fees),
        "spreadCostUsdt": str(spread_cost),
        "slippageCostUsdt": str(slippage_cost),
        "fundingCostUsdt": str(funding_cost),
        "estimatedCostUsdt": str(estimated_cost),
        "plannedLossUsdt": str(planned_loss),
        "netTargetRewardUsdt": str(net_reward),
        "spreadPct": str(fill.spread_pct if fill else 0),
        "slippagePct": str(fill.slippage_pct if fill else 0),
        "visibleBookNotionalUsdt": str(fill.visible_notional if fill else 0),
        "riskChecksPassed": [
            "fresh market evidence",
            "strategy direction and entry zone",
            "position size and leverage",
            "book depth, spread, fees, and funding",
            "paper allocation, ledger, and bot reconciliation",
        ],
    }


def create_proposal_from_committee_run(
    session: Session,
    *,
    candidate_id: str,
    run_id: str,
    now: datetime,
) -> TradeProposal | None:
    """Create a proposal only from a completed non-abstaining run on the candidate snapshot."""
    moment = as_utc(now)
    candidate = session.execute(
        select(SetupCandidate).where(SetupCandidate.id == candidate_id).with_for_update()
    ).scalar_one_or_none()
    run = session.get(CommitteeRun, run_id)
    if candidate is None or run is None:
        raise ValueError("Candidate or committee run was not found.")
    if candidate.strategy_version != STRATEGY_VERSION:
        raise ValueError("This research strategy is not authorized for proposal creation.")
    if run.status != "completed" or run.recommendation is None:
        raise ValueError("Only a completed committee review can create a proposal.")
    if (
        candidate.snapshot_id != run.snapshot_id
        or candidate.symbol != run.symbol
        or candidate.market_type != run.market_type
    ):
        raise ValueError("Committee review must use the candidate's exact market evidence.")
    if candidate.status not in {"awaiting_ai_authorization", "proposed"}:
        raise ValueError("Candidate is no longer open for committee review.")
    findings = (
        session.execute(select(CommitteeFinding).where(CommitteeFinding.run_id == run_id))
        .scalars()
        .all()
    )
    if {finding.role_id for finding in findings} != {
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
    }:
        raise ValueError("All ten committee roles must complete their review.")
    evidence = run.evidence or []
    if not evidence or any(item.get("status") != "fresh" for item in evidence):
        raise ValueError("Committee evidence must be complete and fresh.")
    evidence_ids = {str(item.get("id")) for item in evidence}
    if len(evidence_ids) != len(evidence):
        raise ValueError("Committee evidence identifiers must be unique.")
    for item in evidence:
        observed = item.get("observedAt", item.get("observed_at"))
        if not observed:
            raise ValueError("Committee evidence timestamps are required.")
        observed_at = datetime.fromisoformat(str(observed).replace("Z", "+00:00"))
        if not timedelta(0) <= moment - as_utc(observed_at) <= timedelta(seconds=60):
            raise ValueError("Committee evidence is older than 60 seconds.")
    recommendation = Recommendation.model_validate(run.recommendation)
    if not set(recommendation.evidence_ids).issubset(evidence_ids):
        raise ValueError("Committee recommendation cites evidence that was not captured.")
    market = next((item for item in evidence if item.get("id") == "market"), None)
    if market is None or candidate.snapshot_id not in str(market.get("summary", "")):
        raise ValueError("The market evidence does not identify the candidate's exact snapshot.")
    market_data = market.get("data")
    market_scores = market_data.get("setupScores") if isinstance(market_data, dict) else None
    reviewed_setup = (
        _setup_for_side(market_scores, candidate.side) if isinstance(market_scores, dict) else None
    )
    if reviewed_setup is None or Decimal(str(reviewed_setup.get("score"))) != candidate.score:
        raise ValueError("The committee reviewed different scanner score evidence.")
    for finding in findings:
        finding_evidence = finding.finding.get("evidenceIds", finding.finding.get("evidence_ids"))
        if not finding_evidence or not set(finding_evidence).issubset(evidence_ids):
            raise ValueError("A committee role cited evidence that was not captured.")
    if recommendation.action == "abstain" or recommendation.terms is None:
        raise ValueError("Abstentions and incomplete reviews cannot become proposals.")
    side = recommendation.action.removeprefix("research_")
    if side != candidate.side:
        raise ValueError("Committee direction does not match the scanner candidate.")
    if session.execute(
        select(TradeProposal.id).where(
            (TradeProposal.candidate_id == candidate.id)
            | (TradeProposal.committee_run_id == run.id)
        )
    ).first():
        raise ValueError("This candidate or committee run already has a proposal.")
    snapshot = session.get(MarketSnapshot, candidate.snapshot_id)
    if snapshot is None:
        raise ValueError("Candidate market evidence is unavailable.")
    terms = recommendation.terms
    try:
        risk_details = _evaluate_terms(
            session,
            candidate=candidate,
            snapshot=snapshot,
            side=side,
            entry=terms.entry,
            stop=terms.stop,
            target=terms.target,
            notional=terms.notional_usdt,
            leverage=Decimal(terms.leverage),
            now=moment,
        )
    except ValueError as exc:
        candidate.status = "vetoed"
        candidate.updated_at = moment
        append_event(
            session,
            event_type="setup_candidate.vetoed",
            actor_type="system",
            payload={
                "candidateId": candidate.id,
                "committeeRunId": run.id,
                "snapshotId": snapshot.id,
                "reason": str(exc),
            },
            occurred_at=moment,
        )
        session.flush()
        return None
    proposal = TradeProposal(
        id=str(uuid4()),
        candidate_id=candidate.id,
        committee_run_id=run.id,
        snapshot_id=snapshot.id,
        instrument=(
            candidate.symbol if candidate.market_type == "spot" else f"{candidate.symbol}:USDT"
        ),
        market_type=candidate.market_type,
        side=side,
        status="pending",
        entry_price=terms.entry,
        stop_price=terms.stop,
        target_price=terms.target,
        notional_usdt=terms.notional_usdt,
        leverage=Decimal(terms.leverage),
        planned_loss_usdt=Decimal(risk_details["plannedLossUsdt"]),
        estimated_cost_usdt=Decimal(risk_details["estimatedCostUsdt"]),
        reward_risk=(
            Decimal(risk_details["netTargetRewardUsdt"]) / Decimal(risk_details["plannedLossUsdt"])
        ),
        expires_at=moment + PROPOSAL_TTL,
        created_at=moment,
        details={
            "thesis": recommendation.thesis,
            "confidence": recommendation.confidence,
            "supporting": recommendation.supporting,
            "opposing": recommendation.opposing,
            "uncertainties": recommendation.uncertainties,
            "evidenceIds": recommendation.evidence_ids,
            "risk": risk_details,
        },
    )
    session.add(proposal)
    candidate.status = "proposed"
    candidate.updated_at = moment
    session.flush()
    append_event(
        session,
        event_type="trade_proposal.created",
        actor_type="system",
        payload={
            "proposalId": proposal.id,
            "candidateId": candidate.id,
            "committeeRunId": run.id,
            "snapshotId": snapshot.id,
            "side": side,
            "entry": str(terms.entry),
            "stop": str(terms.stop),
            "target": str(terms.target),
            "notionalUsdt": str(terms.notional_usdt),
            "leverage": terms.leverage,
            "plannedLossUsdt": str(proposal.planned_loss_usdt),
        },
        occurred_at=moment,
    )
    return proposal


def list_proposal_center(session: Session, *, now: datetime) -> tuple[list[Any], list[Any]]:
    """Expire stale owner decisions and return recent candidates and proposals."""
    moment = as_utc(now)
    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _SCAN_LOCK})
    candidates = (
        session.execute(
            select(SetupCandidate)
            .where(SetupCandidate.created_at >= moment - timedelta(hours=24))
            .order_by(SetupCandidate.created_at.desc())
            .limit(100)
        )
        .scalars()
        .all()
    )
    for candidate in candidates:
        if (
            candidate.status == "awaiting_ai_authorization"
            and candidate.created_at + CANDIDATE_TTL <= moment
        ):
            candidate.status = "expired"
            candidate.updated_at = moment
            append_event(
                session,
                event_type="setup_candidate.expired",
                actor_type="system",
                payload={"candidateId": candidate.id},
                occurred_at=moment,
            )
    proposals = (
        session.execute(
            select(TradeProposal)
            .where(TradeProposal.created_at >= moment - timedelta(days=7))
            .order_by(TradeProposal.created_at.desc())
            .limit(100)
        )
        .scalars()
        .all()
    )
    for proposal in proposals:
        if proposal.status == "pending" and proposal.expires_at <= moment:
            proposal.status = "expired"
            proposal.decided_at = moment
            proposal.decision_reason = "Owner decision window expired."
            candidate = session.get(SetupCandidate, proposal.candidate_id)
            if candidate is not None:
                candidate.status = "expired"
                candidate.updated_at = moment
            append_event(
                session,
                event_type="trade_proposal.expired",
                actor_type="system",
                payload={"proposalId": proposal.id, "candidateId": proposal.candidate_id},
                occurred_at=moment,
            )
    return candidates, proposals


def decide_proposal(
    session: Session,
    *,
    proposal_id: str,
    owner_id: str,
    approve: bool,
    reason: str,
    now: datetime,
    current_snapshot: MarketSnapshot | None = None,
) -> TradeProposal:
    """Record a rejection or issue one revalidated, exact-term paper permit."""
    moment = as_utc(now)
    proposal = session.execute(
        select(TradeProposal).where(TradeProposal.id == proposal_id).with_for_update()
    ).scalar_one_or_none()
    if proposal is None:
        raise LookupError("Proposal was not found.")
    if proposal.status != "pending":
        raise ValueError("Proposal is no longer pending.")
    if proposal.expires_at <= moment:
        raise ValueError("Proposal has expired.")
    candidate = session.execute(
        select(SetupCandidate).where(SetupCandidate.id == proposal.candidate_id).with_for_update()
    ).scalar_one_or_none()
    if candidate is None:
        raise ValueError("Candidate evidence was not found.")
    if not approve:
        proposal.status = "rejected"
        proposal.decided_at = moment
        proposal.decided_by = owner_id
        proposal.decision_reason = reason.strip() or "Rejected by owner."
        candidate.status = "rejected"
        candidate.updated_at = moment
        append_event(
            session,
            event_type="trade_proposal.rejected",
            actor_type="owner",
            actor_id=owner_id,
            payload={
                "proposalId": proposal.id,
                "candidateId": candidate.id,
                "reason": proposal.decision_reason,
            },
            occurred_at=moment,
        )
        return proposal

    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _APPROVAL_LOCK})
    snapshot = current_snapshot or session.get(MarketSnapshot, proposal.snapshot_id)
    if snapshot is None:
        raise ValueError("Fresh market evidence is unavailable.")
    try:
        risk_details = _evaluate_terms(
            session,
            candidate=candidate,
            snapshot=snapshot,
            side=proposal.side,
            entry=proposal.entry_price,
            stop=proposal.stop_price,
            target=proposal.target_price,
            notional=proposal.notional_usdt,
            leverage=proposal.leverage,
            now=moment,
        )
    except ValueError as exc:
        reason = f"Risk revalidation veto: {exc}"
        proposal.status = "vetoed"
        proposal.decided_at = moment
        proposal.decided_by = owner_id
        proposal.decision_reason = reason
        candidate.status = "vetoed"
        candidate.updated_at = moment
        append_event(
            session,
            event_type="trade_proposal.vetoed",
            actor_type="system",
            payload={
                "proposalId": proposal.id,
                "candidateId": candidate.id,
                "ownerId": owner_id,
                "reason": reason,
                "snapshotId": snapshot.id,
            },
            occurred_at=moment,
        )
        session.flush()
        return proposal
    low = Decimal(str(candidate.details.get("entryZoneLow", "0")))
    high = Decimal(str(candidate.details.get("entryZoneHigh", "0")))
    drift = (
        min(
            abs(proposal.entry_price - low),
            abs(high - proposal.entry_price),
        )
        / proposal.entry_price
        * 100
    )
    permit = TradingPermit(
        id=str(uuid4()),
        instrument=proposal.instrument,
        market_type=proposal.market_type,
        side=proposal.side,
        max_notional=proposal.notional_usdt,
        approved_price=proposal.entry_price,
        max_price_drift_pct=drift,
        leverage=proposal.leverage,
        stop_price=proposal.stop_price,
        target_price=proposal.target_price,
        approved_at=moment,
        expires_at=proposal.expires_at,
        consumed=False,
    )
    session.add(permit)
    session.flush()
    proposal.status = "approved"
    proposal.permit_id = permit.id
    proposal.decided_at = moment
    proposal.decided_by = owner_id
    proposal.decision_reason = reason.strip() or "Approved by owner for paper mode."
    proposal.details = {**proposal.details, "approvalRisk": risk_details}
    candidate.status = "approved"
    candidate.updated_at = moment
    session.flush()
    append_event(
        session,
        event_type="trade_proposal.approved",
        actor_type="owner",
        actor_id=owner_id,
        payload={
            "proposalId": proposal.id,
            "candidateId": candidate.id,
            "permitId": permit.id,
            "marketType": proposal.market_type,
            "instrument": proposal.instrument,
            "side": proposal.side,
            "notionalUsdt": str(proposal.notional_usdt),
            "approvedPrice": str(proposal.entry_price),
            "maxPriceDriftPct": str(drift),
            "expiresAt": proposal.expires_at.isoformat(),
        },
        occurred_at=moment,
    )
    append_event(
        session,
        event_type="trading_permit.issued",
        actor_type="owner",
        actor_id=owner_id,
        payload={
            "permitId": permit.id,
            "proposalId": proposal.id,
            "candidateId": candidate.id,
            "instrument": permit.instrument,
            "marketType": permit.market_type,
            "side": permit.side,
            "notionalUsdt": str(permit.max_notional),
            "approvedPrice": str(permit.approved_price),
            "leverage": str(permit.leverage),
            "stop": str(permit.stop_price),
            "target": str(permit.target_price),
            "expiresAt": permit.expires_at.isoformat(),
        },
        occurred_at=moment,
    )
    return proposal
