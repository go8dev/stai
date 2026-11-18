# STAI Phase 1 plan

Status: approved by the owner on 17 November 2026, all 23 items as proposed. The owner published Phase 1 on 18 November 2026 and provided healthy production and verified audit screenshots. Restart check 7 remains unconfirmed. Phases 2 and 3 are implemented in the workspace; they have not been published. Phases 4 to 7 are not started.
The decision log at the end records what the owner approved or changed. Item numbers are never reused.

This is the technical review and architecture plan that section 16 of the specification asks
for. It builds on the audit from the planning conversation. Only what depends on this
project's own runtime was re-checked.

One change to the project so far: the Python 3.12 runtime was switched on, which the checks
needed and the build will need. All test installs were done in a temporary folder that has
been deleted.

## What was checked here (17 Nov 2026)

| Open item from the audit | Result in this project |
|---|---|
| Python 3.12+, Freqtrade and TA-Lib | Works. Python 3.12.12. Freqtrade 2026.10 and TA-Lib 0.8.3 installed and ran. Freqtrade, TradingAgents 0.7.1 and the rest of the backend resolve to one set of 148 pinned packages with no conflicts. |
| Dry-run fees in spot mode | Spot 0.10% maker, 0.15% taker. Perpetuals 0.02% maker, 0.05% taker. These come from the exchange library's built-in table, not from an OKX account. |
| Machine size | Two idle bots started together on one core. Spot was ready in 21 s using 363 MB. Futures was ready in 141 s using 427 MB. The API, worker and an AI run on top of that are not measured yet. |
| OKX from a US deployment | Not testable from here, because this workspace is also in Asia. OKX public data works from it. |
| AI cost and duration per run | Needs the owner's key. Measured at the start of Phase 3. |
| Email delivery from the deployed app | Needs a published app. Resend shows as authorized on the owner's account and ready to attach. |

## 1. Proposed architecture

One application, built as a modular monolith, plus the two trading-engine processes that the
audit showed are needed.

| Part | Role |
|---|---|
| Web app | The interface for the ten modules. Dark theme, PAPER label on every trading screen. |
| STAI API | Python and FastAPI. The only part reachable from the internet. Sign-in, proposals, approvals, risk engine, ledger, journal, reports. |
| STAI worker | Same codebase, separate process. Scans every 15 minutes, rule scoring, AI committee runs, proposal expiry, reconciliation, funding, equity snapshots, emails, health checks. |
| Two Freqtrade bots | Unmodified and dry-run only, one for spot and one for futures. Reachable only from inside the machine. |
| PostgreSQL | STAI's decimal ledger as the book of record, all the data models in section 10, and the append-only audit trail. |

How a new entry travels. This is the chain in section 12, enforced on the server:

1. The worker scores BTC, ETH and SOL every 15 minutes with the reused analytics. This costs nothing in model usage.
2. A setup above the threshold starts one committee run, which returns a structured recommendation.
3. The deterministic risk engine checks it and can veto it. If it passes, STAI stores a pending proposal with exact parameters and an expiry, and emails the owner.
4. The owner approves the exact trade in the app. STAI checks price, expiry, limits and halts again.
5. STAI issues a single-use permit tied to the pair, side, size, leverage, stop, target, expiry and a price band, and asks Freqtrade to enter. The gate strategy inside Freqtrade refuses any entry that has no matching unused permit. The bots never start an entry themselves.
6. Freqtrade fills the order in dry-run and manages the stop and target that were approved with the entry. STAI records the orders, fills, fees and funding in its ledger and reconciles against Freqtrade.

Design points that come from the runtime checks:

- **Freqtrade's state.** A published machine loses its local files at every restart. Each bot keeps its normal local database file, and STAI stores a copy in PostgreSQL with every trade event and restores it at start-up. After a restart STAI compares the bots with the ledger and blocks new entries until they agree.
- **AI memory.** TradingAgents keeps its memory in files. STAI stores agent runs, findings and memory in its own tables.
- **Ten roles, fewer model calls.** The Quantitative Researcher and the Execution Specialist are calculations, not model calls. The other eight follow TradingAgents' analyst, debate and decision stages. The aim is fewer calls than the 12 or more it makes as shipped.
- **No live path.** STAI never holds exchange keys. It generates the bots' configuration with dry-run fixed on, and a start-up check stops a bot if dry-run is off or a key is present. The app has no setting for it.

