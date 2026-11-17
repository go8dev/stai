# STAI (SmartTrader AI)

STAI is a personal crypto research and portfolio platform for one owner. It trades on
paper only: a virtual fund of 1,000 USDT (600 spot, 400 futures) priced from OKX public
market data, where an AI committee proposes trades and the owner approves every entry.

There is no live-trading mode, no switch that adds one, and no setting or field for
exchange API keys. Tests fail if any of those is added.

## Status

Phase 1 of 7 (foundation) is built. It is not published yet: publishing is the owner's
step, described in the [publish checklist](#publish-checklist) below.

What exists:

- A sign-in screen with the supplied logo. Only the owner's Replit account can sign in.
  Any other account is refused and shown its own account ID. Everything except the health
  check and the sign-in routes is closed to signed-out visitors.
- The dark STAI interface with navigation to the ten modules of the specification and a
  PAPER label on every screen. Each module screen says that it is not built yet and names
  the phase that delivers it.
- A System Status screen with live checks from the server: backend, database, OKX public
  data, the audit trail, the build, and the time in UTC and Asia/Manila.
- A PostgreSQL structure created by migrations, and an append-only audit trail of
  sign-ins, refused sign-ins and sign-outs that can be verified at any time.
- The Smart Trader analytics (indicators, BTC regime, market snapshot, setup scoring),
  ported by copying, with their 191 tests passing.

What does not exist yet: the trading engine, the market-data service, the virtual fund
and its ledger (Phase 2), the AI committee (Phase 3), proposals, the risk engine and
emails (Phase 4), and the content of the dashboards (Phase 5). No screen shows sample or
made-up numbers.

## Run and check

In the Replit workspace two workflows start the services: `artifacts/api-server: API
Server` (the Python backend, under `/api`) and `artifacts/stai: web` (the web app, at
`/`). All commands below run from the repository root.

| Command | What it does |
| --- | --- |
| `pnpm run check` | Everything that must pass: lint, type checks, the API contract check and the backend tests. |
| `pnpm run lint` | Ruff (rules and formatting) for Python; ESLint and Prettier for TypeScript. |
| `pnpm run typecheck` | TypeScript type checks for the libraries, the web app and the browser test. |
| `pnpm run test` | Backend tests (pytest). They need `DATABASE_URL` and use throwaway databases. |
| `pnpm run test:browser` | Browser test: a signed-out visitor only ever sees the sign-in screen. Both workflows must be running. |
| `pnpm run format` | Format the code (Prettier and Ruff). |
| `pnpm run build` | Type checks, then the production build of every package that has one, including the web app. |
| `pnpm run db:migrate` | Apply migrations to the development database. |
| `pnpm run openapi:export` | Write the API contract from the backend to `lib/api-spec/openapi.yaml`. |
| `pnpm --filter @workspace/api-spec run codegen` | Regenerate the typed web client and validators from the contract. |
| `PYTHONPATH=artifacts/api-server python -m stai.audit verify` | Verify the audit trail from a shell. Exit status 0 intact, 1 broken, 2 could not run. |

Dependencies are pinned. To install them exactly as locked:

```bash
pnpm install --frozen-lockfile   # TypeScript
uv sync --frozen                 # Python, including the checks-only group
```

`scripts/post-merge.sh` runs those two commands and the migrations after a task is merged.

Two routines that come up often:

- **Changing the API.** Change the backend, run `pnpm run openapi:export`, run the
  codegen command, then `pnpm run check`. The check fails when the stored contract does
  not match the backend.
- **Changing the database.** Change the models, add an Alembic revision, run
  `pnpm run db:migrate`. The rules for revisions are in [docs/DATABASE.md](docs/DATABASE.md).

## Layout

| Path | Content |
| --- | --- |
| `artifacts/api-server/stai/` | The backend package: `core` (settings, logs, errors, middleware), `auth`, `audit`, `db`, `system`, `marketdata`, `analytics`, `tools`. |
| `artifacts/api-server/migrations/` | Alembic migrations. |
| `artifacts/api-server/tests/` | Backend tests, with the ported analytics tests in `tests/analytics/`. |
| `artifacts/stai/` | The web app (React and Vite). |
| `lib/api-spec/` | The API contract, generated from the backend, and the client generator's configuration. |
| `lib/api-client-react/`, `lib/api-zod/` | The generated typed client and validators. Do not edit the `generated` folders by hand. |
| `lib/replit-auth-web/` | The browser side of sign-in. |
| `e2e/` | The browser test. |
| `scripts/post-merge.sh` | Setup that runs after a task is merged. |
| `pyproject.toml`, `uv.lock` | Python dependencies, tool settings and the lock file. |
| `docs/` | The documents listed below. |
| `stai_handoff/` | The owner's source material: specification, brief, audit notes, logo, analytics to port. Read-only. |
| `artifacts/mockup-sandbox/` | Replit's canvas scaffold. Not part of STAI. |

## Documents

- [docs/STAI_PHASE1_PLAN.md](docs/STAI_PHASE1_PLAN.md): the approved plan, the 23 numbered owner decisions and the decision log.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): how the parts fit together and how a request is handled.
- [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md): every environment variable, with [docs/example.env](docs/example.env) as a reference that holds no real values.
- [docs/DATABASE.md](docs/DATABASE.md): tables, migrations, how the published database gets its structure, and the audit trail.
- [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md): what Phase 1 does not do, does not detect, or has not verified.
- [docs/UPSTREAM_REGISTER.md](docs/UPSTREAM_REGISTER.md): versions and licences of everything STAI builds on, and what the analytics port changed.
- [replit.md](replit.md): the project overview and the owner's rules.

