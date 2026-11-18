"""Owner-protected, read-only research endpoints. No paid-run mutation is exposed."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select

from stai.committee.models import CommitteeFinding, CommitteeRun
from stai.committee.schemas import (
    ROLE_NAMES,
    CommitteeOverview,
    CommitteeRunDetail,
    RoleDefinition,
)
from stai.committee.storage import detail, summary
from stai.core.errors import ErrorResponse
from stai.core.runtime import Runtime, get_runtime

router = APIRouter(
    prefix="/api/committee",
    tags=["committee"],
    responses={401: {"model": ErrorResponse, "description": "Owner session required"}},
)


@router.get("", operation_id="getCommitteeOverview", response_model=CommitteeOverview)
def get_committee_overview(runtime: Runtime = Depends(get_runtime)) -> CommitteeOverview:
    with runtime.database.session() as session:
        runs = list(
            session.scalars(select(CommitteeRun).order_by(CommitteeRun.started_at.desc()).limit(50))
        )
        counts = dict(
            session.execute(
                select(CommitteeFinding.run_id, func.count()).group_by(CommitteeFinding.run_id)
            ).all()
        )
        return CommitteeOverview(
            paid_automation_enabled=False,
            manual_paid_runs_enabled=False,
            entry_gate="closed",
            roles=[
                RoleDefinition(
                    id=k,
                    name=v,
                    mode="deterministic" if k in {"quantitative", "execution"} else "model",
                )
                for k, v in ROLE_NAMES.items()
            ],
            runs=[summary(r, counts.get(r.id, 0)) for r in runs],
            benchmark_state=runs[0].status if runs else "not_started",
            limits_status="Awaiting owner approval; no threshold or daily caps selected",
            next_step="Review benchmark cost and duration, then approve limits in conversation."
            if runs
            else "The single workspace benchmark has not run yet.",
        )


@router.get(
    "/{run_id}",
    operation_id="getCommitteeRun",
    response_model=CommitteeRunDetail,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def get_committee_run(run_id: str, runtime: Runtime = Depends(get_runtime)) -> CommitteeRunDetail:
    result = detail(runtime.database, run_id, runtime.now())
    if result is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return result