## 2. Repository reuse plan

| Source | Version and licence | Reused for | Left out |
|---|---|---|---|
| Freqtrade | 2026.10, GPL-3.0 | OKX connection, dry-run fills, stops and targets, funding, leverage tiers, backtesting for the Strategy Laboratory. Installed as a pinned package and never edited. | Its own strategies and automatic entries, FreqUI, Telegram. |
| TradingAgents | 0.7.1, Apache-2.0 | Model-provider layer and the analyst, bull and bear, risk and decision roles. Installed from its GitHub release and never edited. | Yahoo and equities data, the fundamentals analyst, file-based memory. |
| LangGraph | as TradingAgents requires, MIT | Running the committee workflow. | |
| CCXT | 4.5.93, MIT | OKX public data: candles, tickers, order book, funding, instrument rules. | Anything that needs keys. |
| Smart Trader analytics | commit a99c668 | Indicators, BTC regime, setup scoring and the snapshot builder with their 191 tests, ported by the six steps in the handoff README. | Everything else in Smart Trader. |
| FreqUI, Hummingbot, ai-hedge-fund | | Reference only. Not installed. | |

New work that no repository provides: OKX data tools for the agents, the Derivatives Analyst,
structured recommendations, the permit service, the ledger, the risk engine and the interface.

Licence note, not legal advice: GPL-3.0 places no obligation on personal use. The gate
strategy plugs into Freqtrade, so the GPL would apply to it if STAI were ever distributed.
Distribution or commercial use needs a legal review first. A register of versions, licences
and integration decisions will be kept in the project.

From this project's starter template: keep the workspace layout and the generated API client,
replace the starter Node API with the Python backend, and remove the starter database package
that the Python side makes redundant.

## 3. Technology stack

- **Interface:** React, TypeScript in strict mode, Vite, Tailwind CSS, TradingView Lightweight Charts, Inter and IBM Plex Mono.
- **Backend:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic.
- **Database:** Replit PostgreSQL 16.
- **AI:** TradingAgents and LangGraph with the owner's provider and key, structured outputs.
- **Trading:** Freqtrade in dry-run, CCXT, TA-Lib, OKX public endpoints only.
- **Email:** Resend.
- **Quality:** pytest, Ruff, ESLint, Prettier, a few browser tests for the main owner workflows. All versions pinned in lock files.

Vite rather than Next.js: the interface is a signed-in dashboard on a Python API, so Next.js
would add a second server with no job.

Git (section 11.3): the project has a Git repository as of 17 November 2026. It had none
when this plan was first written. Each saved checkpoint appears as a commit. Each phase is
built as a separate task that joins the main project only after the owner accepts it, which
keeps the main line working.

## 4. Development phases

The specification's seven phases stand, with two adjustments. The approval gate is built in
Phase 2 together with Freqtrade, so the engine never exists without it. A test publish closes
Phase 1 (item 23).

| Phase | What the owner gets | Size |
|---|---|---|
| 1. Foundation | Python backend and web app, database with migrations, owner sign-in, design system with the supplied logo, navigation with screens that state what is not built yet and show no sample data, ported analytics with tests passing, health check, test publish. | Medium, 1 round |
| 2. Trading engine | Two dry-run bots behind the gate, OKX data with freshness checks, the 1,000 USDT fund, decimal ledger, fees and funding, reconciliation, restart recovery. Market Scanner and Portfolio on real data. | Large, 2 rounds |
| 3. AI committee | TradingAgents on OKX data, the ten roles, structured recommendations, cost and duration measured, committee screens. | Large, 2 rounds |
| 4. Approval and risk | Risk engine, proposals and approval, emails, halts. Ends with the first milestone: OKX data through to a reconciled ledger. | Large, 1 to 2 rounds |
| 5. Dashboard and analytics | Command Center, Journal, Performance, Strategy Laboratory, Risk and Pilot Monitor, daily summary. | Large, 2 rounds |
| 6. Quality assurance | Full test run, authorization, reconciliation and restart tests, fee and funding validation, several days of continuous running on the deployed machine. | Medium, 1 round |
| 7. Pilot readiness | The 16 acceptance criteria checked one by one, configuration frozen, Start Pilot enabled for the owner to press. | Small, 1 round |