## Publish checklist

Publishing is done by the owner in Replit's Publishing tool. The project side is ready:
the deployment type is Reserved VM, the build installs the locked runtime dependencies
and builds the web app, the backend starts in production mode, and Replit's health check
calls `/api/healthz`.

Three choices can only be made by the owner, and the first of them cannot be changed
afterwards. Go through the steps in order.

### Before pressing Publish

1. **Sign in once in the workspace.** Open the preview in its own browser tab (the
   sign-in screen offers **Open STAI in a new tab** when it is shown inside the
   workspace) and press **Log in**. It should lead into STAI. This is the first sign-in
   through Replit's real sign-in service; the tests use a stand-in. If the screen says
   "This account does not have access" and shows an account ID, stop and report the ID
   before publishing.
2. **Check the plan.** Choosing a region needs a paid Replit plan (Core, Pro or
   Enterprise). On the free plan the app is published to North America, where access to
   OKX has not been verified, and the region is permanent. Do not publish from a free plan.
3. **Deployment type.** Open the Publishing tool. The type is already Reserved VM. Where
   it asks for the app type, choose **Web server**, not background worker.
4. **Machine.** 1 vCPU and 4 GiB of memory. At the time of writing Replit lists this at
   about US$35 a month; the Publishing tool shows the current price. The backend alone
   used under 100 MB in the production-form check. The larger size is for the two trading
   bots of Phase 2.
5. **Region.** Expand **Advanced settings** and set **Geography** to **Asia**. This is
   permanent: once the project is published to a region it cannot be moved.
6. **Access.** Under who can access the app, choose a private option: **Invite only**
   (the most restrictive) or **Workspace only**. A personal workspace defaults to Public,
   so this has to be changed by hand. Changing it later means unpublishing first.
7. **Database.** Replit creates a separate production database and shows the SQL it will
   run. Expect it to create four tables (`users`, `auth_sessions`, `audit_events`,
   `alembic_version`) with their primary keys, six further indexes of which two are unique
   (`uq_audit_events_hash`, `uq_audit_events_prev_hash`), one foreign key from
   `auth_sessions` to `users`, and one check (`seq > 0`). Nothing should be dropped or
   altered. Leave **Set up your production database with your current development data**
   switched off, so the published audit trail starts empty.
8. **Secrets.** The published app has its own secrets (**Production app secrets**). Phase 1
   needs none: do not add anything now, and never add exchange keys. Replit provides the
   production `DATABASE_URL` itself.
9. **Press Publish.** If anything on the screen differs from the steps above, stop and ask
   before continuing.

### Checks on the live app

These are done together with the owner after the first publish. Open the live address in
its own browser tab, not inside another page.

| # | Check | Passes when |
| --- | --- | --- |
| 1 | Private access | In a private browser window the live address shows Replit's own sign-in or access screen, not STAI. |
| 2 | Owner sign-in | After Replit's access check, STAI's sign-in screen appears. **Log in** leads into the dark interface with the PAPER label, and the owner's name is shown in the navigation. |
| 3 | Session cookie | In the browser's developer tools the `sid` cookie is HttpOnly, Secure and SameSite Lax. |
| 4 | OKX from Asia | System Status, panel **Market data**: status ok, provider OKX, a latency value and a clock difference. This is the check that the published region can reach OKX. |
| 5 | Database structure | System Status, panel **Database**: status ok, schema ready, no missing tables. **Migration** may read "not available"; that is expected, because the migration marker is a row of data and development data was not copied. |
| 6 | Audit trail | System Status, panel **Audit trail**: at least one event, the newest `auth.signin`. **Verify audit trail** answers "Chain intact". After logging out and in again the count is two higher. |
| 7 | Restart | Press **Republish** without changes (a published app restarts only through a new publish). Afterwards the owner is still signed in, the audit count is unchanged, verification still passes, and **Uptime** in the Backend panel starts again from zero. |

After check 5, and with the owner's go-ahead, the production structure is also compared
table by table with the development structure through Replit's read-only production
access.

### If something is wrong

| What appears | Cause | What to do |
| --- | --- | --- |
| Sign-in screen says "Sign-in is not set up". | The published machine has no owner account ID. | In the workspace Shell run `echo $REPL_OWNER_ID`. Add the number as a production app secret named `STAI_OWNER_USER_ID`, then publish again. Do not paste it into chat or a file. |
| Sign-in screen says "This account does not have access" and shows an account ID. | The account that signed in is not the configured owner. This happens when a workspace is owned by a team. | Stop. Report the ID shown and decide together which account is the owner before changing anything. |
| A page of plain text containing `unknown_host` after pressing Log in. | The live address is not in the list of hosts the backend accepts. | Add the live host name, without `https://`, as a production app secret named `STAI_ALLOWED_HOSTS`, then publish again. |
| "Sign-in could not finish in this window". | The browser withheld the sign-in cookies because STAI was shown inside another page. | Open the live address in its own tab and log in there. |
| "STAI is not ready", or the Database panel shows down or missing tables. | The production database is missing, unreachable or has a different structure. | Stop and report it. Do not create tables by hand. |
| Market data panel shows degraded. | OKX answered slowly (over 2 seconds) or its clock differs from the machine's by more than 5 seconds. | Reload after a minute. If it stays, report it. |
| Market data panel shows down. | OKX refused the request or could not be reached from this region. | Report it before Phase 2 starts. Phase 2 depends on this access. |
| Build shows "commit not available". | The published machine has no Git checkout to read the commit from. | Nothing. Optionally set `STAI_BUILD_COMMIT`. |

What could not be verified before the first publish is listed in
[docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md).
