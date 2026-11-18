"""Historical data collection, persistence and owner-scoped Strategy Lab reads."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from stai.core.runtime import Runtime
from stai.marketdata.okx_market import MarketDataUnavailable
from stai.marketdata.schemas import CandlePoint
from stai.strategy_lab.engine import (
    canonical_data_hash,
    run_backtest,
    strategy_configuration,
)
from stai.strategy_lab.historical_review import (
    request_historical_review,
)
from stai.strategy_lab.models import StrategyBacktestReview, StrategyBacktestRun
from stai.strategy_lab.schemas import (
    BacktestInput,
    BacktestListItem,
    BacktestResult,
    HistoricalReviewAnswer,
    HistoricalReviewResponse,
    StrategyLabOverview,
    StrategyLabStatus,
)
from stai.strategy_lab.structural_engine import (
    STRATEGY_VERSION as STRUCTURAL_STRATEGY_VERSION,
)


def _status(runtime: Runtime) -> StrategyLabStatus:
    enabled = runtime.settings.historical_review_ready
    return StrategyLabStatus(
        paid_committee_review_enabled=False,
        historical_ai_review_enabled=enabled,
        trading_enabled=False,
        proposal_creation_enabled=False,
        notice=(
            "Manual historical AI review is enabled under the configured budget. It cannot "
            "change backtest results or create proposals or orders."
            if enabled
            else "Historical AI review is disabled until a supported model, token prices, and "
            "per-run and daily spending caps are authorized."
        ),
    )


def _result(row: StrategyBacktestRun) -> BacktestResult:
    return BacktestResult.model_validate(row.result)


def _list_item(row: StrategyBacktestRun) -> BacktestListItem:
    result = _result(row)
    total = sum(segment.metrics.trade_count for segment in result.segments)
    return BacktestListItem(
        id=row.id,
        created_at=row.created_at,
        symbol=row.symbol,
        requested_days=row.requested_days,
        strategy_version=row.strategy_version,
        data_sha256=row.data_sha256,
        trade_count=total,
        development_end=result.development_end,
        out_of_sample_start=result.out_of_sample_start,
    )


def overview(session: Session, user_id: str, runtime: Runtime) -> StrategyLabOverview:
    rows = session.execute(
        select(StrategyBacktestRun)
        .where(
            StrategyBacktestRun.user_id == user_id,
            StrategyBacktestRun.strategy_version != STRUCTURAL_STRATEGY_VERSION,
        )
        .order_by(StrategyBacktestRun.created_at.desc())
        .limit(20)
    ).scalars()
    return StrategyLabOverview(
        strategy=strategy_configuration(),
        status=_status(runtime),
        recent_runs=[_list_item(row) for row in rows],
    )


def list_runs(session: Session, user_id: str) -> list[BacktestListItem]:
    rows = session.execute(
        select(StrategyBacktestRun)
        .where(
            StrategyBacktestRun.user_id == user_id,
            StrategyBacktestRun.strategy_version != STRUCTURAL_STRATEGY_VERSION,
        )
        .order_by(StrategyBacktestRun.created_at.desc())
        .limit(20)
    ).scalars()
    return [_list_item(row) for row in rows]


def get_run(session: Session, *, user_id: str, run_id: str) -> BacktestResult | None:
    row = session.execute(
        select(StrategyBacktestRun).where(
            StrategyBacktestRun.id == run_id,
            StrategyBacktestRun.user_id == user_id,
            StrategyBacktestRun.strategy_version != STRUCTURAL_STRATEGY_VERSION,
        )
    ).scalar_one_or_none()
    return _result(row) if row is not None else None


def get_run_record(session: Session, *, user_id: str, run_id: str) -> StrategyBacktestRun | None:
    return session.execute(
        select(StrategyBacktestRun).where(
            StrategyBacktestRun.id == run_id,
            StrategyBacktestRun.user_id == user_id,
            StrategyBacktestRun.strategy_version != STRUCTURAL_STRATEGY_VERSION,
        )
    ).scalar_one_or_none()


def create_historical_review(
    runtime: Runtime,
    *,
    user_id: str,
    run_id: str,
    question: str,
) -> HistoricalReviewResponse | None:
    with runtime.database.session() as session:
        row = get_run_record(session, user_id=user_id, run_id=run_id)
        if row is None:
            return None
        result = _result(row)
        snapshot = row.source_snapshot
        data_sha256 = row.data_sha256
    return request_historical_review(
        runtime.database,
        settings=runtime.settings,
        user_id=user_id,
        backtest_id=run_id,
        data_sha256=data_sha256,
        result=result,
        source_snapshot=snapshot,
        question=question,
        now=runtime.now(),
    )


def list_historical_reviews(
    session: Session, *, user_id: str, run_id: str
) -> list[HistoricalReviewResponse] | None:
    if get_run_record(session, user_id=user_id, run_id=run_id) is None:
        return None
    rows = session.execute(
        select(StrategyBacktestReview)
        .where(
            StrategyBacktestReview.user_id == user_id,
            StrategyBacktestReview.backtest_id == run_id,
            StrategyBacktestReview.status == "completed",
        )
        .order_by(StrategyBacktestReview.created_at.desc())
        .limit(20)
    ).scalars()
    return [
        HistoricalReviewResponse(
            id=row.id,
            backtest_id=row.backtest_id,
            data_sha256=row.data_sha256,
            created_at=row.created_at,
            question=row.question,
            model=row.model,
            input_tokens=row.input_tokens or 0,
            output_tokens=row.output_tokens or 0,
            cost_usd=row.cost_usd or Decimal("0"),
            answer=HistoricalReviewAnswer.model_validate(row.answer),
        )
        for row in rows
        if row.answer is not None
    ]


def _bar_snapshot(bars: list[CandlePoint]) -> list[dict[str, object]]:
    return [bar.model_dump(mode="json") for bar in bars]


def _funding_snapshot(
    funding: list[tuple[datetime, Decimal]],
) -> list[dict[str, str]]:
    return [{"at": at.astimezone(UTC).isoformat(), "rate": str(rate)} for at, rate in funding]


async def create_run(
    runtime: Runtime,
    *,
    body: BacktestInput,
) -> tuple[BacktestResult, dict[str, object]]:
    """Fetch and evaluate a bounded OKX history window, retaining exact inputs."""
    now = runtime.now()
    if now.tzinfo is None:
        raise ValueError("Application clock must return a timezone-aware time.")
    now = now.astimezone(UTC)
    end_at = now.replace(minute=(now.minute // 15) * 15, second=0, microsecond=0)
    start_at = end_at - timedelta(days=body.days)
    warmup_start = start_at - timedelta(days=7)
    symbol = body.symbol

    try:
        spot_bars = await runtime.okx_market_data.get_historical_candles(
            symbol, "spot", warmup_start, end_at
        )
        futures_bars = await runtime.okx_market_data.get_historical_candles(
            symbol, "futures", warmup_start, end_at
        )
        btc_spot_bars = (
            spot_bars
            if symbol == "BTCUSDT"
            else await runtime.okx_market_data.get_historical_candles(
                "BTCUSDT", "spot", warmup_start, end_at
            )
        )
        btc_futures_bars = (
            futures_bars
            if symbol == "BTCUSDT"
            else await runtime.okx_market_data.get_historical_candles(
                "BTCUSDT", "futures", warmup_start, end_at
            )
        )
        funding = await runtime.okx_market_data.get_historical_funding(symbol, start_at, end_at)
    except MarketDataUnavailable:
        raise

    source_snapshot: dict[str, object] = {
        "source": "OKX public historical API",
        "barInterval": "15m",
        "queriedAt": now.isoformat(),
        "requestedStart": start_at.isoformat(),
        "requestedEnd": end_at.isoformat(),
        "warmupStart": warmup_start.isoformat(),
        "series": {
            "targetSpot": _bar_snapshot(spot_bars),
            "targetFutures": _bar_snapshot(futures_bars),
            "btcSpotRegime": _bar_snapshot(btc_spot_bars),
            "btcFuturesContext": _bar_snapshot(btc_futures_bars),
        },
        "fundingRates": _funding_snapshot(funding),
    }
    data_sha256 = canonical_data_hash(source_snapshot)
    run_id = str(uuid4())
    result = await asyncio.to_thread(
        run_backtest,
        run_id=run_id,
        created_at=now,
        symbol=symbol,
        days=body.days,
        requested_start=start_at,
        requested_end=end_at,
        spot_bars=spot_bars,
        futures_bars=futures_bars,
        btc_spot_bars=btc_spot_bars,
        btc_futures_bars=btc_futures_bars,
        funding=funding,
        data_sha256=data_sha256,
    )
    return result, source_snapshot


def persist_run(
    session: Session,
    *,
    result: BacktestResult,
    source_snapshot: dict[str, object],
    user_id: str,
) -> StrategyBacktestRun:
    row = StrategyBacktestRun(
        id=result.id,
        user_id=user_id,
        symbol=result.symbol,
        requested_days=result.requested_days,
        strategy_version=result.strategy.strategy_version,
        data_sha256=result.data_sha256,
        created_at=result.created_at,
        result=result.model_dump(mode="json"),
        source_snapshot=source_snapshot,
    )
    session.add(row)
    session.flush()
    return row
