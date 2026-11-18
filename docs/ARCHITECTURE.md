# Architecture

This document describes the foundation through Phase 3. The approved
plan for all seven phases, with the reasons for each choice, is
[STAI_PHASE1_PLAN.md](STAI_PHASE1_PLAN.md). Where this document and the code disagree,
the code is right and this document needs correcting.

## Parts

| Part | What it is | Where |
| --- | --- | --- |
| Web app | A static React site. It holds no secrets and no data of its own. It calls the backend under `/api` on the same address. | `artifacts/stai/` |
| Backend | One Python process: FastAPI served by Uvicorn. The only part that talks to the database and to outside services. | `artifacts/api-server/stai/` |
| Database | PostgreSQL: identity, sessions, audit, virtual fund, ledger, market observations, paper fills/positions, permits and engine recovery snapshots. | [DATABASE.md](DATABASE.md) |
| Replit sign-in | The outside service that proves who is signing in (OpenID Connect). | `https://replit.com/oidc` |
| OKX public API | Public time, candles, ticker, order book, instrument rules and swap funding, without credentials. | `https://www.okx.com` |
| Paper Worker | Separate Python process, two private unmodified Freqtrade dry-run processes; no publicly routed worker or bot API. | [PHASE2_OPERATIONS.md](PHASE2_OPERATIONS.md) |

Replit's proxy sends every path under `/api` to the backend and everything else to the web
app. In development the web app is served by Vite; when published it is a folder of static
files, and any path that is not a file returns `index.html`.

The worker and bots are configured for the workspace. Continuous production operation
defaults to disabled pending the owner's restart check. The strategy refuses all entries
until Phase 4 connects the owner approval workflow.

### Phase 3 research path

Captured OKX observations and reused analytics, attributed public crypto headlines,
and recorded portfolio → bounded LangGraph/TradingAgents research → validated
advisory recommendation and PostgreSQL findings → AI Committee screen.
This path never calls permit creation or execution. There are ten roles in five
paid stages plus two deterministic calculations. One approved workspace benchmark
has run; recurring and manual paid runs remain disabled pending approved limits.
See [PHASE3_OPERATIONS.md](PHASE3_OPERATIONS.md) for precise upstream reuse,
persistence, measurements and interruption semantics.

### Phase 2 data path

Public OKX adapter → timestamp validation → copied analytics and persisted snapshots →
Market Scanner. PostgreSQL fund/ledger and engine states → Portfolio.
The private worker scans every 15 minutes, reconciles about every 5 seconds and saves
checksummed engine snapshots in PostgreSQL. Completed orders are imported only with
consumed owner-permit and timely book evidence, in the same transaction as the snapshot.
The database-only hash-chain choice and its limitations are recorded in the plan.

Additional protected GET routes: `/api/market/scanner`, `/api/portfolio/summary`,
`/api/portfolio/ledger` and `/api/portfolio/ledger/verify`. All use the same owner gate,
generated API client and error envelope. No Phase 2 trading mutation route exists.
See [Phase 2 operation](PHASE2_OPERATIONS.md) for fee, recovery and reconciliation rules.

The detailed foundation walkthrough below describes the Phase 1 baseline; references
to Phase 2 as future work in that historical walkthrough are superseded by this section.

## How the backend handles a request

Every request passes through the same three layers, in this order.

1. **Request context** (`core/middleware.py`). Gives the request a correlation ID, returns
   it in the `X-Correlation-ID` header, adds the security headers, writes one access-log
   line without the query string, and turns any error that nothing else handled into the
   standard 500 answer. In production it also adds `Strict-Transport-Security`.
