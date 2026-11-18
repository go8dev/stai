# Known limitations

What STAI does not do, does not detect, or has not verified. Each entry says what the
consequence is and, where there is one, what would remove it. Nothing here is hidden
behind a default: where a check cannot run or a value is not available, the interface
says so.

## Phase 2 status and remaining checks

- The owner has published Phase 1 and supplied healthy status/sign-in and intact-audit
  screenshots. The old first-publish checklist below is retained as a historical baseline.
  Production restart check 7 remains unconfirmed.
- Phase 2 changes are workspace-only. No production schema change, publish, VM change
  or continuous production worker activation has been performed.
- Production bots default to disabled. The private worker must be explicitly enabled
  after the owner confirms restart persistence and approves operation.
- The strategy always rejects entries. The standalone exact-permit validator is tested;
  the complete owner approval → engine fill path is Phase 4 work, not a claim made here.
- A five-second snapshot poll is not zero-loss engine recovery under a hard kill.
  Shutdown snapshots, checksums, idempotent replay and reconciliation are implemented.
  Real production kill/restart testing and several days' continuous operation remain
  later acceptance checks.
- Funding amounts and fees are paper accounting, not a promise of an OKX account's
  actual fee tier or fills. The book estimator cannot reproduce market impact, latency,
  partial-fill queues or guaranteed liquidity.
- No Phase 3 AI calls, Phase 4 emails, daily-loss halts, owner proposal approval, pilot
  start or later dashboards are included.

See [Phase 2 operation](PHASE2_OPERATIONS.md) for the current runtime and integrity rules.

## First-publish baseline

