"""Owner-only Strategy Laboratory API; no trading or committee side effects."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from stai.auth.deps import current_auth
from stai.auth.gate import AuthContext
from stai.core.errors import ErrorResponse
from stai.core.runtime import Runtime, get_runtime
from stai.marketdata.okx_market import MarketDataUnavailable
from stai.strategy_lab.schemas import (
    BacktestInput,
    BacktestListItem,
    BacktestResult,
    StrategyLabOverview,
)
from stai.strategy_lab.service import create_run, get_run, list_runs, overview, persist_run

router = APIRouter(
    prefix="/api",
    tags=["strategy-lab"],
    responses={401: {"model": ErrorResponse, "description": "Owner session required."}},
)


@router.get(
    "/strategy-lab",
    operation_id="getStrategyLabOverview",
    response_model=StrategyLabOverview,
    summary="Get the approved strategy setup and recent historical backtests",
)
def get_strategy_lab_overview(
    runtime: Runtime = Depends(get_runtime),
    auth: AuthContext = Depends(current_auth),
) -> StrategyLabOverview:
    with runtime.database.session() as session:
        return overview(session, auth.user.user_id)


@router.get(
    "/strategy-lab/backtests",
    operation_id="listStrategyBacktests",
    response_model=list[BacktestListItem],
    summary="List recent owner Strategy Laboratory runs",
)
def list_strategy_backtests(
    runtime: Runtime = Depends(get_runtime),
    auth: AuthContext = Depends(current_auth),
) -> list[BacktestListItem]:
    with runtime.database.session() as session:
        return list_runs(session, auth.user.user_id)


@router.get(
    "/strategy-lab/backtests/{run_id}",
    operation_id="getStrategyBacktest",
    response_model=BacktestResult,
    responses={404: {"model": ErrorResponse, "description": "Backtest was not found."}},
    summary="Get one saved historical Strategy Laboratory run",
)
def get_strategy_backtest(
    run_id: str,
    runtime: Runtime = Depends(get_runtime),
    auth: AuthContext = Depends(current_auth),
) -> BacktestResult:
    with runtime.database.session() as session:
        result = get_run(session, user_id=auth.user.user_id, run_id=run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Backtest was not found.")
    return result


@router.post(
    "/strategy-lab/backtests",
    operation_id="createStrategyBacktest",
    response_model=BacktestResult,
    status_code=201,
    responses={
        403: {"model": ErrorResponse, "description": "Same-origin CSRF check failed."},
        422: {"model": ErrorResponse, "description": "Backtest inputs are invalid."},
        503: {"model": ErrorResponse, "description": "Historical OKX data is unavailable."},
    },
    summary="Run and save a deterministic OKX historical backtest",
)
async def create_strategy_backtest(
    body: BacktestInput,
    runtime: Runtime = Depends(get_runtime),
    auth: AuthContext = Depends(current_auth),
) -> BacktestResult:
    try:
        result, source_snapshot = await create_run(
            runtime, body=body
        )
    except (MarketDataUnavailable, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Usable closed OKX history is unavailable; no backtest was saved.",
        ) from exc
    with runtime.database.session() as session:
        persist_run(
            session,
            result=result,
            source_snapshot=source_snapshot,
            user_id=auth.user.user_id,
        )
    return result
