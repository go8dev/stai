"""Read and verify the audit trail (owner only)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from stai.audit import schemas, service
from stai.core.errors import ErrorResponse
from stai.core.runtime import Runtime, get_runtime

router = APIRouter(prefix="/api", tags=["audit"])

_NOT_SIGNED_IN = {"model": ErrorResponse, "description": "Not signed in."}


@router.get(
    "/audit/events",
    operation_id="listAuditEvents",
    summary="Most recent audit events, newest first",
    response_model=schemas.AuditEventList,
    response_description="Recent events.",
    responses={
        401: _NOT_SIGNED_IN,
        422: {"model": ErrorResponse, "description": "The limit is out of range."},
    },
)
def list_audit_events(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    runtime: Runtime = Depends(get_runtime),
) -> schemas.AuditEventList:
    with runtime.database.session() as db:
        rows, total = service.list_recent(db, limit)
        return schemas.AuditEventList(
            events=[schemas.AuditEvent.model_validate(row) for row in rows], total=total
        )


@router.post(
    "/audit/verify",
    operation_id="verifyAuditTrail",
    summary="Recompute the hash chain and report the first break, if any",
    response_model=schemas.AuditVerification,
    response_description="Verification result.",
    responses={
        401: _NOT_SIGNED_IN,
        403: {"model": ErrorResponse, "description": "CSRF check failed."},
    },
)
def verify_audit_trail(runtime: Runtime = Depends(get_runtime)) -> schemas.AuditVerification:
    with runtime.database.session() as db:
        report = service.verify_trail(db)

    result = report.result
    first_break = result.first_break
    return schemas.AuditVerification(
        ok=result.ok,
        events_checked=result.events_checked,
        first_seq=result.first_seq,
        last_seq=result.last_seq,
        head_hash=result.head_hash,
        first_break=None
        if first_break is None
        else schemas.AuditBreak(
            seq=first_break.seq,
            reason=schemas.AuditBreakReason(first_break.reason),
            detail=first_break.detail,
        ),
        verified_at=report.verified_at,
        duration_ms=report.duration_ms,
    )
