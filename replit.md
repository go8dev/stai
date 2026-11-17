# STAI (SmartTrader AI)

Personal, paper-trading-only crypto research and portfolio platform for one owner: a 1,000 USDT virtual fund (600 spot, 400 futures) on OKX public data, where an AI committee proposes trades and the owner approves every entry.

## Status

- 17 Nov 2026: planning only. Nothing is built. `docs/STAI_PHASE1_PLAN.md` holds the plan and 23 numbered items waiting for the owner's approval. Its decision log records what was approved or changed.
- The code is still the unmodified starter template described under "Run & Operate" and "Stack". The plan replaces the Node API with a Python backend once approved. The only change so far is the Python 3.12 runtime.

## Owner rules (do not weaken)

- Do not build before the owner approves the plan. After approval, implement one phase at a time. After each phase, report: completed, tested, pending, blocked, next recommended action.
- Paper trading only. No live-trading switch. Never request or store exchange trading credentials. Use public market-data endpoints.
- Every new entry needs the owner's explicit approval of the exact trade. No agent can submit an order.
- Bring nothing from Smart Trader except the analytics in the handoff folder. Do not rewrite the analytics from scratch and do not redraw the logo.
- Do not start the 30-day pilot automatically. The owner presses Start Pilot.
- The AI provider key is collected through Replit Secrets only. Never ask for it in chat, print it or log it. The owner uses their own key, not Replit-managed AI billing.
- Alerts go by email. The owner's time zone is Asia/Manila.

## Source documents

- The governing document is the "STAI Master Development Prompt v1.0". The project brief and audit notes from the planning conversation come with it. Where the brief's owner decisions differ from the specification, the decisions win.
- They are meant to arrive as `stai_handoff/` at the project root through a merge the owner approves, together with the logo files, the reusable analytics and the approval-gate probe. If a needed file is missing, ask the owner.

## Run & Operate

Starter template, unchanged until Phase 1:

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

Starter template, unchanged until Phase 1. The proposed stack is in section 3 of the plan.

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)
- Python 3.12 runtime is enabled; no Python code or dependencies yet

## Where things live

- `docs/STAI_PHASE1_PLAN.md` — architecture plan, numbered owner decisions and decision log

## Architecture decisions

Proposed in the plan and not final until the owner approves them. Record the approved ones here.

## Product

Nothing user-facing exists yet.

## Gotchas

- The project has no Git repository yet. The owner switches it on from the Git pane. Do not run `git init`.
- Do test installs outside the project folder so no dependency files appear before a phase is approved.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