After each phase work stops for a report: completed, tested, pending, blocked, next recommended action.

## 5. Key technical risks

| Risk | Response |
|---|---|
| State lost at restart | Ledger in PostgreSQL, bot state stored with each trade event, entries blocked until bots and ledger agree. Tested in Phases 2 and 6. |
| Stops cannot fire while the service is down | After a restart the futures bot needs about 2.5 minutes. Late exits are recorded at the real price and flagged, and the owner gets an outage email. Updates should be published only while no position is open, and not during the pilot unless a fix is critical. |
| Proposals go stale | A 15 to 60 minute setup can pass before an email is read. Expired proposals are tracked so reports show what they would have done. |
| AI cost and run time unknown | Measure one run first, then set the threshold and the daily caps with the owner. |
| TradingAgents is built for equities | The crypto data tools, two roles and a crypto news source are new work. The version is pinned and sits behind STAI's own interface. |
| Dry-run fills are more favourable than real ones | Fills are instant and complete, and Freqtrade's stored entry fee is too low under leverage. See items 21 and 22. Raw events and adjusted accounting are both kept. |
| Stop and target rules were written for a Binance futures scanner | Reviewed for BTC, ETH and SOL on OKX with backtests before the pilot. |
| Futures backtest history is short | OKX provides about three months of mark-price candles, so futures backtests in the Strategy Laboratory cover about that span. The screen will say so. |
| One machine, no standby | Health checks, outage detection and alerts. Considered acceptable for a paper pilot. |

## 6. Deployment limitations

- The development workspace does not run around the clock. Scanning with no browser open needs the published Reserved VM.
- Replit's published rates when checked: about $35 a month for 1 vCPU and 4 GiB, about $50 for 2 vCPU and 8 GiB, charged while the app is published. The production database and the AI provider are billed separately. Current prices should be confirmed in the Publishing pane.
- The region is chosen at the first publish and cannot be changed afterwards, even by unpublishing.
- Files on the machine are lost at every restart or republish.
- Republishing causes a short outage. The running processes get a shutdown signal first, which STAI will use to store the bots' state.
- Changes to the database structure reach the live database through the Publish step, where the owner reviews them. That step does not carry database triggers (item 20).
- Not verifiable until a publish: OKX from the deployed region, sign-in on the live address, email delivery. Resend may need a verified sending domain before it delivers to an address other than the one on the owner's Resend account.

## 7. Estimated implementation effort

About ten build rounds across the seven phases. Each ends with a report and waits for the
owner's go-ahead. For scale, this is roughly three months of work for one experienced
developer working conventionally. The largest uncertainties are restart recovery and
reconciliation in Phase 2 and the crypto adaptation in Phase 3. Elapsed time also includes
several days of continuous running in Phase 6, and then the 30-day pilot, which starts only
when the owner presses Start Pilot.

## Items for the owner's approval

### Proposals from the planning conversation

1. **Timeframes.** 1-hour candles for trend and 15-minute candles for entry timing.
2. **AI cost control.** Rule scoring every 15 minutes at no model cost. The committee runs only above a score threshold, with daily caps on runs and on spend. One real run is measured at the start of Phase 3 and the numbers come back to the owner for approval.
3. **Proposal validity.** 60 minutes by default, configurable. Entry is a limit order at the proposed price, checked again against the live price at approval. A changed price or an expired proposal needs a new approval.
4. **Position sizing.** At the starting equity, 0.5% risk is 5 USDT and the 20% cap is 200 USDT. They meet at a 2.5% stop distance. With a tighter stop the cap sets the size and the planned risk is below 5 USDT.
5. **Email.** One message per proposal linking to the approval page, a daily summary, and risk and outage alerts. Approval happens only in the app after sign-in. The owner sets the hours in which proposals are sent. Setups outside those hours, and proposals that expire or are rejected, are still tracked for the reports.
6. **Email provider.** Resend.
7. **AI provider.** OpenAI is the working assumption, to be confirmed or changed by the owner.
8. **Logo.** The white-text version in the dark app, the supplied version on light backgrounds, and a simplified S for the browser-tab icon. The interface keeps the specification's accent #25C6B0 and the logo keeps its own teal #00D6C8. The logo stays provisional.

