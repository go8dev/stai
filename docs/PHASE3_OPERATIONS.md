# Phase 3: AI Committee

Phase 3 is implemented in the **development workspace only**. The owner explicitly
deferred production migrations. No publish, production schema change, VM change,
production bot activation or pilot start was performed.

## What runs

The existing paper worker continues free deterministic screening every 15 minutes,
now including the reused setup scorer and BTC 1h/15m regime. It captures completed
candles from the appropriate spot/swap observations; it does not use a spot-only
provider to score futures. Scores and indicator evidence are saved with market
snapshots. Missing BTC evidence is explicitly unknown and earns no alignment points.
There is no selected AI-trigger threshold.

The AI Committee page at `/ai-committee` reads:

- `GET /api/committee`: ten roles, run history and disabled-run policy.
- `GET /api/committee/{run_id}`: role findings, evidence, recommendation, memory,
  provider calls, tokens, estimated cost and duration.

Both require the owner's session. There is no web endpoint or button that runs a
paid model, changes the budget or creates a proposal, permit or order.

### Roles and upstream reuse

Ten roles produce findings. Quantitative Researcher and Execution Specialist are
deterministic calculations. A bounded LangGraph workflow uses five model calls:

1. Shared technical, intelligence and derivatives analysis.
2. Bull Researcher using the unmodified TradingAgents factory.
3. Bear Researcher using its unmodified factory and the bull argument.
4. Shared Portfolio Manager and advisory Risk Officer review.
5. CIO structured recommendation.

All model stages use TradingAgents' OpenAI provider factory, strict STAI schemas and
the same fixed, captured evidence. The standard upstream graph is not launched:
its equity tools, separate risk debates, file memory and structured-output/free-text
fallback retries conflict with the crypto tool boundary and fixed call budget.
Other crypto role prompts and orchestration are STAI adapters, not claims that
upstream equity analysts already understand OKX.

No upstream source was changed. TradingAgents 0.7.1 is locked to its release commit
in `uv.lock`; its packaged licence is Apache-2.0. LangGraph 1.2.22, LangChain Core
1.8.1, LangChain OpenAI 1.8.0 and LangSmith 0.15.0 are MIT. OpenAI SDK 3.52.0 is
Apache-2.0. Dependencies include unused equity and other-provider packages required
by TradingAgents; STAI does not invoke those providers or Yahoo tools.

## Evidence and recommendation safety

Public OKX evidence covers BTC/ETH/SOL spot and swaps: completed 1h/15m candles,
indicators, funding, book levels and instrument rules. Model context contains only a
bounded completed-candle tail; full-series calculations remain deterministic.
Cointelegraph's public RSS supplies at most five attributed headlines from the last
24 hours, with source URLs and publication timestamps. It is broad crypto news,
not measured social sentiment or guaranteed asset-specific coverage.

RSS input is size-limited, rejects DTD/entities and does not follow redirects.
Feed outages or malformed/old stories are reported as unavailable, not synthetic
headlines. Headline text and prior research are untrusted data, not instructions.
Models have no browsing, file, secret, database or execution tools. LangSmith
tracing is explicitly disabled for the benchmark workflow and provider calls.

Structured findings require known roles and evidence references. The recommendation
is `research_long`, `research_short` or `abstain`, with thesis, supporting and opposing
evidence, uncertainty and subjective confidence. Indicative terms use Decimal and
coherent long/short levels; they are **not** an actionable proposal.

The final check withholds directional recommendations on stale (>60 seconds) market
evidence, unavailable required evidence, invalid spot direction/leverage, or
indicative loss above the initial 5 USDT research bound. This is schema/research
validation, **not** the Phase 4 deterministic risk engine. Model confidence is not a
calibrated probability. Historical evidence is labelled stale when viewed later.

## One measured benchmark

On 18 November 2026, the owner-approved workspace benchmark completed on BTC/USDT
USDT perpetual evidence:

- Ten findings: eight advisory model roles and two deterministic roles.
- Five model calls, with no provider retry.
- Duration **37,646 ms (37.646 seconds)**, including evidence collection and persistence.
- **32,746 input tokens; 2,104 output tokens.**
- Estimated operating cost **$0.0164648 USD**, separate from the virtual USDT fund.
- Final action **abstain**. No permit, order, position or trading-ledger movement.

Cost basis: the provider's standard text rates for
`gpt-4.1-mini-2025-04-14`, verified at
<https://developers.openai.com/api/docs/pricing> on 18 November 2026:
$0.40 per million input tokens and $1.60 per million output tokens. All input is
conservatively costed as uncached. This is a list-price estimate, not an invoice;
credits, taxes and account-specific billing were not checked. Unknown usage/model
pricing stays unknown, never zero. The source lists this model as deprecated;
select and separately authorize a replacement benchmark before relying on it for
continuous operation. TradingAgents' model catalog warns about this exact snapshot
ID, but the provider accepted it; the resolved model is recorded per call.

The first shell invocation was refused before claiming a slot or contacting OpenAI,
because shell settings default to production. The actual workspace benchmark used
explicit development mode; only that invocation made paid calls.

### Limits proposed for owner review — NOT enabled

Provisional starting values:

- Rule-score threshold: **70/100**, requiring fresh, complete evidence.
- At most **10 committee runs per UTC day**.
- At most **$0.50 USD per UTC day**, with pre-request reservation of a conservative
  worst-case run cost in any future implementation.

At the measured list-price estimate, ten similar runs would cost about **$0.165/day**.
One run does not establish trading quality, score calibration, future latency or
future cost. These are proposed operational limits, not approved policy. Automatic
and repeat manual paid runs remain disabled; no setting silently enables them.
Owner approval and a separately scoped implementation are needed to activate them.

## Persistence, interruption and retries

Development migration `0003` adds `committee_agents`, `committee_runs`,
`committee_findings` and `committee_calls`. Runs retain findings/evidence, bounded
prior-research memory, model IDs, usage, cost basis and duration. Financial results
do not come from model memory.

A PostgreSQL session advisory lock permits one committee process. A unique benchmark
purpose consumes the single paid-run slot even if the process fails. Each attempted
provider call is committed before network I/O, so a crash cannot make an attempted
charge disappear. Provider SDK retries are zero; there is no plain-text fallback.
The workflow is acyclic, capped at five calls, 2,000 output tokens per call,
30,000 prompt/schema characters per call, and a 60-second request timeout.

Recovery only marks running records interrupted when it can acquire the process
lock. The paper worker checks on scans; the benchmark also checks before starting.
The API health check remains database-lazy. In-flight attempts and interrupted runs
have unknown total cost where provider usage is missing. They are never resumed or
retried automatically. Public evidence may be recollected without a paid request
when preflight is refused before the benchmark slot is claimed.

The CLI is development-only and has already used its slot:

```bash
STAI_ENV=development PYTHONPATH=artifacts/api-server \
  python -m stai.committee --benchmark --symbol BTC/USDT --market-type futures
```

Do not delete the benchmark row or reset the slot to get another run. A failed run
requires a report and fresh owner authorization before any additional paid attempt.
`OPENAI_API_KEY` comes only from Secrets and is never written into project files.

## Verification boundaries

The backend tests use throwaway PostgreSQL databases and synthetic model responses;
they do not spend money. They cover the real LangGraph and upstream debate factories,
all ten roles, strict schemas/citations, forced abstention, owner-only APIs,
one-shot/concurrency protection, recovery and Decimal/unknown-cost bookkeeping.
The live benchmark separately verifies provider integration on real public data.

The committee frontend is typechecked and built against the generated contract.
The signed-in committee UI has not been browser-verified with the owner's session.
Production migration/restart, provider account invoice and long-running reliability
remain unverified. Phase 4 approval/risk/email/execution wiring is not implemented.
