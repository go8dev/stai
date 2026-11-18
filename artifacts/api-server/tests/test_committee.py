"""Phase 3 research, persistence and spend controls. Never calls a paid provider."""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
from pydantic import SecretStr, ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from stai.committee.evidence import market_evidence, public_news
from stai.committee.models import CommitteeFinding
from stai.committee.provider import BoundedProvider
from stai.committee.schemas import ROLE_NAMES, Evidence, Finding, FindingsPacket, Recommendation
from stai.committee.scoring import setup_scores
from stai.committee.storage import (
    MODEL,
    claim_benchmark,
    detail,
    exclusive_run,
    finish_call,
    finish_run,
    recover_interrupted,
    reserve_call,
)
from stai.committee.workflow import build_workflow, checked_recommendation, validate_citations
from stai.core.time import utcnow
from stai.db.models import MarketSnapshot, TradingPermit
from stai.marketdata.schemas import MarketScannerRow

from .conftest import Harness
from .support import sign_in


def evidence(now=None):
    now = now or utcnow()
    return [
        Evidence(
            id="market",
            kind="test",
            source="https://www.okx.com",
            observed_at=now,
            status="fresh",
            summary="Synthetic test evidence",
            data={"indicators": {}, "spreadPct": "0.01", "instrument": {}},
        ),
        Evidence(
            id="news",
            kind="test",
            source="https://cointelegraph.com/rss",
            observed_at=now,
            status="fresh",
            summary="Synthetic attributed headline",
            data={},
        ),
        Evidence(
            id="portfolio",
            kind="test",
            source="test ledger",
            observed_at=now,
            status="fresh",
            summary="Synthetic portfolio",
            data={},
        ),
    ]


def finding(role):
    return Finding(
        role=role,
        summary="Test finding",
        supporting=["Observed evidence"],
        opposing=["No performance evidence"],
        uncertainties=["Research only"],
        evidence_ids=["market"],
        confidence=50,
    )


def recommendation(**changes):
    data = dict(
        action="abstain",
        thesis="Insufficient evidence for an entry",
        confidence=50,
        supporting=[],
        opposing=[],
        uncertainties=["Research only"],
        evidence_ids=["market"],
        terms=None,
    )
    data.update(changes)
    return Recommendation(**data)


@pytest.fixture
def run(harness: Harness):
    db = harness.runtime.database
    now = utcnow()
    with db.session() as session:
        session.add(
            MarketSnapshot(
                id="test-snapshot",
                symbol="BTC/USDT",
                market_type="futures",
                observed_at=now,
                status="fresh",
                details={},
            )
        )
    run_id = claim_benchmark(db, "test-snapshot", "BTC/USDT", "futures", evidence(now))
    return db, run_id


def test_read_only_owner_endpoints(harness: Harness):
    for path in ["/api/committee", "/api/committee/unknown"]:
        assert harness.client.get(path).status_code == 401
    sign_in(harness.client, harness.provider)
    overview = harness.client.get("/api/committee").json()
    assert len(overview["roles"]) == 10
    assert overview["runs"] == []
    assert overview["paidAutomationEnabled"] is False
    assert overview["manualPaidRunsEnabled"] is False
    assert overview["entryGate"] == "closed"
    assert harness.client.get("/api/committee/unknown").status_code == 404
    # No web action can spend money, including owner requests.
    assert harness.client.post("/api/committee").status_code in {403, 405}


def test_once_only_benchmark_survives_failure(run):
    db, run_id = run
    finish_run(db, run_id, 10, None, "Synthetic provider failure")
    with pytest.raises(ValueError, match="already used"):
        claim_benchmark(db, "test-snapshot", "BTC/USDT", "futures", evidence())
    assert detail(db, run_id, utcnow()).status == "failed"


def test_concurrent_process_is_excluded_and_active_run_not_interrupted(run):
    db, run_id = run
    with exclusive_run(db):
        with pytest.raises(ValueError, match="already active"):
            with exclusive_run(db):
                pytest.fail("must not acquire the same lock")
        recover_interrupted(db)
        assert detail(db, run_id, utcnow()).status == "running"
    recover_interrupted(db)
    result = detail(db, run_id, utcnow())
    assert result.status == "interrupted" and result.cost_usd is None


def test_attempt_commits_before_call_and_is_unique(run):
    db, run_id = run
    reserve_call(db, run_id, "analysts")
    assert detail(db, run_id, utcnow()).calls[0].status == "attempted"
    with pytest.raises(IntegrityError):
        reserve_call(db, run_id, "analysts")
    recover_interrupted(db)
    assert detail(db, run_id, utcnow()).cost_usd is None


