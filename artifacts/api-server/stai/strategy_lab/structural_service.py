"""Persistence and bounded OKX data collection for the structural challenger."""

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
from stai.strategy_lab.engine import canonical_data_hash
from stai.strategy_lab.models import StrategyBacktestRun
from stai.strategy_lab.structural_engine import (
    DEVELOPMENT_END,
    DEVELOPMENT_START,
    ENGINE_VERSION,
    FUTURE_VALIDATION_END,
    FUTURE_VALIDATION_START,
    STRATEGY_VERSION,
    research_windows,
    run_structural_backtest,
    strategy_configuration,
)
from stai.strategy_lab.structural_schemas import (
    StructuralBacktestInput,
    StructuralBacktestResult,
    StructuralLabOverview,
    StructuralRunListItem,
)

WARMUP = timedelta(days=7)


class StructuralWindowLocked(ValueError):
    """The reserved future validation sample is not available yet."""


class StructuralWindowUsed(ValueError):
    """The owner has already consumed the one reserved validation sample."""


def _result(row: StrategyBacktestRun) -> StructuralBacktestResult:
    return StructuralBacktestResult.model_validate(row.result)


def _list_item(row: StrategyBacktestRun) -> StructuralRunListItem:
    result = _result(row)
    completed = sum(
        scenario.metrics.trade_count
        for segment in result.segments
        for scenario in segment.cost_results
        if scenario.market_cost_bps == 5
    )
    return StructuralRunListItem(
        id=row.id,
        created_at=row.created_at,
        symbol=row.symbol,  # type: ignore[arg-type]
        strategy_version=row.strategy_version,
        sample_period=result.sample_period,
        requested_start=result.requested_start,
        requested_end=result.requested_end,
        data_sha256=row.data_sha256,
        completed_trades=completed,
    )


def overview(session: Session, user_id: str, now: datetime) -> StructuralLabOverview:
    rows = session.execute(
        select(StrategyBacktestRun)
        .where(
            StrategyBacktestRun.user_id == user_id,
            StrategyBacktestRun.strategy_version == STRATEGY_VERSION,
        )
        .order_by(StrategyBacktestRun.created_at.desc())
        .limit(20)
    ).scalars()
    development, future = research_windows(now)
    return StructuralLabOverview(
        strategy=strategy_configuration(),
        development_window=development,
        future_validation_window=future,
        committee_review_status="not_run",
        committee_notice=(
            "Candidate evidence is proposal-compatible, but no AI calls, proposals, "
            "approvals, permits, or orders are created by this research page."
        ),
        recent_runs=[_list_item(row) for row in rows],
    )


def list_runs(session: Session, user_id: str) -> list[StructuralRunListItem]:
    rows = session.execute(
        select(StrategyBacktestRun)
        .where(
            StrategyBacktestRun.user_id == user_id,
            StrategyBacktestRun.strategy_version == STRATEGY_VERSION,
        )
        .order_by(StrategyBacktestRun.created_at.desc())
        .limit(20)
    ).scalars()
    return [_list_item(row) for row in rows]


def get_run(session: Session, *, user_id: str, run_id: str) -> StructuralBacktestResult | None:
    row = session.execute(
        select(StrategyBacktestRun).where(
            StrategyBacktestRun.id == run_id,
            StrategyBacktestRun.user_id == user_id,
            StrategyBacktestRun.strategy_version == STRATEGY_VERSION,
        )
    ).scalar_one_or_none()
    return _result(row) if row is not None else None


def _snapshot_bars(bars: list[CandlePoint]) -> list[dict[str, object]]:
    return [bar.model_dump(mode="json") for bar in bars]


def _snapshot_funding(
    rows: list[tuple[datetime, Decimal]],
) -> list[dict[str, str]]:
    return [{"at": at.astimezone(UTC).isoformat(), "rate": str(rate)} for at, rate in rows]


def _window(sample_period: str) -> tuple[datetime, datetime]:
    if sample_period == "development":
        return DEVELOPMENT_START, DEVELOPMENT_END
    return FUTURE_VALIDATION_START, FUTURE_VALIDATION_END