2. **Gate** (`auth/gate.py`). Closed by default. Five paths are public: `/api/healthz`,
   `/api/login`, `/api/callback`, `/api/logout` and `/api/auth/user`. Every other path,
   including paths that do not exist, needs the owner's session and answers `401
   not_authenticated` without one. Because the gate is middleware and not a rule on each
   route, a route added later is closed without anyone having to remember it. A request
   that changes something must also pass the two CSRF checks described below.
3. **Routes**. Thin functions that call a service module and return a typed answer.

| Path | Method | Purpose | Open to |
| --- | --- | --- | --- |
| `/api/healthz` | GET | Health check. Does not touch the database. | Everyone |
| `/api/login` | GET | Starts sign-in. | Everyone |
| `/api/callback` | GET | Completes sign-in. | Everyone |
| `/api/logout` | GET | Ends the session. | Everyone |
| `/api/auth/user` | GET | Who is signed in, or nobody. | Everyone |
| `/api/auth/csrf` | GET | The CSRF token of the current session. | Owner |
| `/api/system/status` | GET | Live checks for the System Status screen. | Owner |
| `/api/audit/events` | GET | The newest audit records, up to 100. | Owner |
| `/api/audit/verify` | POST | Recomputes the whole audit chain. The only route that is not a GET. | Owner |

Every failure has one shape:

```json
{ "error": "not_authenticated", "message": "Log in to continue.", "correlationId": "…", "details": null }
```

`error` is a stable code for programs, `message` is written for people, and
`correlationId` matches the log lines of that request. Messages are written in the code
and never copied from an exception, so nothing from a stack trace, the database driver or
a secret can reach a response. A database that is missing, unreachable or without its
tables answers `503 database_unavailable`.

## Sign-in

Sign-in follows Replit's OpenID Connect flow with PKCE. The route names and the
browser-side hook (`lib/replit-auth-web`) are the ones Replit's instructions use; the
server side is written in Python (`auth/routes.py`, `auth/oidc.py`).

1. The browser opens `/api/login`. The backend checks that the request arrived on one of
   its configured hosts, creates a state value, a nonce and a PKCE verifier, stores them in
   four short-lived cookies, and redirects to the sign-in service.
2. The sign-in service returns the browser to `/api/callback` with a one-time code.
3. The backend checks the state, exchanges the code together with the PKCE verifier for an
   identity token, and verifies the token's signature, issuer, audience, expiry and nonce.
4. The account ID in the token is compared with the configured owner ID.
   - Not the owner: no session is created, the refusal is written to the audit trail, and
     the browser returns to the sign-in screen, which shows the refused account's ID.
   - The owner: the user record is updated, a session is created, the sign-in is written
     to the audit trail in the same transaction, and the browser returns to the app.

Rules that hold throughout:

- **One owner.** The owner ID comes from configuration (`STAI_OWNER_USER_ID`, else
  `REPL_OWNER_ID`) and is never written in the code. It is compared again on every
  request, so changing the configured owner locks every older session out. With no owner
  ID configured nobody can sign in. There is no fallback account.
- **Known hosts only.** Sign-in starts and ends only on a host from the configured list.
  The host comes from request headers, so it is used only after it matched that list.
- **No tokens kept.** The identity token is read once and discarded, and nothing else the
  sign-in service returns is stored. The request asks only for the account's identity and
  profile (`openid profile`): no email address and no refresh token.
- **Reasons, not loops.** A sign-in that fails returns to the sign-in screen with a reason
  it can explain: refused, cancelled, failed, cookies missing, not configured, too many
  attempts, or database unavailable.
- **Rate limits.** Per minute: 10 sign-in starts and 10 callbacks per client, 30 of each
  overall; 20 sign-outs per client, 60 overall. The counters live in memory.

## Sessions and CSRF

A session is a random token in the `sid` cookie (HttpOnly, Secure, SameSite=Lax). The
database stores only the token's SHA-256, so a copy of the table cannot be used to sign
in. A session ends at a fixed time after it was created, 7 days by default, whether or
not it was used. Logging out deletes it and records the sign-out. Sessions survive a
restart because they are in the database.

A request that changes something needs two things, checked by the gate:

1. It comes from a page of this app: the `Origin` header (or `Referer` when there is no
   `Origin`) names a configured host over `https`.
2. It carries the header `X-CSRF-Token`. The value is derived from the session token with
   HMAC-SHA256 and is handed out by `/api/auth/csrf`. The generated web client fetches
   and attaches it by itself.

`/api/logout` is a GET, as Replit's flow expects. It ignores any request the browser
marks as coming from another site, so a link elsewhere cannot sign the owner out.

## Audit trail

Significant events are appended to `audit_events`. Each record stores the hash of the
record before it and a hash of its own content, so changing, removing or reordering
earlier records breaks the chain at the first affected record. Phase 1 writes three event
types: `auth.signin`, `auth.signin_refused` and `auth.signout`.

The chain can be verified in three ways: the **Verify audit trail** button on the System
Status screen, `POST /api/audit/verify`, and `python -m stai.audit verify` from a shell.
The System Status screen also checks the newest 50 records on every refresh. How the
chain is built, and what it cannot detect, is in [DATABASE.md](DATABASE.md) and
[KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md).

## System status and the OKX check

`/api/system/status` runs its checks when it is called. Nothing is made up.

| Check | What it does | Reported as |
| --- | --- | --- |
| Backend | Environment, uptime, Python version. | ok |
| Database | Runs a query, reads the server version, compares the tables that exist with the tables the code expects, reads the migration revision. | ok, or down when it cannot be reached or a table is missing |
| Audit trail | Counts the records and checks the newest 50. | ok, or down when the check fails |
| Market data | Calls OKX's public server-time endpoint without keys and measures the response time and the clock difference. | ok; degraded when slower than 2 seconds or more than 5 seconds apart; down when refused or unreachable |

The overall status is down when the database or the audit trail is down, degraded when
any other check is not ok, and ok otherwise. The OKX answer is kept for 10 seconds, so
refreshing the screen does not send a request each time.

The OKX check exists for the test publish: exchanges refuse some regions, and this shows
whether the published machine's region can reach OKX before Phase 2 depends on it.

## API contract and the web client

The backend is the source of the API contract. `pnpm run openapi:export` writes it to
`lib/api-spec/openapi.yaml`, and the codegen step turns it into typed React Query hooks
(`lib/api-client-react`) and validators (`lib/api-zod`). The web app calls the backend
only through these hooks, so a change in the backend that the web app does not follow
fails the type check. `pnpm run check` fails when the stored contract differs from what
the backend would produce. The backend does not serve the contract or a documentation
page.

## Web app

`artifacts/stai/src/App.tsx` asks the backend who is signed in. Signed out, it shows the
sign-in screen and nothing else. Signed in, it shows the app shell: navigation for the
ten modules, the PAPER label and the owner's name with **Log out**.

- `src/lib/modules.ts` is the single list of the ten modules, their routes and the phase
  that delivers each. Every module route shows the same "not built yet" screen, filled
  from that list. Update a module's entry there when its phase is delivered.
- `src/pages/system-status.tsx` is the only screen with live content.
- A `401` answer on any call sends the browser back to the sign-in screen with the notice
  that the session has ended.
- Colours, typography and spacing are tokens in `src/index.css`: Inter for text, IBM Plex
  Mono with tabular numerals for values. Times are stored and sent in UTC and shown in
  Asia/Manila.
- The logo files in `public/brand/` are resized copies of the supplied logo. The
  simplified S is used only for the browser-tab icon and the small app icons.

## Analytics

`stai/analytics/` holds the rule-based analytics carried over from Smart Trader:
indicators, BTC regime, market snapshot and setup scoring. They were ported by copying.
What changed is listed in [UPSTREAM_REGISTER.md](UPSTREAM_REGISTER.md).

The analytics read market data through one interface, `MarketDataProvider`
(`stai/marketdata/provider.py`), which can only read candles and a ticker. No provider is
registered in Phase 1, so asking for one fails with a clear error instead of returning
made-up data. The OKX implementation arrives in Phase 2. Nothing in Phase 1 calls the
analytics yet; their tests pass data in directly.

The analytics work in floats, which is fine for indicators. Money and quantities do not
pass through them. Those belong to the decimal ledger of Phase 2.

## Settings, logs and secrets

- **Settings** come from environment variables only (`core/config.py`), are read once at
  start and are checked then. A wrong value stops the backend with a message that names
  the variable and never repeats the value. See [ENVIRONMENT.md](ENVIRONMENT.md).
- **Logs** are one JSON object per line on standard output, each with the request's
  correlation ID. Two layers keep secrets out: a field whose name looks sensitive (token,
  cookie, password, email and similar) is replaced, and every secret value found in the
  environment at start is masked wherever it would appear in a line.
- **Files** on a published machine do not survive a restart, so the backend writes
  nothing to disk. Everything that must persist is in PostgreSQL.

## Starting and stopping

`python -m stai` starts the backend (`stai/__main__.py`).

- It refuses to start without `PORT`, with an unknown `STAI_ENV`, with `--reload` outside
  development, and in development mode on a published machine.
- It takes a lock for its port, so two copies cannot run for the same port.
- It does not create or change tables. With no database, or a database without tables, it
  still starts and answers the health check, and reports the database as unavailable.
- The database connection is opened on first use, with a pool of 5 connections and 5 more
  under load, each checked before use.
- On a stop signal it finishes the requests in progress, for up to 10 seconds, closes its
  connections and logs that it stopped.

Published form, set in the artifact configuration:

| Step | Command |
| --- | --- |
| Build, backend | `uv sync --frozen --no-dev` installs exactly the locked runtime dependencies. |
| Build, web app | `pnpm --filter @workspace/stai run build` writes `artifacts/stai/dist/public`. |
| Run | `python -m stai` with `STAI_ENV=production`, `PORT=8080` and `PYTHONPATH=artifacts/api-server`. |
| Health check | `/api/healthz` |
| Deployment type | Reserved VM, so one machine that is always on. |

## Paper trading only

The rule is enforced by what the code does not contain, and by tests that fail if it is
added (`tests/test_paper_only.py`):

- The trading mode has one value, `paper`, and no environment variable changes it.
- No setting, table column, form field or code path holds an exchange API key, secret or
  passphrase.
- No code places, changes or cancels an order, and the market-data interface has no
  method that could.
- OKX is only ever sent the public server-time request.
- No exchange library and no trading engine is declared, locked or installed in Phase 1.

Some of these tests describe Phase 1 as it is and will fail as soon as Phase 2 adds the
dry-run engine: the ones about installed libraries, outside calls, the single
state-changing route, the single OKX request and code that handles orders. They are to be
revised on purpose at that point, each keeping the rule it protects: dry-run only, no
exchange credentials, no live switch. They are not to be deleted or skipped.

## Where later phases attach

| Phase | Attaches to |
| --- | --- |
| 2. Trading engine | An OKX implementation of `MarketDataProvider`; new tables and Alembic revisions for the ledger; a worker process started from the same package; the two Freqtrade bots behind the approval gate. |
| 3. AI committee | TradingAgents and its model provider, installed within the version constraints already recorded in `pyproject.toml`. |
| 4. Approval and risk | New audit event types through `audit/service.py`; state-changing routes, which the gate already protects with CSRF. |
| 5. Dashboards | The module entries in `src/lib/modules.ts` and their screens. |