### Working assumptions from the planning conversation

9. The owner is the only user and the only approver.
10. The 600 USDT spot and 400 USDT futures allocations are fixed. Nothing moves between them automatically.
11. Spot is long-only. Futures use at most 2x leverage with isolated margin.
12. The daily-loss halt, the drawdown pause and the emergency halt block new entries only. Protective exits keep working.
13. The day for the daily loss limit is the UTC day, so it resets at 08:00 Manila time.
14. STAI's PostgreSQL ledger, in decimal values, is the book of record. Freqtrade is reconciled against it.
15. Freqtrade runs unmodified as a separate process, reachable only from inside the machine.
16. Hosting is a Reserved VM.

### New points from checking this project

17. **Sign-in.** "Log in with Replit", restricted to the owner's Replit account. The platform's other sign-in option needs an extra Node server in front of the Python backend.
18. **Region.** Asia. OKX public data is verified only from Asia, the owner is in Manila, and the choice is permanent.
19. **Machine size.** Start at 1 vCPU and 4 GiB, about $35 a month. Move to 2 vCPU and 8 GiB, about $50, if AI runs or start-up need it.
20. **Database changes.** Alembic migrations in development, as the specification asks. The live database is updated by Replit's Publish step. Because that step carries no triggers, the append-only rule for the ledger and audit trail is enforced in the application and backed by a hash chain: each record carries a fingerprint of the one before it, so any later edit is detectable.
21. **Latency and partial fills.** STAI models latency itself with a configurable delay before submission, a timestamp at every step and the price drift recorded. Partial fills are documented as a limitation, with a guard that refuses an entry that is large against the visible order book.
22. **Fees.** Defaults as measured above, configurable, and always computed by STAI from the fills.
23. **Early test publish.** At the end of Phase 1 the owner publishes the foundation privately on the Reserved VM, so the deployed machine is checked early: OKX access, sign-in, how the database structure is carried over, restart behaviour. Machine billing starts at that point and the region becomes permanent. Unpublishing between phases stops the charge.

## Inputs only the owner can give

Where each one stands after the owner's approval on 17 November 2026:

- The AI provider, and its API key through Replit's secure Secrets form. The key is never asked for in chat, printed or logged. Provider: OpenAI. The key is requested through the secure form as `OPENAI_API_KEY`.
- The email address for alerts. Given by the owner. It is kept as the Replit Secret `STAI_ALERT_EMAIL` and is written in no project file.
- How the handoff files reach the project. Settled: copied from the conversation to `stai_handoff/` at the project root.
- Git. Settled: the project has a repository, so commit history exists from before Phase 1.

## Decision log

