# STAI (SmartTrader AI): project brief

Date: 17 November 2026. Project name: STAI SmartTrader AI.

You are building STAI, a personal, paper-trading-only cryptocurrency research and portfolio
platform for one owner. This brief has three parts:

- Part A (this part): what was decided and verified with the owner in a planning conversation
  before this project was created. You have no other record of that conversation.
- Part B: the owner's specification, "STAI Master Development Prompt v1.0", reproduced
  verbatim. It is the governing document.
- Part C: the audit notes from the planning conversation.

Where an owner decision in A2 differs from Part B, the decision wins. Everything else in
Part B stands as written.

## A1. What to do first

1. Do not start building yet. Section 16 of the specification requires a technical review and
   an architecture plan first, and the owner has been told that nothing is built until they
   approve that plan.
2. Present the Phase 1 plan with the items section 16 lists: proposed architecture, repository
   reuse plan, technology stack, development phases, key technical risks, deployment
   limitations and estimated implementation effort.
3. In the same plan, list the proposals in A3 and the assumptions in A4 so the owner can
   approve or change each one, and ask for the two inputs in A7 that only the owner can give.
4. Most of the repository audit is already done (A5 and Part C). Build on it. Re-check only
   what depends on this project's own runtime (A7). Do not repeat the rest.
5. After approval, implement one phase at a time. After each phase give the short report
   section 16 asks for: completed, tested, pending, blocked, next recommended action.

## A2. Owner decisions

| Question | Decision |
|---|---|
| Where to build | A new project (this one). From the owner's earlier project, Smart Trader, reuse only the analytics. |
| Trading rhythm | Intraday: setups that play out over about 15 to 60 minutes. |
| AI model billing | The owner's own API key, not Replit-managed AI billing. |
| Alerts | Email. |
| Logo | The owner supplied a logo. Use it and do not design a new one. It stays provisional, as section 3 says. |

The owner is in the Asia/Manila time zone (UTC+8).

## A3. Proposals the owner has seen but not yet approved

Put these in the Phase 1 plan for approval.

- **Timeframes.** 1-hour candles for trend and 15-minute candles for entry timing. The reused
  analytics already work this way.
- **AI cost control.** Deterministic rule scoring runs every 15 minutes at no model cost. The
  AI committee runs only on setups whose rule score clears a threshold, with a daily cap on
  runs and on spend. Measure the cost and duration of one committee run before fixing the
  caps. TradingAgents makes at least 12 model calls per run as shipped.
- **Proposal validity.** 60 minutes by default, configurable. Entry is a limit order at the
  proposed price, checked again against the live price at the moment of approval. A changed
  price or an expired proposal needs a new approval (section 12).
- **Position sizing.** 0.5% risk is 5 USDT and the 20% cap is 200 USDT. They meet at a 2.5%
  stop distance. With a tighter intraday stop, the cap sets the size and the planned risk is
  below 5 USDT.
- **Email.** One message per proposal linking to the approval page, a daily summary, and risk
  and outage alerts. Approval happens only in the app after login, never from the email. A
  setting defines the hours in which proposals are sent. Setups outside those hours, and
  proposals that expire or are rejected, are still tracked so reports can show what they
  would have done. The owner was told that intraday setups can go stale before an email is
  read.
- **Email provider.** Resend. Resend and SendGrid are both already authorized on the owner's
  Replit account.
- **AI provider.** Assumed to be OpenAI, because Smart Trader used OpenAI. This is not
  confirmed.
- **Logo use.** The white-text version inside the dark app, the version as supplied on light
  backgrounds (emails and printed reports), and a simplified S for the browser-tab icon,
  because the mark blurs below 32 px. Keep the colour palette from section 3. The logo's teal
  is #00D6C8 and the specification's accent is #25C6B0.

## A4. Working assumptions stated to the owner, with no objection so far

List these in the plan for explicit confirmation.

- The owner is the only user and the only approver.
- The 600 USDT spot and 400 USDT futures allocations are fixed. Nothing moves between them
  automatically.
- Spot is long-only. Futures use at most 2x leverage with isolated margin.
- The daily-loss halt, the drawdown pause and the emergency halt block new entries only.
  Protective exits keep working.
