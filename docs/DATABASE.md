# Database notes

STAI keeps everything that must survive a restart in PostgreSQL. Development and the
published app each have their own database, and Replit sets `DATABASE_URL` for each.
This document covers the structure, the rules every later table follows, how
structure changes reach the published database, and how the audit trail works.

## Tables

Twelve tables in `public`, including the migration marker. Phase 1 added the identity,
session and audit tables described below. Phase 2 adds:

| Table | Purpose |
| --- | --- |
| `virtual_funds` | Singleton fund, initial 1,000 USDT, initialized idempotently under a lock. |
| `fund_allocations` | Composite fund/market key; fixed 600 spot and 400 futures allocations. |
| `ledger_entries` | Decimal signed movements, idempotency keys, canonical hashes and sequence chain. |
| `market_snapshots` | UUID observations with status, exchange time, prices, rules, indicators and book evidence. |
| `paper_positions` | Reconciled position quantity, entry/mark, leverage, fees, funding and P&L. |
| `paper_fills` | Append-only raw and conservative adjusted fill evidence, fees, spread and slippage. |
| `trading_permits` | Exact owner-approved terms and single-use state; no creation API in Phase 2. |
| `bot_states` | Private engine status plus explicitly required compressed SQLite snapshot/checksum for recovery. |

Money and quantities use `Numeric(30,12)`; prices are never binary floats in accounting.
No sequence, server default, trigger or database function is required. The Phase 2
revision is `10af905d740f`, after `0001`. Application guards cover ledger and fill
records as well as audit records. Engine snapshot and fill import writes are atomic.
The owner chose database-only integrity; tail deletion or a privileged full-chain rewrite
is not detectable. See [Phase 2 operation](PHASE2_OPERATIONS.md).

The foundation reference below describes the `0001` baseline. Its references to one
revision or no monetary columns describe Phase 1 only, not the current schema.

### `users`

The accounts that have signed in. Only the owner's account can, so this holds one row.

| Column | Type | Null | Meaning |
| --- | --- | --- | --- |
| `id` | text | no | Primary key. The account ID from the identity token. |
| `username` | text | yes | |
| `first_name` | text | yes | |
| `last_name` | text | yes | |
| `profile_image_url` | text | yes | Stored only when it is an `https` address. |
| `created_at` | timestamp with time zone | no | First sign-in. |
| `updated_at` | timestamp with time zone | no | Last time the profile fields were refreshed. |
| `last_login_at` | timestamp with time zone | yes | |

### `auth_sessions`

One row per signed-in browser.

| Column | Type | Null | Meaning |
| --- | --- | --- | --- |
| `token_hash` | varchar(64) | no | Primary key. SHA-256 of the session cookie's value. The value itself is never stored. |
| `user_id` | text | no | Foreign key to `users.id`, deleted together with the user. |
| `created_at` | timestamp with time zone | no | |
| `expires_at` | timestamp with time zone | no | Fixed when the session is created. Using the session does not extend it. |

Indexes: `ix_auth_sessions_user_id`, `ix_auth_sessions_expires_at`.

A session is deleted at log out, when it is found expired, and in a sweep of all expired
sessions at every sign-in.

### `audit_events`