async def create_run(
    runtime: Runtime,
    *,
    user_id: str,
    body: StructuralBacktestInput,
) -> tuple[StructuralBacktestResult, dict[str, object]]:
    now = runtime.now()
    if now.tzinfo is None:
        raise ValueError("Application clock must return a timezone-aware time.")
    now = now.astimezone(UTC)
    start_at, end_at = _window(body.sample_period)
    if body.sample_period == "future_validation" and now < end_at:
        raise StructuralWindowLocked("The frozen future-validation window is not complete yet.")
    if body.sample_period == "future_validation":
        with runtime.database.session() as session:
            existing = session.execute(
                select(StrategyBacktestRun.id)
                .where(
                    StrategyBacktestRun.user_id == user_id,
                    StrategyBacktestRun.symbol == body.symbol,
                    StrategyBacktestRun.result["sample_period"].astext == "future_validation",
                )
                .limit(1)
            ).scalar_one_or_none()
        if existing is not None:
            raise StructuralWindowUsed(
                "The reserved future-validation sample has already been used for this instrument."
            )
    warmup_start = start_at - WARMUP
    symbol = body.symbol

    market_data = runtime.okx_market_data
    try:
        (
            spot_15m,
            spot_1h,
            futures_15m,
            futures_1h,
            spot_1m,
            futures_1m,
        ) = await asyncio.gather(
            market_data.get_historical_candles(
                symbol, "spot", warmup_start, end_at, timeframe="15m"
            ),
            market_data.get_historical_candles(
                symbol, "spot", warmup_start, end_at, timeframe="1h"
            ),
            market_data.get_historical_candles(
                symbol, "futures", warmup_start, end_at, timeframe="15m"
            ),
            market_data.get_historical_candles(
                symbol, "futures", warmup_start, end_at, timeframe="1h"
            ),
            market_data.get_historical_candles(symbol, "spot", start_at, end_at, timeframe="1m"),
            market_data.get_historical_candles(symbol, "futures", start_at, end_at, timeframe="1m"),
        )

        if symbol == "BTCUSDT":
            btc_spot_1h = spot_1h
            btc_futures_1h = futures_1h
        else:
            btc_spot_1h, btc_futures_1h = await asyncio.gather(
                market_data.get_historical_candles(
                    "BTCUSDT", "spot", warmup_start, end_at, timeframe="1h"
                ),
                market_data.get_historical_candles(
                    "BTCUSDT", "futures", warmup_start, end_at, timeframe="1h"
                ),
            )
        spot_rules = await market_data.get_instrument_rule(symbol, "spot")
        futures_rules = await market_data.get_instrument_rule(symbol, "futures")
        funding = await market_data.get_historical_funding(symbol, start_at, end_at)
    except MarketDataUnavailable:
        raise

    tick_sizes = {
        "spot": spot_rules.tick_size,
        "futures": futures_rules.tick_size,
    }
    if tick_sizes["spot"] is None or tick_sizes["futures"] is None:
        raise MarketDataUnavailable("OKX did not return tick sizes for both markets.")

    source_snapshot: dict[str, object] = {
        "source": "OKX public historical API",
        "strategyVersion": STRATEGY_VERSION,
        "engineVersion": ENGINE_VERSION,
        "samplePeriod": body.sample_period,
        "queriedAt": now.isoformat(),
        "requestedStart": start_at.isoformat(),
        "requestedEnd": end_at.isoformat(),
        "warmupStart": warmup_start.isoformat(),
        "configuration": strategy_configuration().model_dump(mode="json"),
        "series": {
            "targetSpot1m": _snapshot_bars(spot_1m),
            "targetFutures1m": _snapshot_bars(futures_1m),
            "targetSpot15m": _snapshot_bars(spot_15m),
            "targetFutures15m": _snapshot_bars(futures_15m),
            "targetSpot1h": _snapshot_bars(spot_1h),
            "targetFutures1h": _snapshot_bars(futures_1h),
            "btcSpot1h": _snapshot_bars(btc_spot_1h),
            "btcFutures1h": _snapshot_bars(btc_futures_1h),
        },
        "instrumentRules": {
            "spot": {
                "instrumentId": spot_rules.instrument_id,
                "tickSizeAtQuery": str(spot_rules.tick_size),
            },
            "futures": {
                "instrumentId": futures_rules.instrument_id,
                "tickSizeAtQuery": str(futures_rules.tick_size),
            },
        },
        "fundingRates": _snapshot_funding(funding),
    }
    data_sha256 = canonical_data_hash(source_snapshot)
    run_id = str(uuid4())
    result = await asyncio.to_thread(
        run_structural_backtest,
        run_id=run_id,
        created_at=now,
        symbol=symbol,
        sample_period=body.sample_period,
        sample_start=start_at,
        sample_end=end_at,
        m15_by_market={"spot": spot_15m, "futures": futures_15m},
        hourly_by_market={"spot": spot_1h, "futures": futures_1h},
        btc_hourly_by_market={"spot": btc_spot_1h, "futures": btc_futures_1h},
        minute_by_market={"spot": spot_1m, "futures": futures_1m},
        tick_sizes=tick_sizes,  # type: ignore[arg-type]
        funding=funding,
        data_sha256=data_sha256,
        now=now,
    )
    return result, source_snapshot


def persist_run(
    session: Session,
    *,
    result: StructuralBacktestResult,
    source_snapshot: dict[str, object],
    user_id: str,
) -> StrategyBacktestRun:
    row = StrategyBacktestRun(
        id=result.id,
        user_id=user_id,
        symbol=result.symbol,
        requested_days=30,
        strategy_version=STRATEGY_VERSION,
        data_sha256=result.data_sha256,
        created_at=result.created_at,
        result=result.model_dump(mode="json"),
        source_snapshot=source_snapshot,
    )
    session.add(row)
    session.flush()
    return row