- The day used for the daily loss limit is the UTC day.
- STAI's own PostgreSQL ledger, in decimal values, is the book of record. Freqtrade is the
  paper execution engine and is reconciled against that ledger.
- Freqtrade runs unmodified as a separate process, reachable only on localhost.
- Hosting is a Reserved VM deployment.

## A5. What the audit established (details in Part C)

All of this was observed on 17 November 2026 in a separate sandbox located in Asia, on
Python 3.13.11.

- Freqtrade 2026.10 needs Python 3.12 or newer. It supports one trading mode per bot, so STAI
  needs two dry-run bots, one for spot and one for futures.
- Freqtrade stores money as floats, so it cannot be the book of record.
- An approval gate works on unmodified Freqtrade. A strategy that never signals an entry and
  allows an entry only when it matches an approved proposal was tested against live OKX
  perpetual data with no API keys. Entries with no approval, with an approval for a different
  pair or side, or above the approved size were refused. The approved entry filled at the best
  bid or ask. Pausing Freqtrade refused new entries and still allowed exits.
- Still to build on top of that gate: binding leverage, stop, target and expiry to the
  approval, single use of each approval, and a price-drift check at execution time.
- Freqtrade's dry-run fills orders instantly and in full from the live order book. It does not
  simulate latency or partial fills. Section 9 asks for both, so the plan must say whether
  STAI models them itself or documents them as limitations.
- Freqtrade's stored entry fee understates the fee when leverage is used. STAI must compute
  fees from fills.
- TradingAgents 0.7.1 is built for equities on daily Yahoo data. It has no OKX data, no
  derivatives inputs and no quantitative or derivatives role, and it keeps memory in files or
  SQLite. A published Replit app's filesystem is not persistent, so that state must move to
  the database.
- OKX public REST works without keys. Minimum order sizes for BTC, ETH and SOL fit a 200 USDT
  position cap and a 5 USDT planned risk.
- Smart Trader's analytics passed all 191 of their tests on Python 3.13.11 with pandas 3.1.1,
  numpy 2.5.5 and pydantic 2.14.3.

## A6. Supporting files

A folder named `stai_handoff/` is being added to the root of this project from the planning
conversation. It arrives as a merge that the owner approves, so it may appear shortly after
you start. It contains:

- `PROJECT_BRIEF.md`, `MASTER_PROMPT_v1.0.md` and `AUDIT_NOTES.md`: Parts A, B and C of this
  brief.
- `brand/stai_logo_dark_background.png`: the logo with white text, for the dark app.
- `brand/stai_logo_light_background.png`: the logo as supplied, for light backgrounds.
- `smart_trader_analytics/`: the reusable analytics and their four test files, with a README
  that lists the port steps and what was left behind on purpose.
- `freqtrade_gate_probe/`: the strategy, example configuration and decision log from the
  approval gate test.

If the folder is not there when you need a file from it, ask the owner for it. Do not redraw
the logo or rewrite the analytics from scratch.

## A7. Open items

Only the owner can provide:

- The AI provider and its API key. Collect the key through Replit Secrets only. Never ask for
  it in chat, print it or log it.
- The email address that alerts go to.

Not yet verified:

- Whether this project's runtime provides Python 3.12 or newer and installs Freqtrade and
  TA-Lib cleanly.
- OKX public API reachability from a US-hosted deployment. It was verified only from Asia.
  Replit deployments default to the United States, and the region is selectable.
- Dry-run fee rates in spot mode. On perpetuals the fee was 0.05% of notional per side.
- Model cost and duration per committee run on intraday data.
- Machine size for two bots, the API and an AI run together. One idle futures bot used about
  435 MB, and start-up took about 2 minutes on 1 vCPU.
- Email delivery from the deployed app.

## A8. Rules that must not be weakened

- Paper trading only. No live-trading switch. Do not request or store exchange trading
  credentials. Use public market-data endpoints (section 12).
- Bring nothing from Smart Trader except the analytics in `stai_handoff/`. Its Binance client,
  exchange key settings, trading-enabled flag and order execution code conflict with
  section 12.
- Every new entry needs the owner's explicit approval of the exact trade. No agent can submit
  an order (section 7).
- Do not start the 30-day pilot automatically (section 13).
