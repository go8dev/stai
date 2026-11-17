"""Health check (public) and system status (owner only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from stai.core.errors import ErrorResponse
from stai.core.runtime import Runtime, get_runtime
from stai.system.schemas import HealthStatus, SystemStatus
from stai.system.service import collect_status

router = APIRouter(prefix="/api")


@router.get(
    "/healthz",
    operation_id="healthCheck",
    summary="Health check",
    tags=["health"],
    response_model=HealthStatus,
    response_description="Healthy",
)
async def health_check() -> HealthStatus:
    """Says only that the process is serving. It never touches the database."""
    return HealthStatus(status="ok")


@router.get(
    "/system/status",
    operation_id="getSystemStatus",
    summary="Live checks of the backend, database, market-data reachability and build",
    tags=["system"],
    response_model=SystemStatus,
    response_description="Current status.",
    responses={401: {"model": ErrorResponse, "description": "Not signed in."}},
)
async def get_system_status(runtime: Runtime = Depends(get_runtime)) -> SystemStatus:
    return await collect_status(runtime)