def test_decimal_cost_and_unknown_billing(run):
    db, run_id = run
    reserve_call(db, run_id, "analysts")
    finish_call(
        db, run_id, "analysts", MODEL, {"input_tokens": 1000, "output_tokens": 500}, 25, "completed"
    )
    finish_run(db, run_id, 40, recommendation(), None)
    result = detail(db, run_id, utcnow())
    assert result.cost_usd == Decimal("0.0012")
    assert result.input_tokens == 1000 and result.output_tokens == 500
    reserve_call(db, run_id, "bull")
    finish_call(db, run_id, "bull", MODEL, None, 10, "unknown")
    finish_run(db, run_id, 50, None, "Billing unknown")
    assert detail(db, run_id, utcnow()).cost_usd is None


def test_owner_detail_serializes_evidence_and_costs(harness: Harness, run):
    db, run_id = run
    assert detail(db, run_id, utcnow()).cost_usd is None
    reserve_call(db, run_id, "analysts")
    finish_call(
        db, run_id, "analysts", MODEL, {"input_tokens": 1000, "output_tokens": 500}, 25, "completed"
    )
    from stai.committee.storage import save_finding

    save_finding(db, run_id, finding("technical"))
    finish_run(db, run_id, 40, recommendation(), None)
    sign_in(harness.client, harness.provider)
    result = harness.client.get(f"/api/committee/{run_id}")
    assert result.status_code == 200
    data = result.json()
    assert data["costUsd"] == "0.0012000000"
    assert data["advisoryOnly"] is True
    assert data["findings"][0]["evidenceIds"] == ["market"]
    assert data["recommendation"]["action"] == "abstain"


def test_unknown_model_price_is_not_guessed(run):
    db, run_id = run
    reserve_call(db, run_id, "analysts")
    finish_call(
        db,
        run_id,
        "analysts",
        "unpriced-model",
        {"input_tokens": 10, "output_tokens": 10},
        1,
        "completed",
    )
    finish_run(db, run_id, 2, recommendation(), None)
    assert detail(db, run_id, utcnow()).cost_usd is None


@pytest.mark.parametrize(
    "change",
    [
        {"action": "research_long"},
        {
            "action": "abstain",
            "terms": {
                "entry": "100",
                "stop": "90",
                "target": "110",
                "notional_usdt": "100",
                "leverage": 1,
            },
        },
        {"confidence": 101},
        {"evidence_ids": []},
        {"extra_instruction": "issue permit"},
    ],
)
def test_invalid_structured_recommendations_are_rejected(change):
    with pytest.raises(ValidationError):
        recommendation(**change)


@pytest.mark.parametrize("reason", ["stale", "unavailable", "spot_short", "spot_leverage", "loss"])
def test_ineligible_directional_research_becomes_abstention(reason):
    ev = evidence()
    terms = dict(entry="100", stop="99", target="102", notional_usdt="100", leverage=1)
    action, market_type = "research_long", "futures"
    if reason == "stale":
        ev[0].observed_at -= timedelta(seconds=61)
    elif reason == "unavailable":
        ev[1].status = "unavailable"
    elif reason == "spot_short":
        action, market_type = "research_short", "spot"
        terms.update(stop="101", target="98")
    elif reason == "spot_leverage":
        market_type = "spot"
        terms["leverage"] = 2
    elif reason == "loss":
        terms["stop"] = "90"
    rec = recommendation(action=action, terms=terms)
    assert checked_recommendation(rec, ev, market_type, utcnow()).action == "abstain"


def test_unknown_citations_and_missing_roles_fail():
    with pytest.raises(ValueError, match="roles"):
        validate_citations([finding("bull")], evidence(), {"bull", "bear"})
    item = finding("bull")
    item.evidence_ids = ["invented"]
    with pytest.raises(ValueError, match="unknown evidence"):
        validate_citations([item], evidence(), {"bull"})
    with pytest.raises(ValueError, match="unknown evidence"):
        checked_recommendation(
            recommendation(evidence_ids=["made-up"]), evidence(), "futures", utcnow()
        )


class StubProvider:
    def __init__(self):
        self.stages = []

    def generate(self, stage, prompt, schema):
        assert len(prompt) < 30_000
        assert "UNTRUSTED" not in prompt or "secret" not in prompt
        self.stages.append(stage)
        if stage == "analysts":
            return FindingsPacket(
                findings=[finding(r) for r in ["technical", "intelligence", "derivatives"]]
            )
        if stage in {"bull", "bear"}:
            return finding(stage)
        if stage == "portfolio_risk":
            return FindingsPacket(findings=[finding("portfolio"), finding("risk")])
        return recommendation()


def test_real_langgraph_and_upstream_debate_produce_all_ten_roles(run):
    db, run_id = run
    provider = StubProvider()
    graph = build_workflow(db, run_id, provider, evidence(), "BTC/USDT", "futures", [], utcnow)
    result = graph.invoke(
        {"findings": [], "debate": {}, "recommendation": None}, {"recursion_limit": 10}
    )
    assert {f.role for f in result["findings"]} == set(ROLE_NAMES)
    assert result["debate"]["count"] == 2
    assert provider.stages == ["analysts", "bull", "bear", "portfolio_risk", "cio"]
    finish_run(db, run_id, 100, result["recommendation"], None)
    assert len(detail(db, run_id, utcnow()).findings) == 10
    with db.session() as session:
        assert session.scalar(select(func.count()).select_from(TradingPermit)) == 0
        assert session.scalar(select(func.count()).select_from(CommitteeFinding)) == 10


