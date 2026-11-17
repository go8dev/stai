# STAI (SmartTrader AI)

Personal, paper-trading-only crypto research and portfolio platform for one owner: a 1,000 USDT virtual fund (600 spot, 400 futures) on OKX public data, where an AI committee proposes trades and the owner approves every entry.

## Status

- 17 Nov 2026: the owner approved the plan in `docs/STAI_PHASE1_PLAN.md`, all 23 numbered items as proposed. Its decision log records every approval and change.
- Phase 1 (foundation) is set up as a task. Nothing is built yet: the code is still the unmodified starter template described under "Run & Operate" and "Stack", plus the Python 3.12 runtime.
- Work proceeds one phase at a time. Phases 2 to 7 are not started and each needs the owner's go-ahead.

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

Starter template, unchanged until Phase 1:

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

Starter template, unchanged until Phase 1. The approved stack is in section 3 of the plan.

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)
- Python 3.12 runtime is enabled; no Python code or dependencies yet

## Where things live

- `docs/STAI_PHASE1_PLAN.md` — approved architecture plan, the 23 numbered owner decisions and the decision log
- `stai_handoff/` — specification, brief, audit notes, logo files, analytics to port, gate probe

## Architecture decisions

Approved by the owner on 17 Nov 2026. Details and reasons are in the plan.

- One Python application (FastAPI API plus a worker process) and two unmodified Freqtrade dry-run bots, one for spot and one for futures, reachable only from inside the machine.
- STAI's PostgreSQL ledger, in decimal values, is the book of record. Freqtrade is the paper execution engine and is reconciled against it. Each bot keeps its local database file, and STAI stores a copy in PostgreSQL with every trade event because a published machine loses its files at restart.
- An entry reaches Freqtrade only with a single-use permit issued after the owner approves the exact trade. The gate is built together with Freqtrade in Phase 2.
- Migrations run in development only. Replit's Publish step applies the production structure and carries no triggers, so append-only is enforced in the application with a hash chain.
- Sign-in is Replit's sign-in restricted to the owner's account. Hosting is a Reserved VM in Asia, starting at 1 vCPU and 4 GiB.

## Product

Nothing user-facing exists yet.

## Gotchas

- The project has a Git repository and checkpoints appear as commits. Do not rewrite history or force-push.
- The alert address is kept as the Replit Secret `STAI_ALERT_EMAIL`. Replit writes plain environment variables into the `.replit` file, which Git tracks, so personal values go in Secrets. Never write the address, or any other personal data or secret, into a file, log or test.
- Do test installs outside the project folder so no dependency files appear before a phase is approved.
- The publish region is permanent after the first publish and only the owner can choose it, in the Publishing tool.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
