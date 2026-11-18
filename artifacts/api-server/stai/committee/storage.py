"""Run lifecycle, advisory singleton lock, and durable accounting of provider attempts."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select, text

from stai.audit.service import append_event
from stai.committee.models import (
    CommitteeAgent,
    CommitteeCallRecord,
    CommitteeFinding,
    CommitteeRun,
)
from stai.committee.schemas import (
    ROLE_NAMES,
    CommitteeCall,
    CommitteeRunDetail,
    CommitteeRunSummary,
    Evidence,
    Finding,
    Recommendation,
)
from stai.core.time import utcnow
from stai.db.session import Database

LOCK_KEY = 0x535441490003
BENCHMARK = "phase3-owner-benchmark"
MODEL = "gpt-4.1-mini-2025-04-14"
COST_BASIS = (
    "Estimated USD, OpenAI standard text rates verified 18 Nov 2026 at "
    "https://developers.openai.com/api/docs/pricing: "
    "gpt-4.1-mini-2025-04-14 input $0.40/M, output $1.60/M. "
    "Conservative uncached input; excludes account credits/taxes. Model listed deprecated."
)


@contextmanager
def exclusive_run(database: Database):
    """A session-scoped lock survives individual stage commits, releases on disconnect."""
    with database.engine.connect() as connection:
        acquired = connection.scalar(text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY})
        connection.commit()
        try:
            if not acquired:
                raise ValueError("A committee process is already active")
            yield
        finally:
            if acquired:
                connection.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})
                connection.commit()


def recover_interrupted(database: Database) -> None:
    try:
        with exclusive_run(database), database.session() as session:
            for run in session.scalars(
                select(CommitteeRun).where(CommitteeRun.status == "running")
            ):
                run.status = "interrupted"
                run.finished_at = utcnow()
                run.error = (
                    "Process stopped; provider billing may be incomplete. No automatic retry."
                )
                run.cost_usd = None
                append_event(
                    session,
                    event_type="committee.interrupted",
                    actor_type="system",
                    payload={"runId": run.id},
                )
    except ValueError:
        pass  # Another process owns the lock; its running rows are not interrupted.


def claim_benchmark(
    database: Database, snapshot_id: str, symbol: str, market_type: str, evidence: list[Evidence]
) -> str:
    with database.session() as session:
        if session.scalar(select(CommitteeRun.id).where(CommitteeRun.purpose == BENCHMARK)):
            raise ValueError(
                "The single benchmark slot is already used; no further paid run allowed"
            )
        for role_id, name in ROLE_NAMES.items():
            session.merge(
                CommitteeAgent(
                    id=role_id,
                    name=name,
                    mode="deterministic" if role_id in {"quantitative", "execution"} else "model",
                )
            )
        session.flush()
        prior = list(
            session.scalars(
                select(CommitteeRun)
                .where(CommitteeRun.status == "completed")
                .order_by(CommitteeRun.started_at.desc())
                .limit(3)
            )
        )
        memory = [
            f"Previous advisory research only: {r.recommendation.get('thesis', '')[:500]}"
            for r in prior
            if r.recommendation
        ]
        run_id = str(uuid4())
        session.add(
            CommitteeRun(
                id=run_id,
                purpose=BENCHMARK,
                symbol=symbol,
                market_type=market_type,
                snapshot_id=snapshot_id,
                status="running",
                started_at=utcnow(),
                model=MODEL,
                input_tokens=0,
                output_tokens=0,
                cost_usd=Decimal("0"),
                cost_basis=COST_BASIS,
                evidence=[e.model_dump(mode="json", by_alias=True) for e in evidence],
                memory=memory,
            )
        )
        append_event(
            session,
            event_type="committee.started",
            actor_type="owner",
            payload={"runId": run_id, "purpose": BENCHMARK},
        )
        return run_id


def save_finding(database: Database, run_id: str, finding: Finding) -> None:
    with database.session() as session:
        session.add(
            CommitteeFinding(
                run_id=run_id, role_id=finding.role, finding=finding.model_dump(mode="json")
            )
        )


def reserve_call(database: Database, run_id: str, stage: str) -> None:
    """Commit BEFORE network I/O; a crash cannot make a paid attempt invisible."""
    with database.session() as session:
        session.add(
            CommitteeCallRecord(
                run_id=run_id,
                stage=stage,
                model=MODEL,
                input_tokens=None,
                output_tokens=None,
                cost_usd=None,
                duration_ms=0,
                status="attempted",
            )
        )


def finish_call(
    database: Database,
    run_id: str,
    stage: str,
    model: str,
    usage: dict | None,
    duration_ms: int,
    status: str,
) -> None:
    with database.session() as session:
        call = session.get(CommitteeCallRecord, (run_id, stage))
        call.model, call.duration_ms, call.status = model, duration_ms, status
        if usage is not None:
            call.input_tokens = usage.get("input_tokens")
            call.output_tokens = usage.get("output_tokens")
        if model == MODEL and call.input_tokens is not None and call.output_tokens is not None:
            call.cost_usd = (
                Decimal(call.input_tokens) * Decimal("0.40")
                + Decimal(call.output_tokens) * Decimal("1.60")
            ) / Decimal(1_000_000)


def finish_run(
    database: Database,
    run_id: str,
    duration_ms: int,
    recommendation: Recommendation | None,
    error: str | None,
) -> None:
    with database.session() as session:
        run = session.get(CommitteeRun, run_id)
        calls = list(
            session.scalars(select(CommitteeCallRecord).where(CommitteeCallRecord.run_id == run_id))
        )
        run.status = "completed" if error is None else "failed"
        run.finished_at, run.duration_ms, run.error = utcnow(), duration_ms, error
        run.input_tokens = sum(c.input_tokens or 0 for c in calls)
        run.output_tokens = sum(c.output_tokens or 0 for c in calls)
        run.cost_usd = (
            sum((c.cost_usd for c in calls), Decimal("0"))
            if all(c.cost_usd is not None for c in calls)
            else None
        )
        run.recommendation = recommendation.model_dump(mode="json") if recommendation else None
        append_event(
            session,
            event_type=f"committee.{run.status}",
            actor_type="system",
            payload={"runId": run_id, "calls": len(calls)},
        )


def summary(run: CommitteeRun, count: int) -> CommitteeRunSummary:
    result = CommitteeRunSummary(
        **{
            name: getattr(run, name)
            for name in CommitteeRunSummary.model_fields
            if name not in {"action", "finding_count"}
        },
        action=run.recommendation.get("action") if run.recommendation else None,
        finding_count=count,
    )
    if run.status == "running":
        result.cost_usd = None  # An in-flight provider attempt may already be billable.
    return result


def detail(database: Database, run_id: str, now: datetime) -> CommitteeRunDetail | None:
    with database.session() as session:
        run = session.get(CommitteeRun, run_id)
        if run is None:
            return None
        findings = list(
            session.scalars(select(CommitteeFinding).where(CommitteeFinding.run_id == run_id))
        )
        calls = list(
            session.scalars(select(CommitteeCallRecord).where(CommitteeCallRecord.run_id == run_id))
        )
        evidence = [Evidence.model_validate(e) for e in run.evidence]
        return CommitteeRunDetail(
            advisory_only=True,
            **summary(run, len(findings)).model_dump(),
            snapshot_id=run.snapshot_id,
            evidence=evidence,
            findings=[Finding.model_validate(f.finding) for f in findings],
            calls=[CommitteeCall.model_validate(c) for c in calls],
            recommendation=Recommendation.model_validate(run.recommendation)
            if run.recommendation
            else None,
            memory=run.memory,
            evidence_stale=any(
                e.status != "fresh" or (now - e.observed_at).total_seconds() > 60
                for e in evidence
                if e.id == "market"
            ),
        )