These depend on Replit's published environment, which does not exist until the owner
publishes. The publish checklist in the [README](../README.md#publish-checklist) covers
each of them and says what to do if it fails.

| Not verified | What was done instead | If it turns out differently |
| --- | --- | --- |
| A complete sign-in through Replit's real sign-in service. | The tests and the production-form check complete sign-in against a stand-in for the service. The development database holds no user and no audit record, so nobody has signed in for real yet. | Step 1 of the checklist does it in the workspace before publishing. |
| Whether the published machine has the owner's account ID (`REPL_OWNER_ID`). | It is present in the workspace. | The sign-in screen says "Sign-in is not set up" until `STAI_OWNER_USER_ID` is added as a production app secret. |
| Whether the live address is in the host list Replit provides, and arrives in the request headers the backend reads. | Checked with a made-up host name. | **Log in** answers `unknown_host` until the host is added as `STAI_ALLOWED_HOSTS`. |
| Whether the Publish step creates the production database from a development database that has tables but almost no rows. | Replit's documentation was read. It was not tried. | The Database panel shows down or missing tables. Stop and report. |
| Whether Replit's access screen for a private app interferes with the sign-in return or the cookies. | Nothing. It cannot be reproduced in the workspace. | Sign-in fails or loops on the live address. Stop and report. |
| Whether OKX answers the published machine in the Asia region. | It answers from the workspace. | The Market data panel shows down. Report before Phase 2 starts. |
| Replit's own build, proxy and static hosting. | The production form was run in the workspace: the runtime-only Python environment in a separate folder, the built web app behind a stand-in for static hosting, the backend in production mode. 56 of 56 checks passed. | The publish fails or the live checks fail. |
| Behaviour across a Republish. | The backend was stopped and started in production form. The session and the audit trail survived, and a request in progress was answered in full. | Live check 7 fails. |
| Memory needed once the later phases run. | The backend alone used under 100 MB in production form. Before Phase 1, two idle trading bots were measured at about 0.8 GB together. The worker process and an AI run on top of that have not been measured. | Item 19 of the plan moves the machine to 2 vCPU and 8 GiB. |

## Sign-in and sessions

- **Sign-in needs its own tab.** When STAI is shown inside another page, such as the
  workspace preview pane, the browser withholds the sign-in cookies. The sign-in screen
  detects this and offers **Open STAI in a new tab**.
- **Cookies look different in the workspace preview.** Replit's development proxy rewrites
  them to `SameSite=None`. The backend sets `Lax`, and live check 3 confirms that this is
  what the published app sends.
- **Rate limits are kept in memory.** A restart clears them. The per-client count trusts
  the forwarded address header, which a caller can set; the overall limit cannot be
  sidestepped that way. The other side of the overall limit is that a flood of sign-in
  attempts can make the owner's own sign-in answer "too many attempts" for up to a minute
  at a time. A private app is not reachable by outsiders at all, which removes most of
  this.
- **A session cannot be ended from elsewhere.** It lasts a fixed time, 7 days by default.
  **Log out** ends the session of that browser only. There is no screen that lists
  sessions or ends them all. Changing the configured owner ID locks every session out.
- **Log out is a GET request,** as Replit's sign-in flow defines it. The backend ignores
  it when the browser marks the request as coming from another site. A browser that does
  not send that marker gets no such protection. The worst outcome is being signed out.
- **If the sign-in service is down, nobody can sign in.** Sessions that already exist
  keep working, because they are checked against the database only.

## Audit trail

- **Two changes are not detected:** removing the newest records, and replacing the whole
  chain with one whose hashes were recomputed. Both need direct access to the database.
  The owner explicitly chose to keep database-only chains in Phase 2, with no external
  anchor. This limitation applies to the paper ledger as well as the audit trail.
- **The append-only guard is not a security barrier.** It works on the application's own
  connection and recognises statements by their text. It stops mistakes in application
  code. It does not stop someone who connects with the database credentials.
- **The status screen checks the newest 50 records only.** A change further back is found
  by the full verification, which runs when someone starts it: the button, the API route
  or the command. Nothing runs it on a schedule.
- **Records cannot be removed,** by design. That includes the account ID of every account
  that was refused.
- **Three event types are recorded:** sign-in, refused sign-in and sign-out. Refused
  requests of other kinds, such as a failed CSRF check, appear in the logs only.

## System status and alerts

- **Nothing alerts the owner.** A check that goes down is visible only while the System
  Status screen is open. Email alerts arrive in Phase 4.
- **The health check does not touch the database.** Replit sees the app as healthy while
  the database is down. This is deliberate, so that a database outage does not make
  Replit restart a working process. The status screen and every protected route report
  the outage.
- **The OKX check asks for the server time only.** It shows that OKX's public API answers
  this machine. It does not show that candles, tickers or streams work, or how OKX's rate
  limits behave. That is Phase 2. The answer is kept for 10 seconds.
- **Two values can read "not available" on the published app:** the migration revision,
  because it is a row of data that the Publish step does not copy, and the commit, because
  the published machine has no Git checkout. Neither is a fault.

## Backend

- **No limit on request size of its own.** No route reads a request body in Phase 1. A
  limit has to be added with the first route that accepts one.
- **Security headers cover the API only.** The web app's pages are static files served by
  Replit, so STAI sets no headers on them, including no content security policy and no
  rule against showing the page inside another page. The backend refuses to be shown that
  way, and a STAI page shown inside another site does not receive the session cookie.
- **Log masking errs on the side of hiding.** The backend masks every value of an
  environment variable whose name looks secret. Any text in a log line that happens to
  equal one of those values is replaced as well, which in the workspace occasionally hides
  a harmless word.
- **Logs go to standard output only.** They are kept for as long as Replit keeps them.
  STAI does not store or forward them.
- **One process.** The rate limits and the OKX answer are held per process. Phase 2 adds
  a worker process and has to keep that in mind.
- **No backup of its own.** Phase 1 sets up no export or backup of the database beyond
  what Replit provides.

## Analytics

- **Not connected to anything.** No market-data provider is registered and no route calls
  the analytics. Their tests pass data in directly.
- **One small file was rebuilt, not copied.** The ported services import a data shape,
  `MarketRegimeResponse`, from a file that was not in the handoff. It was rebuilt with the
  five fields the services use. See [UPSTREAM_REGISTER.md](UPSTREAM_REGISTER.md).
- **The stop and target rules have not been reviewed.** The handoff notes ask for that
  review before the pilot. It is outside Phase 1.
- **They calculate in floats.** That is fine for indicators. Money and quantities must not
  pass through them.
- **They are exempt from most style checks,** so the files stay comparable with the
  source. Correctness checks still apply.

## Web app

- **Ten module screens are placeholders.** Each names the phase that delivers it.
- **Unused parts of the starter remain.** The web app still contains the starter's full
  set of interface components and their dependencies. STAI's screens use four of them.
- **Tested in Chromium only,** at a desktop width and a phone width.

## Checks

- **The browser test is separate.** `pnpm run test:browser` is not part of
  `pnpm run check`, needs both workflows running, and covers the signed-out visitor only.
  The signed-in screens were checked with a one-off browser run on desktop and phone
  widths. That run and the production-form check are not committed, so neither can be
  repeated with one command.
- **The generated web client is checked by name only.** `pnpm run check` fails when the
  stored API contract differs from the backend. For the generated TypeScript it checks
  that the operations and data shapes of the contract are present, not that the files are
  what the generator would write. After changing the API, run the codegen command.
- **Python has no static type checker.** Ruff checks rules and formatting. Types are
  checked at run time by Pydantic and by the tests.
- **The backend tests need the development database.** Without `DATABASE_URL` they do not
  run.
- **Workflows can start twice.** After Replit restores the workflows, a second copy of the
  backend is sometimes started. It finds the port taken, says so and exits. If the preview
  stays blank, restart the workflow.
- **`pnpm run build` builds more than STAI.** It also builds Replit's canvas scaffold in
  `artifacts/mockup-sandbox`. Publishing does not: it installs the backend's dependencies
  and builds the web app.
- **One deprecation warning is silenced.** The test client of Starlette 1.10 prefers a
  newer HTTP library than the one STAI pins. Every other warning fails the tests.