| Date | Items | Outcome |
|---|---|---|
| 17 Nov 2026 | 1 to 23 | Proposed. |
| 17 Nov 2026 | 1 to 23 | Approved by the owner as proposed, with no changes. |
| 17 Nov 2026 | 7 | AI provider confirmed: OpenAI. The key is entered through Replit's secure Secrets form as `OPENAI_API_KEY` and is first used in Phase 3. |
| 17 Nov 2026 | Inputs | Alert address received. It is kept as the Replit Secret `STAI_ALERT_EMAIL`, entered by the owner in the secure form, and is first used in Phase 4. It is not kept as a plain environment variable, because Replit writes those into the `.replit` file, which Git tracks. |
| 17 Nov 2026 | Inputs | Owner chose to copy the handoff files from the conversation. Copied to `stai_handoff/` at the project root: 25 files, checksums identical to the source. |
| 17 Nov 2026 | 17 | Note: interface labels read "Log in" and "Log out" without naming the provider, which is a platform rule. The sign-in method is unchanged. |
| 17 Nov 2026 | 18, 23 | Note: the region is chosen by the owner in the Publishing tool's advanced settings before the first publish. Region selection needs a paid Replit plan; on the free plan the app publishes to North America. |
| 17 Nov 2026 | Inputs | Git: the project has a repository, first commit 17 Nov 2026 at 13:02 UTC. The Git paragraph in section 3 and the inputs list were updated to match. |
| 18 Nov 2026 | Phase 1 | Built and checked in the workspace: Python backend, database with migrations, owner sign-in, audit trail, web app with the ten module screens and System Status, ported analytics, documents and the publish checklist. What was built is described in `README.md` and `docs/ARCHITECTURE.md`; what is not verified or not done is in `docs/KNOWN_LIMITATIONS.md`. Not published. No later phase was started. |
| 18 Nov 2026 | 23 | Open. The project side is ready: deployment type Reserved VM, production build and run commands, health check. Pressing Publish and the seven checks on the live app are the owner's step and follow the checklist in `README.md`. |
| 18 Nov 2026 | 16, 18, 19 | Note: region (Asia), private access and machine size (1 vCPU, 4 GiB) are not set by the project. The owner chooses them in the Publishing tool at the first publish. The region is permanent from then on. |
| 18 Nov 2026 | 17 | Note: built as Replit's OpenID Connect sign-in with PKCE in the Python backend. The owner's account ID is read from the workspace's owner ID, with the production secret `STAI_OWNER_USER_ID` as an override. Nobody has signed in through Replit's real service yet, because the tests use a stand-in. Step 1 of the checklist is the first real sign-in. |
| 18 Nov 2026 | 20 | Note: item 20 says any later edit is detectable. As built, changing, removing or reordering earlier audit records is detected. Two cases are not: removing the newest records, and replacing the whole chain with recomputed hashes. Both need direct database access. A copy of the newest hash kept outside the database would close the gap. Whether to add one is for the owner to decide, at the latest when the ledger arrives in Phase 2. |
| 18 Nov 2026 | Analytics | Ported by copying from the handoff, all 191 tests passing. One exception to copying: the data shape `MarketRegimeResponse` (five fields) was rebuilt, because the file that defines it was not in the handoff. The record of every change is in `docs/UPSTREAM_REGISTER.md`. The review of the stop and target rules stays open until before the pilot. |
| 18 Nov 2026 | 8 | Note: built as approved. The app shows resized copies of the supplied white-text logo, and the simplified S is used only for the browser-tab icon and the small app icons. |
| 18 Nov 2026 | Inputs | `OPENAI_API_KEY` and `STAI_ALERT_EMAIL` are in Replit Secrets. Phase 1 uses neither. |
| 18 Nov 2026 | 23 | The owner's production screenshots confirm a production backend, ready schema, reachable OKX and an intact two-event audit chain. Restart check 7 remains unconfirmed; do not enable continuous production bots until it is confirmed. No production changes were made by the agent. |
| 18 Nov 2026 | Phase 2 | Owner said to proceed. Built public OKX data, Decimal fund/ledger, paper-only engine configuration, closed entry strategy, permit validation, restart snapshots, reconciliation, Scanner and Portfolio. The worker is enabled in development only; production defaults to disabled. No AI calls, proposal workflow, email, pilot start or later phase was built. |
| 18 Nov 2026 | 20 | Owner chose **Keep database-only chain** after the external-anchor tradeoff was explained. Do not add an external anchor. Tail deletion and privileged whole-chain rewriting remain accepted limitations; both audit and ledger screens/documentation must state the limit accurately. |
| 18 Nov 2026 | Phase 3 | After reviewing the Phase 2 screenshots, the owner requested the next phase and said no production migration is needed for now. Prepare Phase 3 AI Committee as one task for the owner to start. Development may proceed without production restart check 7; that check is still required before continuous production bots are enabled. No production migration, publish or activation is authorized. |
| 18 Nov 2026 | Phase 3, 2 | Built the ten-role committee with five model calls and two deterministic roles, durable research, read-only APIs and committee screens. One real OpenAI benchmark completed in 37.646 seconds: 32,746 input / 2,104 output tokens, estimated $0.0164648 USD, abstain. Proposed threshold 70, maximum 10 runs and $0.50 per UTC day are for owner review only, not approved or enabled. Provider retries and recurring/manual paid runs remain disabled. Model is listed deprecated; replacement/remeasurement needs separate authorization. See `docs/PHASE3_OPERATIONS.md`. No production change or later phase was made. |
| 18 Nov 2026 | AI screen | Owner selected **70/100** as the initial rule-score threshold for future AI eligibility, adjustable after observation. This approves the threshold value only: no automatic or repeat paid runs, daily run/spend cap, production change, or trade execution is authorized. Strategy rules and any cost caps remain separate decisions. |