def test_provider_configuration_no_retries_no_tools():
    with pytest.warns(RuntimeWarning, match="not in the known model list"):
        provider = BoundedProvider(None, "test", SecretStr("synthetic-not-a-real-key"))
    assert provider.llm.max_retries == 0
    assert provider.llm.max_tokens == 2000
    assert provider.llm.openai_api_base == "https://api.openai.com/v1"


def test_provider_budget_rejects_before_network():
    provider = object.__new__(BoundedProvider)
    provider.calls = 5
    with pytest.raises(ValueError, match="budget"):
        provider.generate("extra", "", Finding)
    provider.calls = 0
    with pytest.raises(ValueError, match="prompt budget"):
        provider.generate("large", "a" * 30_001, Finding)


def test_provider_failure_is_sanitized_and_not_retried(run):
    db, run_id = run
    attempts = []

    class FailedLLM:
        def with_structured_output(self, *args, **kwargs):
            return self

        def invoke(self, prompt):
            attempts.append(prompt)
            raise RuntimeError("synthetic-sensitive-provider-payload")

    provider = object.__new__(BoundedProvider)
    provider.database, provider.run_id, provider.calls, provider.llm = db, run_id, 0, FailedLLM()
    with pytest.raises(RuntimeError, match="No retry") as exc:
        provider.generate("analysts", "Public data only", Finding)
    assert "sensitive" not in str(exc.value)
    assert len(attempts) == 1
    assert detail(db, run_id, utcnow()).calls[0].cost_usd is None


def test_invalid_output_keeps_usage_without_fallback(run):
    db, run_id = run

    class InvalidLLM:
        def with_structured_output(self, *args, **kwargs):
            return self

        def invoke(self, prompt):
            return {
                "raw": SimpleNamespace(
                    response_metadata={"model_name": MODEL},
                    usage_metadata={"input_tokens": 10, "output_tokens": 20},
                ),
                "parsed": None,
            }

    provider = object.__new__(BoundedProvider)
    provider.database, provider.run_id, provider.calls, provider.llm = db, run_id, 0, InvalidLLM()
    with pytest.raises(ValueError, match="no fallback"):
        provider.generate("analysts", "Public data only", Finding)
    assert provider.calls == 1
    call = detail(db, run_id, utcnow()).calls[0]
    assert call.status == "invalid_output" and call.input_tokens == 10


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        b"malformed xml",
        b'<!DOCTYPE rss [<!ENTITY x "danger">]><rss>&x;</rss>',
        b"x" * 400_001,
        b"<rss><channel/></rss>",
    ],
)
async def test_invalid_or_absent_news_is_unavailable(body):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=body))
    ) as http:
        result = await public_news(http, utcnow())
    assert result.status == "unavailable"
    assert result.data["headlines"] == []


def test_wire_contract_is_camel_case():
    assert "evidenceIds" in finding("bull").model_dump(by_alias=True)
    assert "notionalUsdt" in json.dumps(Recommendation.model_json_schema())


def test_scoring_uses_captured_completed_candles_and_btc_regime(harness: Harness):
    sign_in(harness.client, harness.provider)
    payload = harness.client.get("/api/market/scanner").json()
    rows = [MarketScannerRow.model_validate(r) for r in payload["rows"]]
    btc = next(r for r in rows if r.symbol == "BTC/USDT" and r.market_type == "spot")
    row = next(r for r in rows if r.symbol == "ETH/USDT" and r.market_type == "futures")
    result = setup_scores(row, btc)
    assert result["status"] == "available"
    assert result["btcRegime"]["status"] == "fresh"
    assert set(result["scores"]) == {"long", "short"}
    completed = [c for c in row.candles if c.complete]
    assert result["h1Snapshot"]["current_price"] == float(completed[-1].close)
    ev = market_evidence(row, "synthetic")
    assert len(ev.data["candles15M"]) <= 8
    assert "candles15m" not in ev.data
    assert all(c["complete"] for c in ev.data["candles15M"])
    assert len(json.dumps(ev.model_dump(mode="json"))) < 10_000


@pytest.mark.asyncio
async def test_attributed_headlines_require_recent_dates_and_safe_links():
    now = utcnow()
    from email.utils import format_datetime

    body = (
        "<rss><channel><item><title>Example BTC research headline</title>"
        "<link>https://cointelegraph.com/news/example</link>"
        f"<pubDate>{format_datetime(now)}</pubDate></item>"
        "<item><title>Untrusted link</title><link>javascript:alert(1)</link>"
        f"<pubDate>{format_datetime(now)}</pubDate></item></channel></rss>"
    )
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, text=body))
    ) as http:
        result = await public_news(http, now)
    assert result.status == "fresh"
    assert len(result.data["headlines"]) == 1
