"""Single owner-approved workspace benchmark. There is no paid web endpoint."""

from __future__ import annotations

import argparse
import asyncio
import json
from time import monotonic

from langsmith import tracing_context

from stai.committee.evidence import market_evidence, public_news
from stai.committee.models import CommitteeRun
from stai.committee.provider import BoundedProvider
from stai.committee.schemas import Evidence
from stai.committee.scoring import setup_scores
from stai.committee.storage import (
    claim_benchmark,
    detail,
    exclusive_run,
    finish_run,
    recover_interrupted,
)
from stai.committee.workflow import build_workflow
from stai.core.config import get_settings, secret_values_from_environment
from stai.core.logging import configure_logging, register_secret_values
from stai.core.time import utcnow
from stai.main import create_app
from stai.marketdata.routes import _enrich
from stai.marketdata.service import persist_market_rows
from stai.portfolio.routes import get_portfolio_summary


async def collect(runtime, symbol: str, market_type: str) -> tuple[str, list[Evidence]]:
    rows = [_enrich(r) for r in await runtime.okx_market_data.scanner()]
    row = next(r for r in rows if r.symbol == symbol and r.market_type == market_type)
    if (
        row.status != "fresh"
        or row.indicators is None
        or row.indicators.screening_state == "unavailable"
    ):
        raise ValueError("Fresh complete market evidence required before claiming benchmark")
    btc_row = next(r for r in rows if r.symbol == "BTC/USDT" and r.market_type == "spot")
    scores = setup_scores(row, btc_row)
    if scores["status"] != "available":
        raise ValueError("Deterministic scoring evidence unavailable")
    portfolio = get_portfolio_summary(runtime)
    news = await public_news(runtime.http, utcnow())
    with runtime.database.session() as session:
        ids = persist_market_rows(session, [row])
    market = market_evidence(row, ids[0])
    market.data["setupScores"] = scores
    if (utcnow() - market.observed_at).total_seconds() > 60:
        raise ValueError("Market evidence expired during preflight; no paid attempt made")
    return ids[0], [
        market,
        news,
        Evidence(
            id="portfolio",
            kind="ledger_portfolio",
            source="STAI PostgreSQL ledger",
            observed_at=portfolio.updated_at,
            status="fresh" if portfolio.ledger_verified else "unavailable",
            summary="Recorded virtual balances and holdings, not an exchange account",
            data=portfolio.model_dump(mode="json", by_alias=True),
        ),
    ]


async def benchmark(symbol: str, market_type: str) -> dict:
    settings = get_settings()
    # Fail closed on published machines even if someone supplies STAI_ENV incorrectly.
    if settings.is_production or settings.is_published:
        raise ValueError("Benchmark is development-only; production remains untouched")
    if settings.openai_api_key is None:
        raise ValueError("OPENAI_API_KEY is not configured")
    configure_logging("WARNING")
    register_secret_values(secret_values_from_environment())
    app = create_app()
    runtime = app.state.runtime
    recover_interrupted(runtime.database)
    started = monotonic()
    try:
        with exclusive_run(runtime.database):
            # Check slot before any public preflight work or provider construction.
            from sqlalchemy import select

            from stai.committee.storage import BENCHMARK

            with runtime.database.session() as session:
                if session.scalar(select(CommitteeRun.id).where(CommitteeRun.purpose == BENCHMARK)):
                    raise ValueError("Benchmark already attempted; no second paid run authorized")
            snapshot_id, evidence = await collect(runtime, symbol, market_type)
            run_id = claim_benchmark(runtime.database, snapshot_id, symbol, market_type, evidence)
            error = None
            recommendation = None
            try:
                provider = BoundedProvider(runtime.database, run_id, settings.openai_api_key)
                with runtime.database.session() as session:
                    memory = session.get(CommitteeRun, run_id).memory
                workflow = build_workflow(
                    runtime.database,
                    run_id,
                    provider,
                    evidence,
                    symbol,
                    market_type,
                    memory,
                    utcnow,
                )
                with tracing_context(enabled=False):
                    result = await asyncio.to_thread(
                        workflow.invoke,
                        {
                            "findings": [],
                            "debate": {},
                            "recommendation": None,
                        },
                        {"recursion_limit": 10},
                    )
                recommendation = result["recommendation"]
            except Exception:
                error = (
                    "Committee benchmark stopped: provider, budget or output validation failure. "
                    "No automatic retry. Inspect recorded stages; unknown billing stays unknown."
                )
            finish_run(
                runtime.database, run_id, int((monotonic() - started) * 1000), recommendation, error
            )
            result = detail(runtime.database, run_id, utcnow())
            return result.model_dump(mode="json", by_alias=True)
    finally:
        await runtime.http.aclose()
        runtime.database.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", action="store_true", required=True)
    parser.add_argument(
        "--symbol", choices=["BTC/USDT", "ETH/USDT", "SOL/USDT"], default="BTC/USDT"
    )
    parser.add_argument("--market-type", choices=["spot", "futures"], default="futures")
    args = parser.parse_args()
    try:
        result = asyncio.run(benchmark(args.symbol, args.market_type))
    except Exception:
        raise SystemExit(
            "Benchmark preflight refused. No retry or production action was taken."
        ) from None
    # Only safe research metrics, never provider objects or settings.
    print(  # noqa: T201 (safe CLI summary)
        json.dumps(
            {
                k: result[k]
                for k in [
                    "id",
                    "status",
                    "durationMs",
                    "inputTokens",
                    "outputTokens",
                    "costUsd",
                    "action",
                    "error",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
