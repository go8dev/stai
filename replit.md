# STAI (SmartTrader AI)

Personal, paper-trading-only crypto research and portfolio platform for one owner: a 1,000 USDT virtual fund (600 spot, 400 futures) on OKX public data, where an AI committee proposes trades and the owner approves every entry.

## Status

- 17 Nov 2026: the owner approved the plan in `docs/STAI_PHASE1_PLAN.md`, all 23 numbered items as proposed. Its decision log records every approval and change.
- 18 Nov 2026: the owner published Phase 1 and supplied healthy production and intact-audit screenshots. Production restart check 7 remains unconfirmed.
- Phases 2 and 3 are implemented in the workspace. Production continuous bots remain disabled by default pending check 7 and the owner's approval. Phases 4 to 7 are not started.
- The owner explicitly deferred production migrations while requesting Phase 3. Do not block development on production restart check 7, and do not treat proceeding as permission to change production.
- Phase 3's one approved real benchmark completed: ten roles, five calls, 37.646 seconds, estimated $0.0164648 USD. Owner selected 70/100 as the initial future AI-eligibility threshold. Daily run/spend caps remain unapproved; repeated/scheduled paid runs stay locked. Do not reset the used benchmark slot. Details and controls are in `docs/PHASE3_OPERATIONS.md`.
- Owner approved the initial research-strategy design: trend-aligned pullback, 1h trend/BTC context, 15m completed-candle confirmation; spot long-only and futures long/short. This is a design decision, not implementation or authorization for AI runs/trading. Validate EMA-derived exits for OKX and the intraday holding period before any pilot.
- Owner subsequently approved developing the simpler EMA25/EMA99 pullback entries. Scanner and new Strategy Lab runs share the versioned closed-candle evaluator; legacy saved results remain unchanged. Revised entries stay research-only: no score weights or AI eligibility were approved. Exit/risk settings remain unchanged and unvalidated. See `docs/STRATEGY_LAB.md` and the plan's decision log.

## Owner rules (do not weaken)

- Implement one phase at a time. After each phase, report: completed, tested, pending, blocked, next recommended action. Then wait for the owner.
- Paper trading only. No live-trading switch. Never request or store exchange trading credentials. Use public market-data endpoints.
- Every new entry needs the owner's explicit approval of the exact trade. No agent can submit an order.
- Bring nothing from Smart Trader except the analytics in `stai_handoff/`. Do not rewrite the analytics from scratch and do not redraw the logo.
- Do not start the 30-day pilot automatically. The owner presses Start Pilot.
- The AI provider is OpenAI with the owner's own key (`OPENAI_API_KEY` in Replit Secrets), not Replit-managed AI billing. Never ask for the key in chat, print it or log it.
- Alerts go by email. The owner's time zone is Asia/Manila.

## Source documents

- `stai_handoff/` holds the owner's specification ("STAI Master Development Prompt v1.0"), the project brief, the audit notes, the two logo files, the reusable Smart Trader analytics with their tests, and the approval-gate probe. It is read-only source material: port by copying.
- The specification governs. Where the brief's owner decisions (section A2) differ from it, the decisions win.

## Run & Operate

Three STAI workflows run in the workspace: `artifacts/api-server: API Server`, `artifacts/stai: web`, and `artifacts/api-server: Paper Worker` (private health port 8099, no routed path). Commands run from the repository root.

- `pnpm run check` — everything that must pass: lint, type checks, the API contract check and the backend tests
- `pnpm run lint`, `pnpm run typecheck`, `pnpm run test` — the parts of `check`, one command each
- `pnpm run test:browser` — browser test for signed-out visitors; both workflows must be running; not part of `check`
- `pnpm run format` — Prettier and Ruff formatting
- `pnpm run db:migrate` — apply Alembic migrations to the development database
- `pnpm run openapi:export`, then `pnpm --filter @workspace/api-spec run codegen` — after any change to the API
- `pnpm install --frozen-lockfile` and `uv sync --frozen` — install exactly the locked dependencies
- `PYTHONPATH=artifacts/api-server python -m stai.audit verify` — verify the audit trail from a shell
- Required env: `DATABASE_URL`. Every other variable has a default or comes from Replit; see `docs/ENVIRONMENT.md`

## Stack

- Backend: Python 3.12, FastAPI on Uvicorn, Pydantic 2, SQLAlchemy 2.1 with psycopg 3, Alembic. Sign-in uses httpx and PyJWT. Dependencies are pinned in `pyproject.toml` and `uv.lock`.
- Web app: React 19, TypeScript 5.9, Vite 7, Tailwind CSS 4, React Query, wouter. pnpm workspaces on Node.js 24.
- API contract: OpenAPI exported from the backend; Orval generates the typed React Query hooks and Zod validators.
- Database: Replit PostgreSQL.
- Checks: Ruff, pytest, ESLint, Prettier, `tsc`, Playwright.
- Freqtrade 2026.10, CCXT 4.5.93 and TradingAgents 0.7.1 are installed and locked. TradingAgents stays unmodified behind read-only crypto adapters; its equity tools and file memory are not invoked.

