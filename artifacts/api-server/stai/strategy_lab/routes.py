"""Owner-only Strategy Laboratory API; no trading or committee side effects."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from stai.auth.deps import current_auth
from stai.auth.gate import AuthContext
from stai.core.errors import ErrorResponse
from stai.core.runtime import Runtime, get_runtime
from stai.marketdata.okx_market import MarketDataUnavailable
from stai.strategy_lab.historical_review import (
    HistoricalReviewBudgetExceeded,
    HistoricalReviewProviderError,
    HistoricalReviewUnavailable,
)
from stai.strategy_lab.schemas import (
    BacktestInput,
    BacktestListItem,
    BacktestResult,
    HistoricalReviewInput,
    HistoricalReviewResponse,
    StrategyLabOverview,
)
from stai.strategy_lab.service import (
    create_historical_review,
    create_run,
    get_run,
    list_historical_reviews,
    list_runs,
    overview,
    persist_run,
)
from stai.strategy_lab.structural_schemas import (
    StructuralBacktestInput,
    StructuralBacktestResult,
    StructuralLabOverview,
    StructuralRunListItem,
)
from stai.strategy_lab.structural_service import StructuralWindowLocked, StructuralWindowUsed
from stai.strategy_lab.structural_service import create_run as create_structural_run
from stai.strategy_lab.structural_service import get_run as get_structural_run
from stai.strategy_lab.structural_service import list_runs as list_structural_runs
from stai.strategy_lab.structural_service import overview as structural_overview
from stai.strategy_lab.structural_service import persist_run as persist_structural_run

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
        return overview(session, auth.user.user_id, runtime)


@router.get(
    "/strategy-lab/structural",
    operation_id="getStructuralChallengerOverview",
    response_model=StructuralLabOverview,
    summary="Get the isolated structural pullback research setup",
)
def get_structural_challenger_overview(
    runtime: Runtime = Depends(get_runtime),
    auth: AuthContext = Depends(current_auth),
) -> StructuralLabOverview:
    with runtime.database.session() as session:
        return structural_overview(session, auth.user.user_id, runtime.now())


@router.get(
    "/strategy-lab/structural/backtests",
    operation_id="listStructuralChallengerBacktests",
    response_model=list[StructuralRunListItem],
    summary="List saved structural pullback research runs",
)
def list_structural_challenger_backtests(
    runtime: Runtime = Depends(get_runtime),
    auth: AuthContext = Depends(current_auth),
) -> list[StructuralRunListItem]:
    with runtime.database.session() as session:
        return list_structural_runs(session, auth.user.user_id)


@router.get(
    "/strategy-lab/structural/backtests/{run_id}",
    operation_id="getStructuralChallengerBacktest",
    response_model=StructuralBacktestResult,
    responses={
        404: {"model": ErrorResponse, "description": "Research run was not found."},
        422: {"model": ErrorResponse, "description": "Invalid run identifier."},
    },
    summary="Get one saved structural pullback research run",
)
def get_structural_challenger_backtest(
    run_id: str,
    runtime: Runtime = Depends(get_runtime),
    auth: AuthContext = Depends(current_auth),
) -> StructuralBacktestResult:
    with runtime.database.session() as session:
        result = get_structural_run(session, user_id=auth.user.user_id, run_id=run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Research run was not found.")
    return result


@router.post(
    "/strategy-lab/structural/backtests",
    operation_id="createStructuralChallengerBacktest",
    response_model=StructuralBacktestResult,
    status_code=201,
    responses={
        403: {"model": ErrorResponse, "description": "Same-origin CSRF check failed."},
        409: {
            "model": ErrorResponse,
            "description": "The future validation window is locked or already used.",
        },
        422: {"model": ErrorResponse, "description": "Research inputs are invalid."},
        503: {"model": ErrorResponse, "description": "Historical OKX data is unavailable."},
    },
    summary="Run the isolated structural pullback historical challenger",
)
async def create_structural_challenger_backtest(
    body: StructuralBacktestInput,
    runtime: Runtime = Depends(get_runtime),
    auth: AuthContext = Depends(current_auth),
) -> StructuralBacktestResult:
    try:
        if body.sample_period == "future_validation":
            # Holdout check and persistence share this transaction so concurrent requests
            # cannot consume the same instrument's one-time validation sample twice.
            lock_key = f"stai-structural-validation:{auth.user.user_id}:{body.symbol}"
            with runtime.database.session() as session:
                session.execute(
                    text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
                    {"lock_key": lock_key},
                )
                result, source_snapshot = await create_structural_run(
                    runtime,
                    user_id=auth.user.user_id,
                    body=body,
                )
                persist_structural_run(
                    session,
                    result=result,
                    source_snapshot=source_snapshot,
                    user_id=auth.user.user_id,
                )
        else:
            result, source_snapshot = await create_structural_run(
                runtime,
                user_id=auth.user.user_id,
                body=body,
            )
            with runtime.database.session() as session:
                persist_structural_run(
                    session,
                    result=result,
                    source_snapshot=source_snapshot,
                    user_id=auth.user.user_id,
                )
    except StructuralWindowLocked as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except StructuralWindowUsed as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (MarketDataUnavailable, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Usable closed OKX history is unavailable; no research run was saved.",
        ) from exc
    return result


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
    responses={
        404: {"model": ErrorResponse, "description": "Backtest was not found."},
        422: {"model": ErrorResponse, "description": "Backtest identifier is invalid."},
    },
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


@router.get(
    "/strategy-lab/backtests/{run_id}/reviews",
    operation_id="listStrategyBacktestReviews",
    response_model=list[HistoricalReviewResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Backtest was not found."},
        422: {"model": ErrorResponse, "description": "Backtest identifier is invalid."},
    },
    summary="List completed historical AI reviews for one saved run",
)
def list_strategy_backtest_reviews(
    run_id: str,
    runtime: Runtime = Depends(get_runtime),
    auth: AuthContext = Depends(current_auth),
) -> list[HistoricalReviewResponse]:
    with runtime.database.session() as session:
        reviews = list_historical_reviews(session, user_id=auth.user.user_id, run_id=run_id)
    if reviews is None:
        raise HTTPException(status_code=404, detail="Backtest was not found.")
    return reviews


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
        result, source_snapshot = await create_run(runtime, body=body)
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


@router.post(
    "/strategy-lab/backtests/{run_id}/reviews",
    operation_id="createStrategyBacktestReview",
    response_model=HistoricalReviewResponse,
    status_code=201,
    responses={
        403: {"model": ErrorResponse, "description": "Same-origin CSRF check failed."},
        404: {"model": ErrorResponse, "description": "Backtest was not found."},
        409: {"model": ErrorResponse, "description": "Historical AI review is not authorized."},
        422: {"model": ErrorResponse, "description": "Question or saved evidence is invalid."},
        429: {"model": ErrorResponse, "description": "The configured review budget is exhausted."},
        502: {
            "model": ErrorResponse,
            "description": "The provider did not return a usable review.",
        },
    },
    summary="Ask an authorized AI model about one immutable historical run",
)
def create_strategy_backtest_review(
    run_id: str,
    body: HistoricalReviewInput,
    runtime: Runtime = Depends(get_runtime),
    auth: AuthContext = Depends(current_auth),
) -> HistoricalReviewResponse:
    try:
        response = create_historical_review(
            runtime,
            user_id=auth.user.user_id,
            run_id=run_id,
            question=body.question,
        )
    except HistoricalReviewUnavailable as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except HistoricalReviewBudgetExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except HistoricalReviewProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if response is None:
        raise HTTPException(status_code=404, detail="Backtest was not found.")
    return response