The append-only audit trail. See [Audit trail](#audit-trail) below.

| Column | Type | Null | Meaning |
| --- | --- | --- | --- |
| `seq` | bigint | no | Primary key. Assigned by the application: one higher than the record before. Not a database sequence. |
| `occurred_at` | timestamp with time zone | no | |
| `event_type` | varchar(100) | no | For example `auth.signin`. |
| `actor_type` | varchar(32) | no | `owner`, or `account` for an account that is not the owner. |
| `actor_id` | text | yes | The account ID of the actor. |
| `correlation_id` | varchar(64) | yes | The correlation ID of the request that caused the event. |
| `payload` | jsonb | no | Details of the event. |
| `prev_hash` | varchar(64) | no | The `hash` of the record before. |
| `hash` | varchar(64) | no | SHA-256 over this record's content and `prev_hash`. |

Check: `ck_audit_events_seq_positive` (`seq > 0`). Unique indexes:
`uq_audit_events_prev_hash` and `uq_audit_events_hash`, so two records can never follow
the same predecessor. Other indexes: `ix_audit_events_event_type`,
`ix_audit_events_occurred_at`.

### `alembic_version`

One column, `version_num`, holding the current migration revision in one row. In
development it reads `0001`.

### Totals

Useful when reading the SQL that the Publishing tool shows: 4 tables, 10 indexes (4
primary keys and the 6 named above, 2 of them unique), 1 foreign key and 1 check.

## Personal data

What the database holds about people, all of it from Replit's sign-in:

- The owner's account ID, username, first name, last name and profile image address, in
  `users`.
- Account IDs in `audit_events.actor_id`. This includes the ID of any account that tried
  to sign in and was refused.

It holds no email address (sign-in does not ask for one), no password, no session token
and no token from the sign-in service.

## Rules for every table

These apply to Phase 1 and to every table added later. Tests in
`artifacts/api-server/tests/test_migrations.py` enforce them.

- **Time.** Every timestamp is `timestamp with time zone` and is stored in UTC. The
  column type used in the models (`UtcDateTime`) refuses a value without a time zone.
  Times are converted to Asia/Manila only for display.
- **Money.** Amounts, prices and quantities use `NUMERIC` (Python `Decimal`), never a
  floating-point type. Phase 1 has no such column yet; a test fails if a `real`,
  `double precision` or `money` column appears.
- **One schema.** Only `public`.
- **Nothing the Publish step does not carry.** No triggers, functions, procedures or
  grants. Replit's Publish step does not copy them to the published database, so anything
  that depended on them would work in development and silently not exist in production.
- **Nothing that is not confirmed to be carried.** The Phase 1 structure also has no
  views, rules, row-security policies, sequences, identity or generated columns, column
  defaults, custom types or extensions, and a test fails if one appears. Defaults and
  identifiers are set by the application. This list is stricter than what the Publish
  step is known to drop. Relax an entry only after confirming that the Publish step
  carries it.
- **Explicit names.** Keys, checks and indexes are named by the convention in
  `stai/db/base.py` (`pk_`, `fk_`, `ck_`, `uq_`, `ix_`), so the same structure always
  produces the same names.
- **The application never changes structure.** It does not create or alter tables at
  start or at any other time. A database without tables is reported as unavailable.

## Migrations

Structure changes are Alembic migrations in `artifacts/api-server/migrations/versions/`.
Phase 1 has one revision, `0001`.

```bash
pnpm run db:migrate    # apply all revisions to the development database
```

Migrations run in development only. On a published machine the command refuses to run.
`scripts/post-merge.sh` runs it after a task is merged.

To change the structure:

1. Change the models in `artifacts/api-server/stai/db/models.py`.
2. Generate a revision, giving it the next number:

   ```bash
   python -m alembic -c artifacts/api-server/alembic.ini revision --autogenerate --rev-id 0002 -m "short description"
   ```

3. Read the generated file and correct it. Autogenerate is a starting point: it does not
   see renames (it writes a drop and an add) and it can miss changes to checks.
4. Run `pnpm run db:migrate`, then `pnpm run check`. The tests apply every revision to an
   empty database, compare the result with the models, and run the downgrade and upgrade
   again.

A revision must not import from the `stai` package, so that it keeps working after the
code changes. To see the SQL without running it, add `--sql`:

```bash
python -m alembic -c artifacts/api-server/alembic.ini upgrade head --sql
```

Migrations use their own database connection, without the append-only guard described
below, because they are the one place where structure is allowed to change.

## How the published database gets its structure

The published app has its own database. Its structure does not come from the migration
files. When the owner publishes, Replit compares the development structure with the
production structure, shows the SQL for the difference, and applies it. Tables, columns,
indexes and constraints are carried. Data is not, unless the owner switches on the option
to copy development data at the first publish, which the checklist says to leave off.

What follows from that:

- The order is always: migrate in development, check, then publish.
- Read the SQL the Publishing tool shows before confirming. For Phase 1 it should only
  create the four tables with their keys, indexes, foreign key and check. If it ever
  proposes to drop or alter something that holds data, stop.
- The comparison works from the two structures, not from the migration files, so it
  cannot know that a column was renamed and not dropped and added. Change structure by
  adding. To rename or remove something that holds data, add the new form in one publish,
  move the data, and remove the old form in a later publish.
- `alembic_version` arrives in production as an empty table, because the revision is a
  row of data. The System Status screen then shows the migration as "not available".
  That is expected. The screen judges the structure by comparing the tables that exist
  with the tables the code expects.
- Nobody changes the production structure by hand. Production is read through Replit's
  read-only access when a check needs it.

## Connections

The backend opens its connection pool on first use: 5 connections, up to 5 more under
load, each tested before it is used and replaced after 5 minutes. Connecting times out
after 5 seconds. Statement parameters are kept out of error messages and logs.

## Audit trail

### What is recorded

Phase 1 writes three event types.

| Event | Actor | Payload |
| --- | --- | --- |
| `auth.signin` | `owner`, with the owner's account ID | `sessionExpiresAt` |
| `auth.signin_refused` | `account`, with the refused account's ID | `reason`: `not_owner` |
| `auth.signout` | `owner`, with the owner's account ID | empty |

A record is written in the same transaction as the change it describes. Either both are
saved or neither is.

### How the chain is built

Each record stores `prev_hash`, the hash of the record before it, and `hash`, the SHA-256
of a JSON document made of its own fields:

```json
{"actorId":"…","actorType":"owner","correlationId":"…","eventType":"auth.signin","occurredAt":"2026-11-18T03:04:05.678901Z","payload":{},"prevHash":"…","seq":1}
```

The document is written with sorted keys, no spaces and UTF-8, and the time in UTC with
microseconds, so the same record always produces the same bytes. The first record follows
a `prev_hash` of 64 zeros.

Writers take turns through a PostgreSQL advisory lock that is held until the transaction
ends, so two records cannot take the same `seq`. The unique index on `prev_hash` is a
second barrier against the same thing.

A payload may hold text, whole numbers, true, false, null, lists and objects with text
keys. Floating-point numbers are refused, because their text form is not stable: amounts
go in as text.

### Append-only

Through the application's database connection, `audit_events` accepts inserts and reads
and nothing else. Three guards in `stai/audit/guards.py` refuse the rest:

- changing or deleting a loaded record,
- bulk update and delete statements against the table,
- SQL text that names the table together with `UPDATE`, `DELETE`, `TRUNCATE`, `DROP`,
  `ALTER`, `MERGE` or `RENAME`.

The guards stop mistakes in application code. They are not a barrier against someone who
holds the database credentials and connects directly. The hash chain is what makes such a
change detectable.

### Verifying

| Way | What it checks |
| --- | --- |
| **Verify audit trail** on the System Status screen, or `POST /api/audit/verify` | The whole chain, from the first record. |
| `PYTHONPATH=artifacts/api-server python -m stai.audit verify` | The whole chain, from a shell. Prints the result as JSON. Exit status 0 intact, 1 broken, 2 could not run. |
| The **Audit trail** panel on the System Status screen | The newest 50 records, on every refresh. |

Verification stops at the first record that does not fit and reports its number and one
of three reasons:

| Reason | Meaning |
| --- | --- |
| `sequence_gap` | A record number is missing or out of order: a record was removed or inserted. |
| `prev_hash_mismatch` | The record does not point at the hash of the record before it. |
| `hash_mismatch` | The record's content does not match its stored hash: it was changed after it was written. |

### What the chain does not detect

- Removing the newest records. What is left is a shorter chain that still verifies.
- Replacing the whole chain with a new one whose hashes were recomputed.

Both need direct access to the database. They are listed in
[KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md).

## Tests

The backend tests create throwaway databases on the development server for each run,
apply the migrations to them and drop them afterwards. The development data is never
touched, and the published database is never contacted.