## Where things live

- `docs/STAI_PHASE1_PLAN.md` — approved architecture plan, the 23 numbered owner decisions and the decision log
- `README.md` — status, commands, layout and the owner's publish checklist
- `docs/ARCHITECTURE.md`, `docs/ENVIRONMENT.md`, `docs/DATABASE.md`, `docs/KNOWN_LIMITATIONS.md`, `docs/UPSTREAM_REGISTER.md` — how it works, settings, tables and migrations, what is not done or not verified, versions and licences
- `artifacts/api-server/stai/` — backend package: `core`, `auth`, `audit`, `db`, `system`, `marketdata`, `analytics`, `tools`
- `artifacts/api-server/migrations/` — Alembic migrations; `artifacts/api-server/tests/` — backend tests
- `artifacts/stai/` — web app; `src/lib/modules.ts` is the single list of the ten modules and the phase that delivers each
- `lib/api-spec/openapi.yaml` — the API contract; `lib/api-client-react/`, `lib/api-zod/` — generated client and validators
- `lib/replit-auth-web/` — browser side of sign-in
- `e2e/` — browser test; `scripts/post-merge.sh` — setup after a task is merged
- `stai_handoff/` — specification, brief, audit notes, logo files, analytics source, gate probe

## Architecture decisions

Approved by the owner on 17 Nov 2026. Details and reasons are in the plan.

- One Python application (FastAPI API plus a worker process) and two unmodified Freqtrade dry-run bots, one for spot and one for futures, reachable only from inside the machine. Phase 1 built the API only.
- STAI's PostgreSQL ledger, in decimal values, is the book of record. Freqtrade is the paper execution engine and is reconciled against it. Each bot keeps its local database file, and STAI stores a copy in PostgreSQL with every trade event because a published machine loses its files at restart.
- An entry requires a single-use permit for the exact owner-approved terms. Phase 2 builds and tests the validator but deliberately keeps the strategy's entry callback closed and all entry signals zero; Phase 4 connects approval to execution.
- The owner chose database-only ledger integrity. Do not add an external hash anchor. Tail deletion and privileged full-chain rewriting cannot be detected by that chain alone.
- The production worker requires the explicit `--enable-paper-bots` command flag. Do not add it until the owner confirms production restart check 7 and authorizes continuous operation.
- Migrations run in development only. Replit's Publish step applies the production structure and carries no triggers, so append-only is enforced in the application with a hash chain. The backend never creates or alters tables.
- Sign-in is Replit's sign-in restricted to the owner's account. Hosting is a Reserved VM in Asia, starting at 1 vCPU and 4 GiB.
- The API is closed by default: middleware requires the owner's session on every path except the health check and the sign-in routes, so a new route is protected without further work. Requests that change something also need the CSRF header, which the generated client attaches.
- The analytics read market data only through the `MarketDataProvider` interface. Its OKX implementation is Phase 2.

## Product

- A sign-in screen with the supplied logo. Only the owner's Replit account gets in; any other account is refused and shown its own account ID.
- The dark STAI interface with navigation to the ten modules and a PAPER label on every screen. Each module screen says it is not built yet and names the phase that delivers it. No sample numbers anywhere.
- A System Status screen with live checks: backend, database, OKX public data, audit trail, build, and the time in UTC and Asia/Manila.
- An append-only audit trail of sign-ins, refused sign-ins and sign-outs that the owner can verify from the System Status screen.

## Gotchas

- The project has a Git repository and checkpoints appear as commits. Do not rewrite history or force-push.
- The alert address is kept as the Replit Secret `STAI_ALERT_EMAIL`. Replit writes plain environment variables into the `.replit` file, which Git tracks, so personal values go in Secrets. Never write the address, or any other personal data or secret, into a file, log or test. A test scans the project files for real secret values and fails when it finds one.
- `tests/test_paper_only.py` fails if a live-trading switch, an exchange-key setting, order code or an exchange library appears. Never skip or delete these tests. The ones that describe Phase 1 as it is (no engine installed, one OKX request, one state-changing route) are revised on purpose when Phase 2 adds the dry-run engine, each keeping the rule it protects.
- The publish region is permanent after the first publish and only the owner can choose it, in the Publishing tool. Do not publish or trigger a publish for the owner.
- Sign-in needs its own browser tab. Inside the workspace preview the browser withholds the sign-in cookies, and the sign-in screen offers a button that opens STAI in a new tab.
- Never run `uv sync --no-dev` in the workspace. It removes the check tools from the workspace's Python environment. Only the publish build uses it.
- Do not edit the `generated` folders by hand, and do not reformat the ported analytics: they are exempt from style checks so each file stays comparable with its source in `stai_handoff/`.
- Do test installs outside the project folder so no dependency files appear before a phase is approved.
- Change artifact services, commands and publish settings only through the platform's artifact and deployment tooling.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
- `artifacts/mockup-sandbox/` is Replit's canvas scaffold and not part of STAI
