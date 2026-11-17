---
name: Replit publish constraints
description: Platform rules about production databases and Reserved VMs that shaped the STAI architecture.
---

- Production schema changes are applied by the Publish step, which diffs development against
  production for the `public` schema only. It does not carry other schemas, functions, triggers
  or grants. The app must not run DDL or migration scripts against production at start-up.
- A Reserved VM loses its local files on every restart or republish.
- The publishing geography is permanent once chosen, even after unpublishing; moving needs a remix.
- Republishing sends the running process a shutdown signal, then replaces the machine, with a
  short outage.

**Why:** Freqtrade creates and migrates its own tables at start-up and two bots use the same
table names, so pointing the bots at production PostgreSQL conflicts with the first rule. Hence
the design: each bot keeps its SQLite file, and STAI stores a copy in a `public` table together
with the ledger entries it corresponds to, then restores it at boot. For the same reason the
append-only rule for ledger and audit tables is enforced in the application with a hash chain,
not with database triggers.

**How to apply:**
- Alembic migrations run in development only.
- Never add triggers, functions or non-`public` schemas that production depends on.
- The stored bot snapshot must never be older than the ledger; write both in one transaction.
- How Publish treats constraints and indexes is unverified; check it at the first test publish.
