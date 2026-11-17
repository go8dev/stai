# Environment setup

STAI reads its settings from environment variables and from nothing else. It does not
read `.env` files, a secrets directory or a config file. On Replit the values come from
three places:

- **Set by Replit.** The platform puts these in the environment of the workspace and of
  the published machine. Leave them alone.
- **Set by the artifact configuration.** Fixed values such as the port, written through
  the platform tooling.
- **Set by the owner.** Optional overrides. Anything personal or secret goes in
  Replit Secrets, never in a plain environment variable, because plain variables are
  written into the tracked `.replit` file.

[`docs/example.env`](example.env) lists every variable with no real values. It is a
reference only. Nothing loads it.

## Backend variables

These are all the variables the Python backend reads. A test fails if the code reads a
variable that is missing from this list, or if this document leaves one out. Names are
case-sensitive and an empty value counts as not set.

### Runtime

| Variable | Set by | Default | Meaning |
| --- | --- | --- | --- |
| `STAI_ENV` | Artifact configuration | production | `development` or `production`. Not set means production. Any other value stops the backend at startup. |
| `REPLIT_DEPLOYMENT` | Replit | not set | Replit sets it to `1` on a published machine. With it, `STAI_ENV=development` is refused and migrations refuse to run. |
| `PORT` | Artifact configuration | none | Port the backend listens on (8080). The backend does not start without it. |
| `STAI_LOG_LEVEL` | Owner, optional | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`. |
| `STAI_BUILD_COMMIT` | Owner, optional | not set | Commit shown on the system status screen. When not set, the backend reads it from the Git checkout, and shows nothing when there is no checkout. |

What `STAI_ENV=development` changes:

- `localhost` and `127.0.0.1` are accepted as hosts, also over plain `http`, so the
  backend can be called from the workspace shell.
- The `Strict-Transport-Security` header is not sent.
- `python -m stai --reload` is allowed.

Nothing else differs. Sign-in, owner-only access, CSRF checks, secure cookies and the
audit trail work the same way in both modes, and the trading mode is `paper` in both.

### Database

| Variable | Set by | Default | Meaning |
| --- | --- | --- | --- |
| `DATABASE_URL` | Replit | none | PostgreSQL address, including its password. Must start with `postgresql://` or `postgres://`. Development and the published app each get their own. |

Without `DATABASE_URL` the backend still starts and the health check answers, but
sign-in is not possible and the system status reports the database as not configured.

### Sign-in

| Variable | Set by | Default | Meaning |
| --- | --- | --- | --- |
| `REPL_ID` | Replit | none | Identifies this app to the sign-in provider. |
| `ISSUER_URL` | Owner, optional | `https://replit.com/oidc` | Address of the sign-in provider. Must be `https://`. |
| `STAI_OWNER_USER_ID` | Owner, optional | value of `REPL_OWNER_ID` | The one account that may sign in. Takes priority over `REPL_OWNER_ID`. |
| `REPL_OWNER_ID` | Replit | none | Account ID of the workspace owner. Used when `STAI_OWNER_USER_ID` is not set. |
| `STAI_SESSION_TTL_HOURS` | Owner, optional | `168` (7 days) | How long a sign-in lasts, from 1 to 2160 hours (90 days). The session ends at that time whether or not it was used. |

Sign-in needs both `REPL_ID` and an owner ID. If either is missing, the sign-in screen
shows a "not configured" notice and nobody can sign in. There is no fallback account.

Whether `REPL_OWNER_ID` is present on the published machine has not been confirmed
yet. The publish checklist in the README covers it: if the first sign-in on the live
address is refused, set `STAI_OWNER_USER_ID` to the owner's account ID.

### Hosts

| Variable | Set by | Default | Meaning |
| --- | --- | --- | --- |
| `REPLIT_DOMAINS` | Replit | empty | Comma-separated addresses this app is served from. |
| `REPLIT_DEV_DOMAIN` | Replit | empty | Address of the development preview. |
| `STAI_ALLOWED_HOSTS` | Owner, optional | empty | Extra comma-separated hosts, for example a custom domain. |

The three lists are combined. Sign-in starts only on one of these hosts and returns
only to it, and a state-changing request is accepted only when it comes from a page on
one of them. Read-only requests are not filtered by host; they need a valid session.

### Market data

| Variable | Set by | Default | Meaning |
| --- | --- | --- | --- |
| `STAI_OKX_BASE_URL` | Owner, optional | `https://www.okx.com` | Base address for OKX public market data. Must be `https://`. Phase 1 only asks it for the server time. |

There is no variable for an exchange API key, secret or passphrase, and there is no
variable that switches trading mode. STAI is paper trading only. Tests fail if such a
setting is added.

## Web app variables

The web app is a static site. It needs two values while it is being built or served in
development, both set by the artifact configuration:

| Variable | Meaning |
| --- | --- |
| `PORT` | Port of the development server. |
| `BASE_PATH` | Path the app is served under (`/`). |

Nothing secret is built into the web app. It calls the backend on the same address
under `/api`.

## Secrets in the workspace

Three Secrets exist in the workspace. The backend does not read any of them in Phase 1.

| Secret | Purpose | Used from |
| --- | --- | --- |
| `OPENAI_API_KEY` | Model provider for the AI committee. | Phase 3 |
| `STAI_ALERT_EMAIL` | Address that receives alerts. | Phase 4 |
| `SESSION_SECRET` | Came with the project template. STAI does not use it: a session is a random token whose SHA-256 is stored in the database. | Not used |

Their values are still masked in every log line. At startup the backend collects the
value of each environment variable whose name contains `SECRET`, `TOKEN`, `PASSWORD`,
`PASSWD`, `API_KEY`, `PRIVATE_KEY` or `ALERT_EMAIL`, plus `PGPASSWORD`, `DATABASE_URL`
and the password inside it, and replaces them with `[redacted]` wherever they would
appear in a log.

Rules for secrets:

- Add and change them in Replit Secrets only. Never paste one into chat, a file, a test
  or a commit.
- Never set a personal value such as an email address as a plain environment variable.
- Published apps do not automatically share workspace Secrets. Check the Secrets of the
  published app before the phases that need them.

## Running locally in the workspace

The workflows start both services with the right environment. To run the backend by
hand from the repository root:

```bash
PYTHONPATH=artifacts/api-server STAI_ENV=development PORT=8080 python -m stai --reload
```

Checks, from the repository root:

```bash
pnpm run check          # lint, type checks, contract check and backend tests
pnpm run test           # backend tests only
pnpm run test:browser   # signed-out browser test (both workflows must be running)
pnpm run db:migrate     # apply migrations to the development database
```

The backend tests need `DATABASE_URL`. They create throwaway databases on the
development server and drop them afterwards, so development data is never touched. Every
other setting in the tests is made up and passed in directly; the tests do not read the
real environment.
